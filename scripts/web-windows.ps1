param(
    [ValidateSet('Start', 'Stop')]
    [string]$Action = 'Start',
    [switch]$NoBrowser
)

$ErrorActionPreference = 'Stop'
$projectDir = Split-Path -Parent $PSScriptRoot
$pythonExe = Join-Path $projectDir '.venv\Scripts\python.exe'
$runDir = Join-Path $projectDir '.run'
$url = 'http://127.0.0.1:8080'

function Get-AppListener {
    Get-NetTCPConnection -LocalPort 8080 -State Listen -ErrorAction SilentlyContinue |
        Select-Object -First 1
}

function Assert-AppProcess($listener) {
    $serverProcess = Get-CimInstance Win32_Process -Filter "ProcessId=$($listener.OwningProcess)"
    $launcherProcess = if ($serverProcess) {
        Get-CimInstance Win32_Process -Filter "ProcessId=$($serverProcess.ParentProcessId)"
    }
    # Windows venv's python.exe redirects execution to the base interpreter.
    $belongsToProject = $serverProcess.ExecutablePath -eq $pythonExe -or
        $launcherProcess.ExecutablePath -eq $pythonExe
    if (-not $serverProcess -or
        -not $belongsToProject -or
        $serverProcess.CommandLine -notlike '*uvicorn web.backend.main:app*') {
        throw 'Port 8080 belongs to another application.'
    }
}

$listener = Get-AppListener
if ($listener) { Assert-AppProcess $listener }

if ($Action -eq 'Stop') {
    if ($listener) {
        Stop-Process -Id $listener.OwningProcess -Force
        Write-Host 'Claude Session Patcher stopped.'
    } else {
        Write-Host 'Claude Session Patcher is already stopped.'
    }
    exit 0
}

if (-not $listener) {
    if (-not (Test-Path -LiteralPath $pythonExe)) {
        throw 'The project virtual environment is missing.'
    }
    if (-not (Test-Path -LiteralPath (Join-Path $projectDir 'web\frontend\dist\index.html'))) {
        throw 'The frontend build is missing.'
    }
    New-Item -ItemType Directory -Path $runDir -Force | Out-Null
    $env:PYTHONUTF8 = '1'
    $env:PYTHONIOENCODING = 'utf-8'
    $server = Start-Process -FilePath $pythonExe -ArgumentList @(
        '-X', 'utf8', '-m', 'uvicorn', 'web.backend.main:app',
        '--host', '127.0.0.1', '--port', '8080'
    ) -WorkingDirectory $projectDir -WindowStyle Hidden -PassThru `
        -RedirectStandardOutput (Join-Path $runDir 'web.stdout.log') `
        -RedirectStandardError (Join-Path $runDir 'web.stderr.log')
}

$ready = $false
for ($attempt = 0; $attempt -lt 30; $attempt++) {
    try {
        $response = Invoke-WebRequest -Uri "$url/api/version" -UseBasicParsing -TimeoutSec 2
        if ($response.StatusCode -eq 200) { $ready = $true; break }
    } catch {
        if ($server -and $server.HasExited) { break }
        Start-Sleep -Milliseconds 500
    }
}
if (-not $ready) {
    throw "Startup failed. See $runDir\web.stderr.log"
}
Write-Host "Claude Session Patcher is running at $url"
if (-not $NoBrowser) { Start-Process $url }
