$ErrorActionPreference = "Stop"

if (Test-Path ".env") {
  Get-Content ".env" | ForEach-Object {
    $line = $_.Trim()
    if (-not $line -or $line.StartsWith("#") -or -not $line.Contains("=")) {
      return
    }
    $name, $value = $line.Split("=", 2)
    if (-not [Environment]::GetEnvironmentVariable($name, "Process")) {
      [Environment]::SetEnvironmentVariable($name, $value, "Process")
    }
  }
}

if (-not $env:DISCORD_TOKEN) {
  Write-Host "DISCORD_TOKEN nao configurado." -ForegroundColor Red
  exit 1
}

if (-not $env:OPENROUTER_API_KEY) {
  Write-Host "OPENROUTER_API_KEY nao configurado. O bot liga, mas a IA ficara indisponivel." -ForegroundColor Yellow
}

if (-not $env:SITE_PORT) {
  $env:SITE_PORT = "8081"
}

if (-not $env:SITE_HOST) {
  $env:SITE_HOST = "127.0.0.1"
}

$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

$logDir = Join-Path $PSScriptRoot "logs"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$logFile = Join-Path $logDir "tenshi-bot-$PID.log"
Write-Host "Log desta execucao: $logFile" -ForegroundColor DarkGray

while ($true) {
  Write-Host "Iniciando Tenshi Bot..." -ForegroundColor Cyan
  "[$(Get-Date -Format s)] Iniciando Tenshi Bot..." | Tee-Object -FilePath $logFile -Append

  $oldPreference = $ErrorActionPreference
  $ErrorActionPreference = "Continue"
  & python .\main.py 2>&1 | ForEach-Object { $_.ToString() } | Tee-Object -FilePath $logFile -Append
  $code = $LASTEXITCODE
  $ErrorActionPreference = $oldPreference

  Write-Host "Bot encerrou com codigo $code. Reiniciando em 10 segundos..." -ForegroundColor Yellow
  "[$(Get-Date -Format s)] Bot encerrou com codigo $code. Reiniciando em 10 segundos..." | Tee-Object -FilePath $logFile -Append
  Start-Sleep -Seconds 10
}
