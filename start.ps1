param(
  [string]$BindHost = "127.0.0.1",
  [int]$Port = 8000,
  [switch]$NoBrowser
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

$pythonCommand = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCommand) {
  $pythonCommand = Get-Command py -ErrorAction SilentlyContinue
}

if (-not $pythonCommand) {
  throw "Python was not found. Please install Python 3.11 or newer."
}

$pythonExe = $pythonCommand.Source
$args = @("gateway.py", "--host", $BindHost, "--port", $Port)
if ($NoBrowser) {
  $args += "--no-browser"
}

& $pythonExe @args
