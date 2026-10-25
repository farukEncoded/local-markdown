# setup-vendor.ps1 - Automated staging of offline vendor runtimes for Local Markdown
# Downloads and extracts LibreOffice and Tesseract OCR if not already staged.

param(
    [switch]$Force = $false
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
Set-Location $ProjectRoot

Write-Host "=== Setting up Local Markdown Vendor Runtimes ===" -ForegroundColor Cyan

$TesseractDir = Join-Path $ProjectRoot "vendor\tesseract"
$LibreOfficeDir = Join-Path $ProjectRoot "vendor\libreoffice"
$TempDownloads = Join-Path $ProjectRoot "vendor_downloads"

# 1. Tesseract OCR Runtime
$tessExe = Join-Path $TesseractDir "tesseract.exe"
$tessData = Join-Path $TesseractDir "tessdata\eng.traineddata"

if ($Force -or -not (Test-Path $tessExe) -or -not (Test-Path $tessData)) {
    Write-Host "`n[1/2] Staging Tesseract OCR 5.5.3 x64..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Force -Path $TempDownloads | Out-Null
    New-Item -ItemType Directory -Force -Path $TesseractDir | Out-Null

    # Download Tesseract installer
    $tessInstallerUrl = "https://digi.bib.uni-mannheim.de/tesseract/tesseract-ocr-w64-setup-5.5.0.20241111.exe"
    $tessInstallerPath = Join-Path $TempDownloads "tesseract-setup.exe"
    
    if (-not (Test-Path $tessInstallerPath)) {
        Write-Host "Downloading Tesseract installer..." -ForegroundColor Gray
        Invoke-WebRequest -Uri $tessInstallerUrl -OutFile $tessInstallerPath
    }

    # Extract using 7-Zip or installer silent extraction
    Write-Host "Extracting Tesseract..." -ForegroundColor Gray
    Start-Process $tessInstallerPath -ArgumentList "/S /D=$TesseractDir" -Wait

    # Verify English traineddata
    if (-not (Test-Path $tessData)) {
        Write-Host "Downloading English traineddata..." -ForegroundColor Gray
        $engUrl = "https://github.com/tesseract-ocr/tessdata_fast/raw/main/eng.traineddata"
        New-Item -ItemType Directory -Force -Path (Join-Path $TesseractDir "tessdata") | Out-Null
        Invoke-WebRequest -Uri $engUrl -OutFile $tessData
    }
    Write-Host "[PASS] Tesseract OCR staged successfully." -ForegroundColor Green
} else {
    Write-Host "[1/2] Tesseract OCR already staged." -ForegroundColor Green
}

# 2. LibreOffice Standalone Headless Runtime
$loSoffice = Join-Path $LibreOfficeDir "program\soffice.exe"

if ($Force -or -not (Test-Path $loSoffice)) {
    Write-Host "`n[2/2] Staging LibreOffice 26.8.1.1 Headless Runtime..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Force -Path $TempDownloads | Out-Null
    
    $loMsiUrl = "https://download.documentfoundation.org/libreoffice/stable/26.8.1/win/x86_64/LibreOffice_26.8.1_Win_x86-64.msi"
    $loMsiPath = Join-Path $TempDownloads "LibreOffice_Win_x86-64.msi"
    $extractDir = Join-Path $ProjectRoot "vendor_extracted_lo"

    if (-not (Test-Path $loMsiPath)) {
        Write-Host "Downloading LibreOffice MSI..." -ForegroundColor Gray
        Invoke-WebRequest -Uri $loMsiUrl -OutFile $loMsiPath
    }

    Write-Host "Extracting administrative MSI..." -ForegroundColor Gray
    Start-Process msiexec.exe -ArgumentList "/a `"$loMsiPath`" /qb TARGETDIR=`"$extractDir`"" -Wait

    # Consolidate program and share folders
    New-Item -ItemType Directory -Force -Path $LibreOfficeDir | Out-Null
    Move-Item (Join-Path $extractDir "program") $LibreOfficeDir -Force
    Move-Item (Join-Path $extractDir "share") $LibreOfficeDir -Force
    Move-Item (Join-Path $extractDir "license.txt") $LibreOfficeDir -Force -ErrorAction SilentlyContinue
    Move-Item (Join-Path $extractDir "NOTICE") $LibreOfficeDir -Force -ErrorAction SilentlyContinue

    # Prune non-English dictionaries to save 450 MB
    Write-Host "Pruning foreign language dictionaries..." -ForegroundColor Gray
    Get-ChildItem -Path (Join-Path $LibreOfficeDir "share\extensions") -Directory -Filter "dict-*" | 
        Where-Object { $_.Name -ne "dict-en" } | 
        Remove-Item -Recurse -Force

    # Clean up extraction temp
    Remove-Item -Recurse -Force $extractDir -ErrorAction SilentlyContinue
    Remove-Item -Recurse -Force $TempDownloads -ErrorAction SilentlyContinue

    Write-Host "[PASS] LibreOffice Headless Runtime staged successfully." -ForegroundColor Green
} else {
    Write-Host "[2/2] LibreOffice Standalone Runtime already staged." -ForegroundColor Green
}

Write-Host "`n=== Vendor Runtimes Ready ===" -ForegroundColor Cyan
