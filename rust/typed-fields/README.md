# TurboJev — Rust

Real model-backed examples using the **turbojev 0.33.0 contract from crates.io** and the **0.33.0 native C ABI from the public NuGet package**. No local TurboJev or llama.cpp source is compiled. The small `native.rs` owner invokes that stable ABI on its creating thread, frees returned strings and closes the engine; all inference and decision logic stays in the published library.

Rust 1.97.1 is selected by `rust-toolchain.toml`. On Windows, the first run reuses the demo repository's isolated nuget.org cache, or `setup-native.ps1` downloads/extracts the public package with all three Windows architectures. No .NET SDK or NuGet token is required by the installer. The Rust process selects x86/x64/ARM64 automatically.

```powershell
cargo run --release -- ticket
cargo run --release -- fields
cargo run --release -- fair-die --device gpu
cargo run --release -- receipt --device gpu --fields first_item,total
cargo run --release -- receipt-us --image C:/photos/receipt.jpg --device gpu
cargo run --release -- --help
```

`ticket` uses `evaluate`. The other modes use `generate`: scalar/null fields, boolean probabilities, dependencies/conditions, enum permutation budgets and full 14/16-field image schemas. Receipt `--fields` selects an explicit subset and includes dependencies. Expected labels are compared only after inference; no host arithmetic substitutes for model-generated calculations. All answers, mistakes, model/library hashes, device and timings are retained in `result-<example>.json` (`--output PATH` overrides it).

CPU is the default; GPU is explicitly requested without fallback. Text defaults to QJev3.5 0.8B v19c Q8_0 (~0.81 GB). Images use Qwen3.5 2B Q4_K_M and matching F16 projector (~1.95 GB together). GGUF downloads show progress, speed and ETA and reuse `~/.cache/turbojev`. Defaults check byte counts and headers; the text model also checks SHA-256. Interrupted downloads restart. `--model PATH` and `--mmproj PATH` select a compatible custom vision pair; text also accepts `TURBOJEV_MODEL`.

`fair-die` compares actual distributions for 1/auto/8 orderings; `--all-permutations` opts into 720. Averaging is additional inference, not guaranteed correctness. `--max-tokens` bounds each generated field. Each image field repeats processing and can take minutes. The CORD photo is bundled; `receipt-us` requires your own photo. `--reference-labels` applies only to the exact original reference image. A 32-bit process may need a smaller vision pair.

```powershell
cargo check --locked --target i686-pc-windows-msvc
cargo check --locked --target x86_64-pc-windows-msvc
cargo check --locked --target aarch64-pc-windows-msvc
# Choose a disk with free space for build artifacts if needed:
cargo run --release --target-dir C:/temp/turbojev-demo-build -- fields
```

Compilation for an architecture is not execution on it; use a matching host/emulator. Published 0.33.0 native assets cover Windows only. `--native-dir` accepts the matching library directory from a public package when available for another OS; missing runtime support is an error, not a fabricated answer. Request and receipt data are contained in this folder; it can be copied independently.

Question definitions are adapted from TypeLLM (Apache-2.0; [license](TYPELLM-LICENSE)). The CORD photograph has its separate CC BY 4.0 attribution in the [receipt README](../../python/receipt/README.md).

## Structured SDK examples (TurboJev 0.33.0)

```sh
cargo run -- structured
cargo run -- hierarchical
cargo run -- discover-categories
cargo run -- dice
cargo run -- limits
```

All use the registry package, never a workspace build. Dice samples from the
model distribution with seed 42; fair-die measures the distribution with greedy
decoding and compares it with 1/6 per face. Auto costs six layouts, and all costs 720. Numeric limits constrain generated digits, including fractional digits.

Bundled image attribution: [data/receipt/ATTRIBUTION.md](data/receipt/ATTRIBUTION.md).

QJev is specialized in bounded decisions. For open text/number extraction,
arrays or model reasoning, select a general instruction GGUF with `--model PATH`
(or `TURBOJEV_MODEL`). The example schemas stay unchanged; the host never
fabricates an answer. QJev is not expected to reproduce those generation demos.
Its upstream accuracy/calibration figures use a different prompt/scoring path
and do not describe these TurboJev runs. Alternative model URLs and integration
requirements are commented next to the model configuration in each entry point.
