$ErrorActionPreference = "Stop"
$version = "0.29.2"
$rids = @("win-x86", "win-x64", "win-arm64")

function Invoke-Checked {
    param([string]$Command, [string[]]$Arguments)
    & $Command @Arguments
    if ($LASTEXITCODE -ne 0) { throw "$Command failed with exit code $LASTEXITCODE" }
}

foreach ($arch in @("ia32", "x64", "arm64")) {
    Invoke-Checked npm.cmd @('view', "@turbojev/node-win32-$arch@$version", 'version')
}
Invoke-Checked npm.cmd @('view', "@turbojev/runtime-llamacpp-wasm@$version", 'version')

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
    if ($LASTEXITCODE -ne 0) { throw "PyPI wheel download failed for $($target.Name)" }
}

Push-Location (Join-Path $PSScriptRoot "TurboJev-csharp-NET")
try {
    foreach ($rid in $rids) {
        Invoke-Checked dotnet @('publish', '-c', 'Release', '-r', $rid, '--self-contained', 'false', '-o', (Join-Path $PSScriptRoot ".artifacts\dotnet\$rid"))
    }
} finally {
    Pop-Location
}

foreach ($project in @('TurboJev-js-native', 'TurboJev-TS-node')) {
    Push-Location (Join-Path $PSScriptRoot $project)
    try {
        Invoke-Checked npm.cmd @('ci', '--no-audit', '--no-fund')
        if ($project -eq 'TurboJev-TS-node') { Invoke-Checked npm.cmd @('run', 'build') }
    } finally { Pop-Location }
}

Push-Location (Join-Path $PSScriptRoot "TurboJev-rust")
try { Invoke-Checked cargo @('check', '--locked') } finally { Pop-Location }

Invoke-Checked py @('-m', 'py_compile', (Join-Path $PSScriptRoot 'TurboJev-Python/main.py'), (Join-Path $PSScriptRoot 'simple/main.py'), (Join-Path $PSScriptRoot 'snake-python/snake.py'), (Join-Path $PSScriptRoot 'snake-python/benchmark.py'))
Write-Host "Package checks/builds completed for Windows x86, x64, and ARM64 where the registry publishes native artifacts."
