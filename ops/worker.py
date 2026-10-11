"""Local probes, daily verified PostgreSQL backups, seven-day retention.

No Docker socket, external telemetry or outbound notifications required.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time
import urllib.request
import uuid

STATE = Path(os.getenv("OPS_STATE", "/state"))
BACKUPS = STATE / "backups"


def log(event, **fields):
    print(json.dumps({"at": time.time(), "event": event, **fields}, ensure_ascii=False), flush=True)


def atomic_json(path, data):
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)


def sha256(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def sql(statement, database=None):
    return subprocess.check_output(["psql", "-X", "-d", database or os.environ["PGDATABASE"], "-At", "-v", "ON_ERROR_STOP=1", "-c", statement], text=True, stderr=subprocess.DEVNULL, timeout=120).strip()


def restore_check(path):
    database = "restore_check_" + uuid.uuid4().hex
    created = False
    try:
        sql(f"CREATE DATABASE {database}")
        created = True
        subprocess.run(["pg_restore", "--exit-on-error", "--no-owner", "-d", database, str(path)], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=600)
        counts = {table: int(sql(f"SELECT count(*) FROM {table}", database)) for table in ("users", "candidates", "companies", "vacancies")}
        return counts
    finally:
        if created:
            sql(f"DROP DATABASE {database}")


def backup():
    BACKUPS.mkdir(parents=True, exist_ok=True)
    name = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    temporary = BACKUPS / f"{name}.partial"
    target = BACKUPS / f"{name}.dump"
    if target.exists():
        raise RuntimeError("Backup filename already exists")
    try:
        subprocess.run(["pg_dump", "-Fc", "-f", str(temporary)], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=600)
        subprocess.run(["pg_restore", "--list", str(temporary)], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=120)
        counts = restore_check(temporary)
        digest = sha256(temporary)
        temporary.replace(target)
        metadata = {"created_at": time.time(), "sha256": digest, "bytes": target.stat().st_size, "restored_counts": counts, "restore_verified": True}
        atomic_json(target.with_suffix(".json"), metadata)
        # Only after a new backup is actually restored, expire our own verified backups.
        for old in BACKUPS.glob("????????T??????Z.dump"):
            manifest = old.with_suffix(".json")
            if old == target or not manifest.exists():
                continue
            record = json.loads(manifest.read_text(encoding="utf-8"))
            if record.get("restore_verified") and record["created_at"] < time.time() - 7 * 86400:
                old.unlink(); manifest.unlink()
        log("backup_verified", filename=target.name, **metadata)
        return metadata
    finally:
        if temporary.exists():
            temporary.unlink()


def probe(url):
    started = time.monotonic()
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            ok = response.status == 200
        return {"ok": ok, "latency_ms": round((time.monotonic() - started) * 1000, 1)}
    except Exception:
        return {"ok": False, "latency_ms": round((time.monotonic() - started) * 1000, 1)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--verify-latest", action="store_true")
    args = parser.parse_args()
    STATE.mkdir(parents=True, exist_ok=True)
    if args.verify_latest:
        latest = sorted(BACKUPS.glob("????????T??????Z.dump"))[-1]
        record = json.loads(latest.with_suffix(".json").read_text(encoding="utf-8"))
        if sha256(latest) != record["sha256"]:
            raise RuntimeError("Backup checksum mismatch; restore refused")
        log("restore_verified", filename=latest.name, counts=restore_check(latest))
        return
    targets = json.loads(os.environ["OPS_TARGETS"])
    last_backup = 0
    state_path = STATE / "status.json"
    if state_path.exists():
        last_backup = json.loads(state_path.read_text(encoding="utf-8")).get("last_backup", 0)
    previous = {}
    next_backup_attempt = 0
    while True:
        statuses = {name: probe(url) for name, url in targets.items()}
        for name, result in statuses.items():
            if previous.get(name) != result["ok"]:
                log("service_recovered" if result["ok"] else "service_unavailable", service=name, **result)
            previous[name] = result["ok"]
        now = time.time()
        if now - last_backup >= 86400 and now >= next_backup_attempt:
            try:
                backup()
                last_backup = time.time()
            except Exception as exc:
                # Never log subprocess commands/environment: PG credentials stay private.
                log("backup_failed", error_type=type(exc).__name__)
                next_backup_attempt = now + 3600
        atomic_json(state_path, {"checked_at": time.time(), "services": statuses, "last_backup": last_backup, "backup_ok": time.time() - last_backup < 26 * 3600})
        if args.once:
            break
        time.sleep(30)


if __name__ == "__main__":
    main()
