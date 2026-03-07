param(
  [string]$Name = "TEM8Practice"
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

$compilerCandidates = @(
  "C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
  "C:\Program Files\Inno Setup 6\ISCC.exe",
  (Join-Path $env:LOCALAPPDATA "Programs\Inno Setup 6\ISCC.exe")
)

function Get-InnoCompiler {
  foreach ($candidate in $compilerCandidates) {
    if (Test-Path $candidate) {
      return $candidate
    }
  }
  return $null
}

$compiler = Get-InnoCompiler
if (-not $compiler) {
  $winget = Get-Command winget -ErrorAction SilentlyContinue
  if (-not $winget) {
    throw "Inno Setup was not found and winget is unavailable."
  }

  winget install --id JRSoftware.InnoSetup -e --silent --accept-package-agreements --accept-source-agreements
  $compiler = Get-InnoCompiler
  if (-not $compiler) {
    throw "Inno Setup install did not produce ISCC.exe in the expected location."
  }
}

& ".\build_exe.ps1" -Name $Name
& $compiler ".\installer.iss"
