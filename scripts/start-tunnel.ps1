$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
Set-Location -LiteralPath $projectRoot
$localDirectory = Join-Path $projectRoot '.local'
New-Item -ItemType Directory -Force -Path $localDirectory | Out-Null
$environmentFile = if (Test-Path -LiteralPath '.env') { '.env' } else { '.env.example' }
$argsBase = @('compose', '--env-file', $environmentFile, '-f', 'compose.yml', '-f', 'compose.tunnel.yml')
& docker @argsBase up -d tunnel
if ($LASTEXITCODE -ne 0) { throw 'Не удалось запустить туннель' }
$publicUrl = $null
for ($attempt = 0; $attempt -lt 30; $attempt++) {
    $logs = (& docker @argsBase logs --no-color --tail 100 tunnel 2>&1) -join "`n"
    $matchesFound = [regex]::Matches($logs, 'https://[a-z0-9-]+\.trycloudflare\.com')
    if ($matchesFound.Count -gt 0) { $publicUrl = $matchesFound[-1].Value; break }
    Start-Sleep -Seconds 2
}
if (!$publicUrl) { throw 'Cloudflare ещё не выдал URL. Проверьте docker compose -f compose.yml -f compose.tunnel.yml logs tunnel' }
$publicEnvironment = Join-Path $localDirectory 'tunnel.env'
"PUBLIC_ORIGIN=$publicUrl`nCOOKIE_SECURE=true`nEMAIL_VERIFICATION_REQUIRED=false`nPASSWORD_RECOVERY_ENABLED=false`nEXPOSE_DEMO_MAIL=false`nTRUST_CLOUDFLARE=true" | Set-Content -LiteralPath $publicEnvironment -Encoding utf8
& docker compose --env-file $environmentFile --env-file $publicEnvironment -f compose.yml -f compose.tunnel.yml up -d api web
if ($LASTEXITCODE -ne 0) { throw 'Не удалось применить HTTPS-настройки' }
$publicUrl | Set-Content -LiteralPath (Join-Path $localDirectory 'public-url.txt') -Encoding utf8
Write-Output "Демонстрационный стенд: $publicUrl"
Write-Output 'URL временный. После перезапуска туннеля повторите этот скрипт. База данных сохраняется.'
