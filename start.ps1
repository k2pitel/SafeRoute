# Starts SafeRoute for development. Ctrl+C stops it all.
#
#   start.cmd                  everything (default, works on school Wi-Fi):
#                                - backend on :8000
#                                - Cloudflare tunnel for the backend
#                                - Expo on :8081 behind a Cloudflare tunnel  (exps://...trycloudflare.com)
#                                - Expo on :8083 behind Expo's own tunnel     (exp://...on.expo.app, backup)
#   start.cmd -CloudflareOnly  skip the Expo-tunnel backup
#   start.cmd -TunnelOnly      app only via Expo's tunnel (backend still via Cloudflare)
#   start.cmd -Lan             phone and PC on the same Wi-Fi / hotspot, no tunnels
#
# See docs/drafts/GETTING_STARTED.md.
param(
  [switch]$Lan,
  [switch]$CloudflareOnly,
  [switch]$TunnelOnly,
  [int]$Port = 8081,
  [int]$TunnelPort = 8083
)

$ErrorActionPreference = 'Stop'
$Root    = $PSScriptRoot
$Backend = Join-Path $Root 'backend'
$Mobile  = Join-Path $Root 'mobile'
$EnvFile = Join-Path $Mobile '.env'
$LogDir  = Join-Path $env:TEMP 'saferoute'
New-Item -ItemType Directory -Force $LogDir | Out-Null

$started = New-Object System.Collections.ArrayList
$origEnv = $null
$Utf8 = New-Object System.Text.UTF8Encoding $false

function Say($msg) { Write-Host "[saferoute] $msg" -ForegroundColor Cyan }

function Test-Ok($url) {
  try { (Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 5).StatusCode -eq 200 } catch { $false }
}

function Wait-Ok($url, $seconds, $what) {
  for ($i = 0; $i -lt $seconds; $i++) {
    if (Test-Ok $url) { return }
    Start-Sleep 1
  }
  throw "$what did not answer at $url within $seconds s. Logs: $LogDir"
}

function Test-PortBusy($p) {
  [bool](Get-NetTCPConnection -LocalPort $p -State Listen -ErrorAction SilentlyContinue)
}

function Find-Cloudflared {
  $c = Get-Command cloudflared -ErrorAction SilentlyContinue
  if ($c) { return $c.Source }
  foreach ($p in @("${env:ProgramFiles(x86)}\cloudflared\cloudflared.exe", "$env:ProgramFiles\cloudflared\cloudflared.exe")) {
    if (Test-Path $p) { return $p }
  }
  throw "cloudflared not found. Install it: winget install --id Cloudflare.cloudflared"
}

function Start-Tunnel($exe, $localUrl, $name) {
  $log = Join-Path $LogDir "cloudflared-$name.log"
  Remove-Item $log -ErrorAction SilentlyContinue
  $p = Start-Process -FilePath $exe -ArgumentList @('tunnel', '--url', $localUrl) `
         -RedirectStandardError $log -RedirectStandardOutput "$log.out" -WindowStyle Hidden -PassThru
  [void]$started.Add($p)
  for ($i = 0; $i -lt 60; $i++) {
    Start-Sleep 1
    if ($p.HasExited) { break }
    $m = Select-String -Path $log -Pattern 'https://[a-z0-9-]+\.trycloudflare\.com' -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($m) { return $m.Matches[0].Value }
  }
  throw "Cloudflare tunnel for $name did not start. Log: $log"
}

# Expo's own tunnel, as a second hidden Expo server. Returns its exp:// URL,
# or $null if it didn't come up (the Cloudflare one still works then).
function Start-ExpoTunnel($port) {
  $log = Join-Path $LogDir "expo-tunnel.log"
  $env:CI = '1'   # non-interactive: never stop and wait for a prompt
  try {
    $p = Start-Process -FilePath 'cmd.exe' -ArgumentList @('/c', 'npx', 'expo', 'start', '--tunnel', '--port', "$port") `
           -WorkingDirectory $Mobile -RedirectStandardOutput $log -RedirectStandardError "$log.err" -WindowStyle Hidden -PassThru
  } finally { Remove-Item Env:\CI -ErrorAction SilentlyContinue }
  [void]$started.Add($p)
  for ($i = 0; $i -lt 120; $i++) {
    Start-Sleep 1
    if ($p.HasExited) { break }
    try {
      $m = Invoke-WebRequest -Uri "http://localhost:$port" -Headers @{ 'expo-platform' = 'android' } -UseBasicParsing -TimeoutSec 5
      if ($m.Content -match '"hostUri":"([^"]+)"' -and $Matches[1] -notmatch '^(localhost|127\.|192\.|10\.|172\.)') {
        return "exp://$($Matches[1])"
      }
    } catch {}
  }
  return $null
}

function Show-Qr($url, $file, $label) {
  & npx qrcode -o $file -w 500 $url | Out-Null
  Write-Host ''
  Say $label
  & npx qrcode --small $url
  Write-Host "    $url" -ForegroundColor Green
  Say "QR image: $file"
}

