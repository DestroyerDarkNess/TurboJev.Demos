# TurboJev 0.34.0 demo validation

The demo projects target the published 0.34.0 API. Registry checks confirmed
the npm packages, PyPI wheels, crates.io packages, and NuGet package and payload.
The NuGet package-manager build and local compatibility matrix also passed.

## Build and package checks

| Check | Result |
| --- | --- |
| npm | All 13 packages are published; tarball integrity and all eight native architectures verified. |
| PyPI | All eight platform wheels are published and their SHA-256 hashes match the build outputs. |
| crates.io | All 27 workspace packages required by the public Rust demo are present. |
| Python demos | All source files pass `py_compile`; the `simple` demo installed PyPI 0.34.0 and loaded a real GGUF. |
| JavaScript demo | `npm ci` succeeded; the published npm package loaded the GGUF and completed `ticket`. |
| TypeScript demo | `npm ci` and `tsc` succeeded; the published npm package loaded the GGUF and completed `ticket`. |
| Rust demo | `cargo check --locked` passed for Windows x86, x64 and ARM64 targets using crates.io 0.34.0. |
| C# demo | Public NuGet restore and `dotnet publish` passed for all seven supported RIDs. The Windows x64 real-model smoke passed using the public package. |
| Browser WASM | Published-runtime contract and structured-generation tests passed during npm publication. |

The real-model smoke runs used the same cached `SmolLM2-135M-Instruct-Q2_K.gguf`
on Windows x64 with CPU selection. Python evaluation took 1.671 s, JavaScript
3.414 s, TypeScript 2.942 s, and C# 3.719 s. These are separate runs, not a
benchmark comparison; they verify model loading and typed responses, not model
accuracy. Linux ARM64 Python and Node packages were also executed under QEMU in
the native-release validation. macOS artifacts passed cross-build and linker
checks but were not executed on a Mac. Windows x86 and ARM64 were package-checked
but not run on matching hardware.

The complete `build-all.ps1` run passed after NuGet 0.34.0 became available.
`dotnet publish` restored the public package for each RID; the real-model smoke
also loaded it from the public package and evaluated the cached GGUF.
