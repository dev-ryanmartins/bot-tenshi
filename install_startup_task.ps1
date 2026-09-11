$ErrorActionPreference = "Stop"

$taskName = "Tenshi Bot 24h"
$projectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$scriptPath = Join-Path $projectDir "start_bot_24h.ps1"

if (-not (Test-Path $scriptPath)) {
  Write-Host "Nao encontrei start_bot_24h.ps1 em $projectDir" -ForegroundColor Red
  exit 1
}

$action = New-ScheduledTaskAction `
  -Execute "powershell.exe" `
  -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$scriptPath`"" `
  -WorkingDirectory $projectDir

$trigger = New-ScheduledTaskTrigger -AtLogOn
$settings = New-ScheduledTaskSettingsSet `
  -AllowStartIfOnBatteries `
  -DontStopIfGoingOnBatteries `
  -RestartCount 999 `
  -RestartInterval (New-TimeSpan -Minutes 1)

Register-ScheduledTask `
  -TaskName $taskName `
  -Action $action `
  -Trigger $trigger `
  -Settings $settings `
  -Description "Mantem o Tenshi Bot e o site Python ativos apos login do Windows." `
  -Force

Write-Host "Tarefa '$taskName' instalada. O bot iniciara automaticamente quando voce fizer login no Windows." -ForegroundColor Green
