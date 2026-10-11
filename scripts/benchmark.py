"""Небольшая воспроизводимая проверка задержки подбора на демостенде."""
import argparse
import asyncio
import json
import math
import platform
import os
import time
import sys
from datetime import datetime, timezone
from pathlib import Path
import httpx


def memory_gib():
    if platform.system() == "Windows":
        import ctypes
        class MemoryStatus(ctypes.Structure):
            _fields_ = [("length", ctypes.c_ulong), ("load", ctypes.c_ulong)] + [(name, ctypes.c_ulonglong) for name in ("total", "available", "pagefile", "available_pagefile", "virtual", "available_virtual", "extended")]
        status = MemoryStatus()
        status.length = ctypes.sizeof(status)
        ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status))
        return round(status.total / 2**30, 2)
    if hasattr(os, "sysconf"):
        return round(os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES") / 2**30, 2)
    return None


async def run(base, count, concurrency):
    async with httpx.AsyncClient(base_url=base, timeout=30) as client:
        health = await client.get("/api/v1/health")
        if not health.json().get("demo"):
            raise RuntimeError("Проверка разрешена только для демонстрационного стенда")
        auth = await client.post("/api/v1/auth/demo/employer")
        auth.raise_for_status()
        warm = await client.get("/api/v1/candidates?limit=12")
        warm.raise_for_status()
        total = warm.json()["total"]
        semaphore = asyncio.Semaphore(concurrency)

        async def request():
            async with semaphore:
                start = time.perf_counter()
                response = await client.get("/api/v1/candidates?limit=12")
                return (time.perf_counter() - start) * 1000, response.status_code

        start = time.perf_counter()
        results = await asyncio.gather(*(request() for _ in range(count)))
        elapsed = time.perf_counter() - start
        latencies = sorted(r[0] for r in results)
        percentile = lambda p: round(latencies[max(0, math.ceil(p*count)-1)], 2)
        report = {"measured_at_utc": datetime.now(timezone.utc).isoformat(),
                  "environment": ("Cloudflare HTTPS → " if base.startswith("https://") else "Локальная сеть → ") + "Docker Desktop: Next.js production → FastAPI → PostgreSQL 17",
                  "client_os": platform.system(), "cpu": platform.processor(), "host_ram_gib": memory_gib(),
                  "endpoint": "GET /api/v1/candidates?limit=12", "profiles": total,
                  "requests": count, "concurrency": concurrency, "warmup_requests": 1,
                  "successes": sum(r[1] == 200 for r in results), "statuses": sorted(set(r[1] for r in results)),
                  "p50_ms": percentile(.5), "p95_ms": percentile(.95), "max_ms": round(max(latencies), 2),
                  "elapsed_seconds": round(elapsed, 2), "requests_per_second": round(count/elapsed, 2),
                  "limitation": "Синтетический банк; задержка включает сеть указанного окружения. Не подтверждает SLA, безопасность или масштабирование на большой объём."}
        Path("docs/performance.json").write_text(json.dumps(report, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
        print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://localhost:3000")
    parser.add_argument("--requests", type=int, default=100)
    parser.add_argument("--concurrency", type=int, default=10)
    args = parser.parse_args()
    if not 1 <= args.requests <= 1000 or not 1 <= args.concurrency <= 50:
        parser.error("Допустимы 1–1000 запросов и 1–50 одновременных обращений")
    asyncio.run(run(args.base_url, args.requests, args.concurrency))
