$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")

$log = Join-Path (Get-Location) "build_windows.log"
Start-Transcript -Path $log -Append | Out-Null

function Invoke-Build([bool] $DebugBuild) {
    if ($DebugBuild) {
        $env:ANDROIDNOVA_DEBUG = "1"
        $label = "diagnostic"
    } else {
        Remove-Item Env:ANDROIDNOVA_DEBUG -ErrorAction SilentlyContinue
        $label = "normal"
    }

    Write-Host "=== AndroidNova $label PyInstaller build ==="
    python -m PyInstaller --noconfirm --clean packaging\androidnova.spec
    if ($LASTEXITCODE -ne 0) { throw "PyInstaller $label build failed with exit code $LASTEXITCODE" }

    $name = if ($DebugBuild) { "AndroidNova-debug" } else { "AndroidNova" }
    $dir = Join-Path (Get-Location) "dist\$name"
    $exe = Join-Path $dir "$name.exe"
    if (-not (Test-Path $exe)) { throw "Expected executable was not created: $exe" }
    Write-Host "Created: $exe"
}

try {
    $dist = Join-Path (Get-Location) "dist"
    if (Test-Path $dist) { Remove-Item $dist -Recurse -Force }
    $build = Join-Path (Get-Location) "build"
    if (Test-Path $build) { Remove-Item $build -Recurse -Force }

    python --version
    if ($LASTEXITCODE -ne 0) { throw "Python is not available" }
    python -m pip install -r packaging\requirements-build.txt
    if ($LASTEXITCODE -ne 0) { throw "Build dependencies could not be installed" }
    python -m PyInstaller --version
    if ($LASTEXITCODE -ne 0) { throw "PyInstaller is not available" }

    Invoke-Build $false
    Invoke-Build $true

    $normalDir = Join-Path $dist "AndroidNova"
    $debugDir = Join-Path $dist "AndroidNova-debug"
    $normal = Join-Path $normalDir "AndroidNova.exe"
    $debug = Join-Path $debugDir "AndroidNova-debug.exe"
    $package = Join-Path $dist "AndroidNova-Emulator-Test"
    $zip = Join-Path $dist "AndroidNova-Emulator-Test.zip"

    if (-not (Test-Path $normal)) { throw "Normal executable missing: $normal" }
    if (-not (Test-Path $debug)) { throw "Diagnostic executable missing: $debug" }
    if (Test-Path $package) { Remove-Item $package -Recurse -Force }
    New-Item -ItemType Directory -Path $package | Out-Null
    Copy-Item $normalDir (Join-Path $package "AndroidNova") -Recurse
    Copy-Item $debugDir (Join-Path $package "AndroidNova-debug") -Recurse
    Copy-Item README.md (Join-Path $package "README.md")
    if (Test-Path $zip) { Remove-Item $zip -Force }
    Compress-Archive -Path (Join-Path $package "*") -DestinationPath $zip -CompressionLevel Optimal
    Write-Host "Created $zip"
} catch {
    Write-Error $_
    Write-Host "BUILD FAILED. See $log for the complete transcript."
    exit 1
} finally {
    Stop-Transcript | Out-Null
}
