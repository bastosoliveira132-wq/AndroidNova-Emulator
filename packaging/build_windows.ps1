$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")
$dist = Join-Path (Get-Location) "dist"
if (Test-Path $dist) { Remove-Item $dist -Recurse -Force }
$build = Join-Path (Get-Location) "build"
if (Test-Path $build) { Remove-Item $build -Recurse -Force }
python -m pip install -r packaging\requirements-build.txt
python -m PyInstaller --noconfirm --clean packaging\androidnova.spec
Copy-Item README.md (Join-Path $dist "AndroidNova-Emulator\README.md")
$zip = Join-Path $dist "AndroidNova-Emulator-Test.zip"
if (Test-Path $zip) { Remove-Item $zip -Force }
Compress-Archive -Path (Join-Path $dist "AndroidNova-Emulator\*") -DestinationPath $zip -CompressionLevel Optimal
Write-Host "Created $zip"
