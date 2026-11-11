$ErrorActionPreference = 'Stop'
$claudeConfigDir = if ($env:CLAUDE_CONFIG_DIR) { $env:CLAUDE_CONFIG_DIR } else { Join-Path $env:USERPROFILE '.claude' }
if (-not (Test-Path -LiteralPath (Join-Path $claudeConfigDir 'CLAUDE.md'))) {
    throw 'Run claude-patcher --install-config first.'
}

# Native CLI processes need proxy environment variables to use Windows' proxy.
if (-not $env:HTTPS_PROXY) {
    $internetSettings = Get-ItemProperty -LiteralPath 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings' -ErrorAction SilentlyContinue
    if ($internetSettings.ProxyEnable -and $internetSettings.ProxyServer) {
        $proxyServer = [string]$internetSettings.ProxyServer
        if ($proxyServer -match '=') {
            $httpsProxy = $proxyServer -split ';' | Where-Object { $_ -like 'https=*' } | Select-Object -First 1
            $proxyServer = if ($httpsProxy) { $httpsProxy.Substring(6) } else { '' }
        }
        if ($proxyServer) {
            if ($proxyServer -notmatch '^https?://') { $proxyServer = 'http://' + $proxyServer }
            $env:HTTPS_PROXY = $proxyServer
            if (-not $env:HTTP_PROXY) { $env:HTTP_PROXY = $proxyServer }
        }
    }
}

$claudeCmd = Join-Path (& npm.cmd prefix -g) 'claude.cmd'
if (-not (Test-Path -LiteralPath $claudeCmd)) { throw 'Claude Code CLI is not installed.' }
& $claudeCmd @args
exit $LASTEXITCODE
