param(
    [ValidateSet('Start', 'Stop', 'Install', 'Uninstall', 'Serve')]
    [string]$Action = 'Start',
    [switch]$NoBrowser
)

$ErrorActionPreference = 'Stop'
$projectDir = Split-Path -Parent $PSScriptRoot
$pythonExe = Join-Path $projectDir '.venv\Scripts\python.exe'
$runDir = Join-Path $projectDir '.run'
$url = 'http://127.0.0.1:8080'
$taskName = 'ClaudeSessionPatcher-Web'

function Get-ResidentTask {
    $task = Get-ScheduledTask -TaskName $taskName -TaskPath '\' -ErrorAction SilentlyContinue
    if ($task -and ($task.Actions.Count -ne 1 -or
        $task.Actions[0].Arguments -ne "-NoProfile -NonInteractive -WindowStyle Hidden -File `"$PSCommandPath`" -Action Serve")) {
        throw "Scheduled task $taskName belongs to another installation."
    }
    return $task
}

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
$residentTask = Get-ResidentTask

if ($Action -eq 'Install') {
    if (-not (Test-Path -LiteralPath $pythonExe) -or
        -not (Test-Path -LiteralPath (Join-Path $projectDir 'web\frontend\dist\index.html'))) {
        throw 'Install the virtual environment and build the frontend first.'
    }
    $userName = [Security.Principal.WindowsIdentity]::GetCurrent().Name
    $taskAction = New-ScheduledTaskAction -Execute (Join-Path $PSHOME 'powershell.exe') `
        -Argument "-NoProfile -NonInteractive -WindowStyle Hidden -File `"$PSCommandPath`" -Action Serve" `
        -WorkingDirectory $projectDir
    $trigger = New-ScheduledTaskTrigger -AtLogOn -User $userName
    $principal = New-ScheduledTaskPrincipal -UserId $userName -LogonType Interactive -RunLevel Limited
    $settings = New-ScheduledTaskSettingsSet -Hidden -StartWhenAvailable `
        -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
        -MultipleInstances IgnoreNew -ExecutionTimeLimit ([TimeSpan]::Zero) `
        -RestartCount 999 -RestartInterval (New-TimeSpan -Minutes 1)
    Register-ScheduledTask -TaskName $taskName -TaskPath '\' -Action $taskAction `
        -Trigger $trigger -Principal $principal -Settings $settings `
        -Description 'Claude Session Patcher: user logon, hidden, loopback-only web service.' -Force | Out-Null
    $residentTask = Get-ResidentTask
    if ($listener -and $residentTask.State -ne 'Running') {
        Stop-Process -Id $listener.OwningProcess -Force
        Wait-Process -Id $listener.OwningProcess -ErrorAction SilentlyContinue
        $listener = $null
    }
    Write-Host "Installed logon task: $taskName"
    $Action = 'Start'
}

if ($Action -in @('Stop', 'Uninstall') -and $residentTask) {
    Stop-ScheduledTask -TaskName $taskName -TaskPath '\'
    if ($Action -eq 'Uninstall') {
        Unregister-ScheduledTask -TaskName $taskName -TaskPath '\' -Confirm:$false
        Write-Host 'Removed the automatic logon task.'
    }
    $listener = Get-AppListener
    if ($listener) { Assert-AppProcess $listener }
}

if ($Action -in @('Stop', 'Uninstall')) {
    if ($listener) {
        Stop-Process -Id $listener.OwningProcess -Force
        Write-Host 'Claude Session Patcher stopped.'
    } else {
        Write-Host 'Claude Session Patcher is already stopped.'
    }
    exit 0
}

if ($Action -eq 'Serve' -and $listener) {
    throw 'The web server is already running outside this task.'
}

if ($Action -eq 'Start' -and $residentTask -and $residentTask.State -ne 'Running') {
    Start-ScheduledTask -TaskName $taskName -TaskPath '\'
}

if (-not $listener -and ($Action -eq 'Serve' -or -not $residentTask)) {
    if (-not (Test-Path -LiteralPath $pythonExe)) {
        throw 'The project virtual environment is missing.'
    }
    if (-not (Test-Path -LiteralPath (Join-Path $projectDir 'web\frontend\dist\index.html'))) {
        throw 'The frontend build is missing.'
    }
    New-Item -ItemType Directory -Path $runDir -Force | Out-Null
    $env:PYTHONUTF8 = '1'
    $env:PYTHONIOENCODING = 'utf-8'
    do {
        try {
            $server = Start-Process -FilePath $pythonExe -ArgumentList @(
                '-X', 'utf8', '-m', 'uvicorn', 'web.backend.main:app',
                '--host', '127.0.0.1', '--port', '8080'
            ) -WorkingDirectory $projectDir -WindowStyle Hidden -PassThru -Wait:($Action -eq 'Serve') `
                -RedirectStandardOutput (Join-Path $runDir 'web.stdout.log') `
                -RedirectStandardError (Join-Path $runDir 'web.stderr.log')
            if ($Action -eq 'Serve') {
                Add-Content -LiteralPath (Join-Path $runDir 'resident.log') `
                    -Value "$(Get-Date -Format o) Server exited: code=$($server.ExitCode). Restarting in 5 seconds."
            }
        } catch {
            if ($Action -ne 'Serve') { throw }
            Add-Content -LiteralPath (Join-Path $runDir 'resident.log') `
                -Value "$(Get-Date -Format o) Launch failed: $($_.Exception.Message). Retrying in 5 seconds."
        }
        if ($Action -eq 'Serve') { Start-Sleep -Seconds 5 }
    } while ($Action -eq 'Serve')
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
