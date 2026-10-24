param([string]$Version = '0.34.0')
$ErrorActionPreference = 'Stop'
$destination = Join-Path $PSScriptRoot ".artifacts/rust-native/$Version"
$rids = @('win-x86','win-x64','win-arm64','linux-x86','linux-x64','linux-arm64','osx-x64','osx-arm64')
if (Test-Path (Join-Path $destination '.all-targets-installed')) { Write-Host "Native package cached: $destination"; exit 0 }
New-Item -ItemType Directory -Force -Path $destination | Out-Null
$archive = Join-Path $destination "turbojev.$Version.zip"
# Optional manual Windows installer; the Rust entry point installs its own RID portably.
Invoke-WebRequest -Uri "https://api.nuget.org/v3-flatcontainer/turbojev/$Version/turbojev.$Version.nupkg" -OutFile $archive
# Expand-Archive works on Windows PowerShell 5.1, without requiring the .NET SDK.
Expand-Archive -LiteralPath $archive -DestinationPath $destination -Force
Set-Content (Join-Path $destination '.all-targets-installed') $Version
Write-Host "Registry-native runtime ready: $destination"