try {
  if (Test-PortBusy $Port) { throw "Port $Port is already in use (an old Expo still running?). Close it, or run: start.cmd -Port 8085" }
  $wantCfApp     = -not $Lan -and -not $TunnelOnly
  $wantExpoTunnel = -not $Lan -and -not $CloudflareOnly
  if ($wantCfApp -and $wantExpoTunnel -and (Test-PortBusy $TunnelPort)) {
    throw "Port $TunnelPort is already in use. Close it, or run: start.cmd -TunnelPort 8087"
  }

  # 1. First-run setup
  $py = Join-Path $Backend '.venv\Scripts\python.exe'
  if (-not (Test-Path $py)) {
    Say 'First run: creating the backend virtualenv...'
    & python -m venv (Join-Path $Backend '.venv')
    & $py -m pip install -r (Join-Path $Backend 'requirements.txt')
  }
  if (-not (Test-Path (Join-Path $Backend '.env'))) {
    Copy-Item (Join-Path $Backend '.env.example') (Join-Path $Backend '.env')
  }
  if (-not (Test-Path (Join-Path $Mobile 'node_modules'))) {
    Say 'First run: installing the mobile dependencies...'
    Push-Location $Mobile; try { & npm ci } finally { Pop-Location }
  }

  # 2. Backend
  if (Test-Ok 'http://localhost:8000/health') {
    Say 'Backend already running on :8000, reusing it.'
  } else {
    Say 'Starting backend on :8000...'
    $p = Start-Process -FilePath $py -ArgumentList @('-m', 'uvicorn', 'app.main:app', '--host', '0.0.0.0', '--port', '8000') `
           -WorkingDirectory $Backend -RedirectStandardOutput (Join-Path $LogDir 'backend.out.log') `
           -RedirectStandardError (Join-Path $LogDir 'backend.log') -WindowStyle Hidden -PassThru
    [void]$started.Add($p)
    Wait-Ok 'http://localhost:8000/health' 90 'Backend'
  }

  # 3. Point the app at the backend. A stale tunnel URL in mobile\.env is
  #    removed in every mode; the original file is restored on exit.
  if (Test-Path $EnvFile) { $origEnv = [IO.File]::ReadAllText($EnvFile) } else { $origEnv = '' }
  $lines = @($origEnv -split "`r?`n" | Where-Object { $_ -notmatch '^\s*EXPO_PUBLIC_API_BASE_URL\s*=' })

  if ($Lan) {
    Say 'LAN mode: no tunnels, the app finds the backend on this PC by itself.'
  } else {
    $cf = Find-Cloudflared
    Say 'Opening Cloudflare tunnel for the backend...'
    $apiUrl = Start-Tunnel $cf 'http://localhost:8000' 'backend'
    Wait-Ok "$apiUrl/health" 60 'Backend tunnel'
    Say "Backend tunnel: $apiUrl"
    $lines += "EXPO_PUBLIC_API_BASE_URL=$apiUrl"
  }
  [IO.File]::WriteAllText($EnvFile, (($lines -join "`r`n").TrimEnd() + "`r`n"), $Utf8)

  # 4. Expo
  Push-Location $Mobile
  try {
    $expoArgs = @('expo', 'start', '--port', "$Port", '--clear')
    $cfAppUrl = $null; $tunnelAppUrl = $null

    if ($wantExpoTunnel -and $wantCfApp) {
      Say "Starting backup Expo on :$TunnelPort behind Expo's tunnel (up to 2 min)..."
      $tunnelAppUrl = Start-ExpoTunnel $TunnelPort
      if (-not $tunnelAppUrl) { Say "Expo's tunnel didn't come up (log: $LogDir\expo-tunnel.log). Continuing with Cloudflare only." }
    }
    if ($wantCfApp) {
      Say 'Opening Cloudflare tunnel for Expo...'
      $metroUrl = Start-Tunnel $cf "http://localhost:$Port" 'expo'
      $env:EXPO_PACKAGER_PROXY_URL = $metroUrl
      $cfAppUrl = $metroUrl -replace '^https://', 'exps://'
    }
    if ($TunnelOnly) { $expoArgs += '--tunnel' }
    if ($Lan) { $expoArgs += '--lan' }

    if ($tunnelAppUrl) { Show-Qr $tunnelAppUrl (Join-Path $Mobile 'saferoute-qr-tunnel.png') "BACKUP - Expo tunnel (port $TunnelPort):" }
    if ($cfAppUrl) {
      Show-Qr $cfAppUrl (Join-Path $Mobile 'saferoute-qr.png') "MAIN - Cloudflare (port $Port), use this on school Wi-Fi:"
      Write-Host ''
      Say "Scan with Expo Go, or 'Enter URL manually'. Ignore the QR Expo prints below."
      Write-Host ''
    }
    & npx @expoArgs
  } finally { Pop-Location }
}
catch {
  Write-Host "[saferoute] $($_.Exception.Message)" -ForegroundColor Red
}
finally {
  Say 'Stopping...'
  foreach ($p in $started) {
    try { if (-not $p.HasExited) { & taskkill.exe /T /F /PID $p.Id 2>&1 | Out-Null } } catch {}
  }
  if ($null -ne $origEnv) { [IO.File]::WriteAllText($EnvFile, $origEnv, $Utf8) }
  Remove-Item Env:\EXPO_PACKAGER_PROXY_URL -ErrorAction SilentlyContinue
}
