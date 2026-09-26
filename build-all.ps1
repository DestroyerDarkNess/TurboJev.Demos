$ErrorActionPreference = "Stop"
$version = "0.29.1"
$rids = @("win-x86", "win-x64", "win-arm64")

foreach ($arch in @("ia32", "x64", "arm64")) {
    npm view "@turbojev/node-win32-$arch@$version" version | Out-Null
}
npm view "@turbojev/runtime-llamacpp-wasm@$version" version | Out-Null

$wheelRoot = Join-Path $PSScriptRoot ".artifacts\python"
foreach ($target in @(
    @{ Platform = "win32"; Name = "x86" },
    @{ Platform = "win_amd64"; Name = "x64" },
    @{ Platform = "win_arm64"; Name = "arm64" }
)) {
    $destination = Join-Path $wheelRoot $target.Name
    New-Item -ItemType Directory -Force -Path $destination | Out-Null
    py -m pip download --index-url https://pypi.org/simple --no-cache-dir --only-binary=:all: --no-deps --dest $destination `
        --platform $target.Platform --python-version 39 --implementation cp --abi cp39 `
        "turbojev==$version"
}

Push-Location (Join-Path $PSScriptRoot "TurboJev-csharp-NET")
try {
    foreach ($rid in $rids) {
        dotnet publish -c Release -r $rid --self-contained false -o (Join-Path $PSScriptRoot ".artifacts\dotnet\$rid")
    }
} finally {
    Pop-Location
}

Push-Location (Join-Path $PSScriptRoot "TurboJev-TS-node")
try { npm ci; npm run build } finally { Pop-Location }

Push-Location (Join-Path $PSScriptRoot "TurboJev-rust")
try { cargo check --locked } finally { Pop-Location }

py -m py_compile (Join-Path $PSScriptRoot "TurboJev-Python\main.py")
Write-Host "Package checks/builds completed for Windows x86, x64, and ARM64 where the registry publishes native artifacts."
