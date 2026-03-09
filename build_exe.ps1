param(
  [string]$Name = "TEM8Practice"
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

$distDir = Join-Path $root "dist"
$distDataDir = Join-Path $distDir "data"
$distLogsDir = Join-Path $distDir "logs"

python -m PyInstaller `
  --noconfirm `
  --clean `
  --onefile `
  --name $Name `
  --add-data "app\static;app\static" `
  --add-data "data\questions.json;data" `
  --add-data "data\answer_key.json;data" `
  --add-data "data\answer_key.template.json;data" `
  --add-data "data\ai_review.template.json;data" `
  --add-data "data\user_progress.json;data" `
  gateway.py

New-Item -ItemType Directory -Force -Path $distDataDir | Out-Null
Copy-Item ".\data\questions.json" $distDataDir -Force
Copy-Item ".\data\answer_key.json" $distDataDir -Force
Copy-Item ".\data\answer_key.template.json" $distDataDir -Force
Copy-Item ".\data\ai_review.template.json" $distDataDir -Force
Copy-Item ".\data\user_progress.json" $distDataDir -Force

if (Test-Path $distLogsDir) {
  Remove-Item $distLogsDir -Recurse -Force
}
New-Item -ItemType Directory -Force -Path $distLogsDir | Out-Null
