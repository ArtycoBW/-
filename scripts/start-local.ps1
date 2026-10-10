$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot
if (-not (Test-Path -LiteralPath '.venv/Scripts/python.exe')) {
    uv python install 3.12
    uv venv --python 3.12 .venv
}
uv pip install -r backend/requirements.txt
if (-not (Test-Path -LiteralPath 'frontend/node_modules/next')) {
    Push-Location frontend
    npm ci
    Pop-Location
}
$env:DEMO_MODE = 'true'
$env:PUBLIC_ORIGIN = 'http://localhost:3000'
$env:PYTHONIOENCODING = 'utf-8'
& '.venv/Scripts/python.exe' -m backend.seed
$pythonPath = Join-Path $projectRoot '.venv/Scripts/python.exe'
$frontendPath = Join-Path $projectRoot 'frontend'
$nodePath = (Get-Command node).Source
foreach ($port in @(8000,3000)) {
    if (Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue) {
        throw "Порт $port занят. Завершите предыдущий запуск или используйте его."
    }
}
$api = Start-Process -FilePath $pythonPath -ArgumentList '-m','uvicorn','backend.main:app','--host','127.0.0.1','--port','8000' -WorkingDirectory $projectRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput "$projectRoot/.local/api.log" -RedirectStandardError "$projectRoot/.local/api.error.log"
$web = Start-Process -FilePath $nodePath -ArgumentList 'node_modules/next/dist/bin/next','dev','--hostname','127.0.0.1' -WorkingDirectory $frontendPath -WindowStyle Hidden -PassThru -RedirectStandardOutput "$projectRoot/.local/web.log" -RedirectStandardError "$projectRoot/.local/web.error.log"
@{api=$api.Id;web=$web.Id} | ConvertTo-Json | Set-Content '.local/processes.json'
Write-Output 'Разряд: http://localhost:3000. API: http://localhost:8000/api/v1/docs. Журналы: .local/.'
