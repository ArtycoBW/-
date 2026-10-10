"""Create a consistent PostgreSQL dump in a private local directory."""
from datetime import datetime, timezone
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
directory = ROOT / '.local/backups'
directory.mkdir(parents=True, exist_ok=True)
target = directory / (datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '.dump')
with target.open('xb') as output:
    subprocess.run(['docker', 'compose', 'exec', '-T', 'db', 'pg_dump', '-U', 'razryad', '-d', 'razryad', '-Fc'], cwd=ROOT, stdout=output, check=True)
subprocess.run(['docker', 'compose', 'exec', '-T', 'db', 'pg_restore', '--list'], cwd=ROOT, input=target.read_bytes(), stdout=subprocess.DEVNULL, check=True)
print('Backup verified:', target.name, target.stat().st_size, 'bytes')
