# Automated Windows Build and Packaging Workflow for Local Markdown
[CmdletBinding()]
param(
    [switch]$SkipTests = $false
)

$ErrorActionPreference = "Stop"
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "   Local Markdown - Windows Production Build      " -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

$ProjectRoot = (Get-Location).Path

# 0. Locate Python, PyInstaller, and Pytest (.venv or system PATH in CI)
$VenvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$VenvPyInstaller = Join-Path $ProjectRoot ".venv\Scripts\pyinstaller.exe"
$VenvPytest = Join-Path $ProjectRoot ".venv\Scripts\pytest.exe"

if (Test-Path $VenvPython) {
    $PythonExe = $VenvPython
    $PyInstallerExe = $VenvPyInstaller
    $PytestExe = $VenvPytest
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $PythonExe = (Get-Command python).Source
    $PyInstallerExe = if (Get-Command pyinstaller -ErrorAction SilentlyContinue) { (Get-Command pyinstaller).Source } else { "pyinstaller" }
    $PytestExe = if (Get-Command pytest -ErrorAction SilentlyContinue) { (Get-Command pytest).Source } else { "pytest" }
} else {
    throw "Python runtime not found in .venv or on system PATH."
}

# 1. Run Tests
if (-not $SkipTests) {
    Write-Host "`n[1/5] Running automated tests..." -ForegroundColor Yellow
    $env:PYTHONPATH = "src"
    & $PytestExe -v tests/unit tests/integration
    if ($LASTEXITCODE -ne 0) {
        throw "Unit/Integration tests failed! Aborting build."
    }
} else {
    Write-Host "`n[1/5] Skipping tests as requested." -ForegroundColor Gray
}

# Ensure vendor offline runtimes are staged
$loCheck = Join-Path $ProjectRoot "vendor\libreoffice\program\soffice.exe"
$tessCheck = Join-Path $ProjectRoot "vendor\tesseract\tesseract.exe"
if (-not (Test-Path $loCheck) -or -not (Test-Path $tessCheck)) {
    Write-Host "`nStaging vendor runtimes (LibreOffice & Tesseract)..." -ForegroundColor Yellow
    & powershell -ExecutionPolicy Bypass -File (Join-Path $ProjectRoot "scripts\setup-vendor.ps1")
}

# 2. PyInstaller Build
Write-Host "`n[2/5] Freezing application with PyInstaller..." -ForegroundColor Yellow
& $PyInstallerExe packaging\LocalMarkdown.spec --clean --noconfirm
if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller build failed!"
}

# 3. Verify Bundle
Write-Host "`n[3/5] Verifying frozen bundle payload..." -ForegroundColor Yellow
& powershell -ExecutionPolicy Bypass -File scripts\verify-bundle.ps1

# 4. Inno Setup Compiler
Write-Host "`n[4/5] Compiling Inno Setup installer..." -ForegroundColor Yellow
$isccPaths = @(
    "C:\Users\infor\AppData\Local\Programs\Inno Setup 6\ISCC.exe",
    "C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
    "C:\Program Files\Inno Setup 6\ISCC.exe"
)
$iscc = $isccPaths | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $iscc -and (Get-Command iscc -ErrorAction SilentlyContinue)) {
    $iscc = (Get-Command iscc).Source
}
if (-not $iscc) {
    throw "Inno Setup Compiler (ISCC.exe) not found!"
}

New-Item -ItemType Directory -Force -Path dist_release | Out-Null
& $iscc packaging\installer.iss
if ($LASTEXITCODE -ne 0) {
    throw "Inno Setup compilation failed!"
}

# 5. Build Portable ZIP and Hashes
Write-Host "`n[5/5] Building portable ZIP and computing release hashes..." -ForegroundColor Yellow
& $PythonExe -c @"
import zipfile, os, re
from pathlib import Path

init_text = Path('src/local_markdown/__init__.py').read_text(encoding='utf-8')
m = re.search(r'__version__\s*=\s*[\"\\\']([^\"\\\']+)[\"\\\']', init_text)
ver = m.group(1) if m else '1.0.1'

dist_dir = Path('dist/LocalMarkdown')
zip_path = Path(f'dist_release/LocalMarkdown-Portable-{ver}-x64.zip')
if zip_path.exists():
    zip_path.unlink()
with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
    for root, dirs, files in os.walk(dist_dir):
        for f in files:
            full = Path(root) / f
            rel = 'LocalMarkdown/' + str(full.relative_to(dist_dir)).replace('\\', '/')
            zf.write(full, rel)
"@

$hashes = Get-FileHash dist_release\LocalMarkdown-* -Algorithm SHA256
$hashes | ForEach-Object { "$($_.Hash)  $((Split-Path $_.Path -Leaf))" } | Out-File -Encoding utf8 dist_release\SHA256SUMS.txt

Write-Host "`n==================================================" -ForegroundColor Green
Write-Host "   Release Artifacts Generated Successfully!       " -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Green
$hashes | Select-Object Path, Hash | Format-List
Get-ChildItem dist_release\* | Select-Object Name, Length | Format-Table -AutoSize
