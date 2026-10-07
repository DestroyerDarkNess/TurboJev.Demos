param([string]$Version = '0.30.1')
$ErrorActionPreference = 'Stop'
$destination = Join-Path $PSScriptRoot "../.artifacts/rust-native/$Version"
$rids = @('win-x86','win-x64','win-arm64')
if (@($rids | Where-Object { !(Test-Path (Join-Path $destination "runtimes/$_/native/turbojev_capi.dll")) }).Count -eq 0) { Write-Host "Native package cached: $destination"; exit 0 }
New-Item -ItemType Directory -Force -Path $destination | Out-Null
$archive = Join-Path $destination "turbojev.$Version.zip"
# NuGet's public package contains all three Windows architectures and their dependencies.
Invoke-WebRequest -Uri "https://api.nuget.org/v3-flatcontainer/turbojev/$Version/turbojev.$Version.nupkg" -OutFile $archive
# Expand-Archive works on Windows PowerShell 5.1, without requiring the .NET SDK.
Expand-Archive -LiteralPath $archive -DestinationPath $destination -Force
Write-Host "Registry-native runtime ready: $destination"
