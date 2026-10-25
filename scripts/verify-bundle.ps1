# Verification script for Local Markdown bundled release payload
[CmdletBinding()]
param(
    [string]$DistPath = "dist\LocalMarkdown"
)

$ErrorActionPreference = "Stop"
Write-Host "=== Verifying Local Markdown Release Bundle ===" -ForegroundColor Cyan

$dist = Resolve-Path $DistPath
$exe = Join-Path $dist "LocalMarkdown.exe"
if (-not (Test-Path $exe)) {
    throw "Executable not found: $exe"
}
Write-Host "[PASS] Found main executable: $exe" -ForegroundColor Green

# Locate vendor directory
$vendor = Join-Path $dist "vendor"
if (-not (Test-Path $vendor)) {
    $vendor = Join-Path $dist "_internal\vendor"
}

$tessExe = Join-Path $vendor "tesseract\tesseract.exe"
$tessData = Join-Path $vendor "tesseract\tessdata\eng.traineddata"
$sofficeExe = Join-Path $vendor "libreoffice\program\soffice.exe"

if (-not (Test-Path $tessExe) -or -not (Test-Path $tessData)) {
    throw "Bundled Tesseract OCR runtime missing!"
}
Write-Host "[PASS] Verified bundled Tesseract OCR runtime and English trained data." -ForegroundColor Green

if (-not (Test-Path $sofficeExe)) {
    throw "Bundled LibreOffice runtime missing!"
}
Write-Host "[PASS] Verified bundled LibreOffice runtime for legacy Office import." -ForegroundColor Green

Write-Host "=== Bundle Verification Complete ===" -ForegroundColor Cyan
