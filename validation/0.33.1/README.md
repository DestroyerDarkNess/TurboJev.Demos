# TurboJev 0.33.1 demo validation

Checked on Windows x64 on 2026-10-11 using published packages. All active
demos, registry dependencies, lockfiles, CDN URLs and installation scripts
now select 0.33.1. Historical validation records were preserved.

| Check | Result |
| --- | --- |
| `build-all.ps1` | Passed |
| C# publish and native DLL architecture | Windows x86, x64 and ARM64 passed |
| Rust `cargo check --locked` | Windows x86, x64 and ARM64 passed |
| PyPI wheel downloads | Windows x86, x64 and ARM64 available |
| JavaScript and TypeScript installation | npm packages and all three native variants locked to 0.33.1 |
| TypeScript build | Passed |
| Python sources and CLI entry points | 21 files compiled; 15 CLI import checks passed |
| Snake integrity regressions | 8 tests passed; these test host behavior, not model intelligence |
| Browser dependencies | Six CDN resources, including WASM, returned HTTP 200 |
| Real inference | Python simple and Node ticket executed with QJev3.5 0.8B on CPU |

[checks.json](checks.json) records the coverage. The other JSON files contain
the dependency checks and actual model responses. Model answers were not
replaced with expected values; smoke execution is not an accuracy benchmark.

ARM64 was cross-compiled and its package architecture checked, not executed
on ARM64 hardware. Browser inference and the remaining model-backed demos,
including receipt OCR, were not rerun for this dependency update. Earlier
measurements remain under their original release folders.
