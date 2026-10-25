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
    Write-Host "`n[1/2] Staging Tesseract OCR..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Force -Path $TempDownloads | Out-Null
    New-Item -ItemType Directory -Force -Path $TesseractDir | Out-Null

    $pfTess = Join-Path $env:ProgramFiles "Tesseract-OCR"
    if (Test-Path (Join-Path $pfTess "tesseract.exe")) {
        Write-Host "Found installed Tesseract OCR in Program Files, copying to vendor..." -ForegroundColor Gray
        Copy-Item "$pfTess\*" $TesseractDir -Recurse -Force
    } elseif (Get-Command choco -ErrorAction SilentlyContinue) {
        Write-Host "Installing Tesseract via Chocolatey..." -ForegroundColor Gray
        try {
            choco install tesseract --no-progress -y
            if (Test-Path (Join-Path $pfTess "tesseract.exe")) {
                Copy-Item "$pfTess\*" $TesseractDir -Recurse -Force
            }
        } catch {
            Write-Host "Chocolatey install failed: $_" -ForegroundColor Yellow
        }
    }

    # Verify English traineddata
    if (-not (Test-Path $tessData)) {
        try {
            Write-Host "Downloading English traineddata from GitHub..." -ForegroundColor Gray
            $engUrl = "https://github.com/tesseract-ocr/tessdata_fast/raw/main/eng.traineddata"
            New-Item -ItemType Directory -Force -Path (Join-Path $TesseractDir "tessdata") | Out-Null
            Invoke-WebRequest -Uri $engUrl -OutFile $tessData
        } catch {
            Write-Host "Could not download traineddata: $_" -ForegroundColor Yellow
        }
    }

    if (Test-Path $tessExe) {
        Write-Host "[PASS] Tesseract OCR staged successfully." -ForegroundColor Green
    } else {
        Write-Host "[WARN] Tesseract binary not staged. OCR tests will be skipped." -ForegroundColor Yellow
    }
} else {
    Write-Host "[1/2] Tesseract OCR already staged." -ForegroundColor Green
}

# 2. LibreOffice Standalone Headless Runtime
$loSoffice = Join-Path $LibreOfficeDir "program\soffice.exe"

if ($Force -or -not (Test-Path $loSoffice)) {
    Write-Host "`n[2/2] Staging LibreOffice Headless Runtime..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Force -Path $TempDownloads | Out-Null
    
    $pfLO = Join-Path $env:ProgramFiles "LibreOffice"
    if (Test-Path (Join-Path $pfLO "program\soffice.exe")) {
        Write-Host "Found installed LibreOffice in Program Files, copying to vendor..." -ForegroundColor Gray
        New-Item -ItemType Directory -Force -Path $LibreOfficeDir | Out-Null
        Copy-Item "$pfLO\program" $LibreOfficeDir -Recurse -Force
        Copy-Item "$pfLO\share" $LibreOfficeDir -Recurse -Force
    } elseif (Get-Command choco -ErrorAction SilentlyContinue) {
        Write-Host "Installing LibreOffice via Chocolatey..." -ForegroundColor Gray
        try {
            choco install libreoffice-fresh --no-progress -y
            if (Test-Path (Join-Path $pfLO "program\soffice.exe")) {
                New-Item -ItemType Directory -Force -Path $LibreOfficeDir | Out-Null
                Copy-Item "$pfLO\program" $LibreOfficeDir -Recurse -Force
                Copy-Item "$pfLO\share" $LibreOfficeDir -Recurse -Force
            }
        } catch {
            Write-Host "Chocolatey LibreOffice install failed: $_" -ForegroundColor Yellow
        }
    } else {
        $loMsiUrl = "https://download.documentfoundation.org/libreoffice/stable/26.8.1/win/x86_64/LibreOffice_26.8.1_Win_x86-64.msi"
        $loMsiPath = Join-Path $TempDownloads "LibreOffice_Win_x86-64.msi"
        $extractDir = Join-Path $ProjectRoot "vendor_extracted_lo"

        try {
            Write-Host "Downloading LibreOffice MSI..." -ForegroundColor Gray
            Invoke-WebRequest -Uri $loMsiUrl -OutFile $loMsiPath
            Write-Host "Extracting administrative MSI..." -ForegroundColor Gray
            Start-Process msiexec.exe -ArgumentList "/a `"$loMsiPath`" /qb TARGETDIR=`"$extractDir`"" -Wait
            New-Item -ItemType Directory -Force -Path $LibreOfficeDir | Out-Null
            Move-Item (Join-Path $extractDir "program") $LibreOfficeDir -Force
            Move-Item (Join-Path $extractDir "share") $LibreOfficeDir -Force
        } catch {
            Write-Host "LibreOffice download/extraction failed: $_" -ForegroundColor Yellow
        } finally {
            Remove-Item -Recurse -Force $extractDir -ErrorAction SilentlyContinue
            Remove-Item -Recurse -Force $TempDownloads -ErrorAction SilentlyContinue
        }
    }

    # Prune non-English dictionaries to save 450 MB if present
    $extDir = Join-Path $LibreOfficeDir "share\extensions"
    if (Test-Path $extDir) {
        Get-ChildItem -Path $extDir -Directory -Filter "dict-*" | 
            Where-Object { $_.Name -ne "dict-en" } | 
            Remove-Item -Recurse -Force
    }

    if (Test-Path $loSoffice) {
        Write-Host "[PASS] LibreOffice Headless Runtime staged successfully." -ForegroundColor Green
    } else {
        Write-Host "[WARN] LibreOffice not staged. Legacy Office tests will be skipped." -ForegroundColor Yellow
    }
} else {
    Write-Host "[2/2] LibreOffice Standalone Runtime already staged." -ForegroundColor Green
}

Write-Host "`n=== Vendor Runtimes Ready ===" -ForegroundColor Cyan
