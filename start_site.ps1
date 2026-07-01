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

if (-not $env:SITE_PORT) {
  $env:SITE_PORT = "8081"
}

if (-not $env:SITE_HOST) {
  $env:SITE_HOST = "127.0.0.1"
}

python .\artifacts\tenshi-bot\site_server.py
