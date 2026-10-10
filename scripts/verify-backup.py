"""Restore the newest private backup to a fresh isolated database, then drop only it."""
from pathlib import Path
import subprocess
import uuid

ROOT = Path(__file__).resolve().parents[1]
backups = sorted((ROOT / '.local/backups').glob('*.dump'))
if not backups:
    raise SystemExit('Run scripts/backup.py first')
database = 'restore_check_' + uuid.uuid4().hex[:12]
base = ['docker', 'compose', 'exec', '-T', 'db']

def psql(sql, target='razryad'):
    return subprocess.check_output(base + ['psql', '-U', 'razryad', '-d', target, '-At', '-v', 'ON_ERROR_STOP=1', '-c', sql], cwd=ROOT, text=True).strip()

created = False
try:
    psql(f'CREATE DATABASE {database}')
    created = True
    subprocess.run(base + ['pg_restore', '-U', 'razryad', '-d', database, '--exit-on-error', '--no-owner'], cwd=ROOT, input=backups[-1].read_bytes(), check=True)
    counts = {table: int(psql(f'SELECT count(*) FROM {table}', database)) for table in ['users', 'candidates', 'companies', 'vacancies']}
    if not counts['users']:
        raise RuntimeError('Restored database has no users')
    print('Restore verified:', counts)
finally:
    if created:
        psql(f'DROP DATABASE {database}')
