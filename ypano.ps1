<#
.SYNOPSIS
    PowerShell launcher for Yandex Panorama Downloader on Windows.
.EXAMPLE
    .\ypano.ps1 "https://yandex.ru/maps/..."
#>

[CmdletBinding()]
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$ScriptArgs
)

$PythonExe = Get-Command python.exe -ErrorAction SilentlyContinue
if (-not $PythonExe) {
    $PythonExe = Get-Command py.exe -ErrorAction SilentlyContinue
}

if (-not $PythonExe) {
    Write-Error "Python не найден. Установите Python с https://www.python.org/ и добавьте в PATH."
    exit 1
}

& $PythonExe.Source -m yandex_panorama.cli @ScriptArgs
exit $LASTEXITCODE
