# MC Server Framework - Build Script (PowerShell)
# This script uses PyInstaller to package the project into a standalone .exe

Write-Host "==============================================================" -ForegroundColor Cyan
Write-Host "    MC Server Framework - Application Build Tool" -ForegroundColor Cyan
Write-Host "==============================================================" -ForegroundColor Cyan
Write-Host ""

# Check virtual environment
if (-not $env:VIRTUAL_ENV) {
    Write-Host "WARNING: Virtual environment not detected, trying to activate..." -ForegroundColor Yellow
    if (Test-Path '.\env\Scripts\Activate.ps1') {
        & '.\env\Scripts\Activate.ps1'
        Write-Host "OK Virtual environment activated" -ForegroundColor Green
    } else {
        Write-Host "ERROR: Virtual environment not found. Please run:" -ForegroundColor Red
        Write-Host "   python -m venv env" -ForegroundColor Yellow
        Write-Host '   .\env\Scripts\Activate.ps1' -ForegroundColor Yellow
        Write-Host "   pip install -r requirements.txt" -ForegroundColor Yellow
        exit 1
    }
}

# Check PyInstaller
Write-Host "Checking PyInstaller..." -ForegroundColor Cyan
$pyinstallerInstalled = pip list | Select-String "pyinstaller"
if (-not $pyinstallerInstalled) {
    Write-Host "WARNING: PyInstaller not installed, installing..." -ForegroundColor Yellow
    pip install pyinstaller
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: PyInstaller installation failed" -ForegroundColor Red
        exit 1
    }
    Write-Host "OK PyInstaller installed" -ForegroundColor Green
} else {
    Write-Host "OK PyInstaller installed" -ForegroundColor Green
}

# Clean old build files
Write-Host ""
Write-Host "Cleaning old build files..." -ForegroundColor Cyan
if (Test-Path '.\build') {
    Remove-Item -Recurse -Force '.\build'
    Write-Host "OK Cleaned build directory" -ForegroundColor Green
}
if (Test-Path '.\dist') {
    Remove-Item -Recurse -Force '.\dist'
    Write-Host "OK Cleaned dist directory" -ForegroundColor Green
}

# Run build
Write-Host ""
Write-Host "Starting build process..." -ForegroundColor Cyan
Write-Host "This may take a few minutes, please wait..." -ForegroundColor Yellow
Write-Host ""

pyinstaller mc-server-framework.spec --clean

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "ERROR: Build failed, please check error messages" -ForegroundColor Red
    exit 1
}

# Check output
Write-Host ""
Write-Host "==============================================================" -ForegroundColor Green
Write-Host "    OK Build Complete!" -ForegroundColor Green
Write-Host "==============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Output location: " -NoNewline
Write-Host '.\dist\mc-server-framework\' -ForegroundColor Yellow
Write-Host ""
Write-Host "Main executable: " -NoNewline
Write-Host '.\dist\mc-server-framework\mc-server-framework.exe' -ForegroundColor Yellow
Write-Host ""

# Show file size
$exePath = '.\dist\mc-server-framework\mc-server-framework.exe'
if (Test-Path $exePath) {
    $size = (Get-Item $exePath).Length / 1MB
    Write-Host "File size: " -NoNewline
    Write-Host "$([math]::Round($size, 2)) MB" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "==============================================================" -ForegroundColor Cyan
Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host "==============================================================" -ForegroundColor Cyan
Write-Host "1. Test the executable:" -ForegroundColor White
Write-Host '   cd dist\mc-server-framework' -ForegroundColor Yellow
Write-Host '   .\mc-server-framework.exe' -ForegroundColor Yellow
Write-Host ""
Write-Host "2. Create release package:" -ForegroundColor White
Write-Host '   Compress dist\mc-server-framework directory to ZIP' -ForegroundColor Yellow
Write-Host '   or run: .\package.ps1' -ForegroundColor Yellow
Write-Host ""
Write-Host "3. View documentation:" -ForegroundColor White
Write-Host '   Read BUILD.md for more build options' -ForegroundColor Yellow
Write-Host ""
