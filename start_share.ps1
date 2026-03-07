param(
  [int]$Port = 8000
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
& $pythonExe "gateway.py" "--host" "0.0.0.0" "--port" $Port "--no-browser"
