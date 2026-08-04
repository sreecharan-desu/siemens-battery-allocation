# Windows PowerShell — delegates to cross-platform install.py
# Usage: .\scripts\install.ps1
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)

if (Get-Command python -ErrorAction SilentlyContinue) {
    python scripts/install.py @args
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
    py -3 scripts/install.py @args
} else {
    Write-Error "Python not found. Install Python 3.11+ from https://www.python.org/downloads/"
}
