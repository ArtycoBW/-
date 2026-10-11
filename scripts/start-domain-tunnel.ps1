param([switch]$PrepareOnly)
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath (Split-Path $PSScriptRoot -Parent)
foreach ($requiredFile in @('.local/domain-api.env', '.local/domain.env')) {
    if (!(Test-Path -LiteralPath $requiredFile)) { throw "Отсутствует $requiredFile. Сначала подготовьте окружение домена." }
}
$composeArgs = @('compose', '--env-file', '.local/domain.env', '-f', 'compose.domain.yml')
if ($PrepareOnly) {
    & docker @composeArgs up -d --wait domain-api domain-web
} else {
    $tokenPath = '.local/cloudflare-tunnel-token.txt'
    if (!(Test-Path -LiteralPath $tokenPath)) { throw "Сохраните токен туннеля в $tokenPath" }
    $tunnelToken = (Get-Content -LiteralPath $tokenPath -Raw).Trim()
    if ($tunnelToken -notmatch '^[A-Za-z0-9+/=_-]{80,}$') {
        throw 'В файле должен быть только токен, без команды установки, кавычек и пробелов.'
    }
    [System.IO.File]::WriteAllText((Join-Path (Get-Location) $tokenPath), $tunnelToken, [System.Text.UTF8Encoding]::new($false))
    $tunnelToken = $null
    & docker @composeArgs --profile tunnel up -d --no-deps domain-tunnel
}
if ($LASTEXITCODE -ne 0) { throw 'Не удалось запустить компоненты нового домена.' }
Write-Output 'Текущий проект razryad и временный туннель не изменялись.'
