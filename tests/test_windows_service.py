import os
import shutil
import subprocess
from pathlib import Path

import pytest


@pytest.mark.skipif(os.name != "nt", reason="Windows resident service launcher")
@pytest.mark.parametrize("server_exit", [0, 23])
def test_resident_task_relaunches_after_server_exit(tmp_path, server_exit):
    project = tmp_path / "project with spaces"
    scripts = project / "scripts"
    scripts.mkdir(parents=True)
    source = Path(__file__).resolve().parents[1] / "scripts" / "web-windows.ps1"
    shutil.copy2(source, scripts / source.name)
    for relative in (".venv/Scripts/python.exe", "web/frontend/dist/index.html"):
        target = project / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.touch()
    # No real scheduler or server is used. A short-lived native process exercises
    # PowerShell's real Start-Process/ExitCode behavior in the isolated project.
    harness = tmp_path / "harness.ps1"
    harness.write_text(
        """param([string]$Target, [int]$ServerExit)
function Get-ScheduledTask { return $null }
function Get-NetTCPConnection { return $null }
$script:Launches = 0
function Start-Process {
    param($FilePath, $ArgumentList, $WorkingDirectory, $WindowStyle,
        [switch]$PassThru, [switch]$Wait,
        $RedirectStandardOutput, $RedirectStandardError)
    $script:Launches++
    if ($script:Launches -eq 2) { [Environment]::Exit(42) }
    Microsoft.PowerShell.Management\\Start-Process -FilePath $env:ComSpec `
        -ArgumentList "/c exit $ServerExit" -WorkingDirectory $WorkingDirectory `
        -WindowStyle Hidden -PassThru -Wait:$Wait `
        -RedirectStandardOutput $RedirectStandardOutput `
        -RedirectStandardError $RedirectStandardError
}
& $Target -Action Serve -NoBrowser
exit $LASTEXITCODE
""",
        encoding="utf-8",
    )
    result = subprocess.run(
        ["powershell.exe", "-NoProfile", "-File", str(harness),
         "-Target", str(scripts / source.name), "-ServerExit", str(server_exit)],
        capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 42, result.stderr
    assert f"code={server_exit}" in (project / ".run/resident.log").read_text()
