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

    $root = Join-Path (Get-Location) "dist"
    $normal = Join-Path $root "AndroidNova\AndroidNova.exe"
    $debug = Join-Path $root "AndroidNova-debug\AndroidNova-debug.exe"
    $zip = Join-Path $root "AndroidNova-Emulator-Test.zip"
    if (Test-Path $zip) { Remove-Item $zip -Force }
    Compress-Archive -Path @($normal, $debug, (Join-Path $root "AndroidNova\*"), (Join-Path $root "AndroidNova-debug\*")) -DestinationPath $zip -CompressionLevel Optimal
    Write-Host "Created $zip"
} catch {
    Write-Error $_
    Write-Host "BUILD FAILED. See $log for the complete transcript."
    exit 1
} finally {
    Stop-Transcript | Out-Null
}
