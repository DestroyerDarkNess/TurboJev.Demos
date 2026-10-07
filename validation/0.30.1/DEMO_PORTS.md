# Additional-language example validation

Windows x64, published TurboJev 0.30.1. These are functional integration checks,
with overlapping compiler/machine work; timings are not isolated comparisons.
Existing C# and full Python receipt measurements remain separate and unchanged.

| Host | Real execution evidence |
|---|---|
| Node.js | [Scalar/null/dependency/condition fields](node-demo-fields.json), [three die budgets](node-fair-die.json), [CORD total subset](node-receipt.json) |
| TypeScript | Strict build, [typed fields](typescript-fields.json), [US currency subset](typescript-receipt-us.json) |
| Python | [Typed fields](python-fields.json), [receipt boolean subset](python-receipt.json); main entry point dispatches other modes to the existing full Python examples |
| Rust | [Typed fields](rust-fields.json), [three die budgets](rust-fair-die.json), [CORD total subset](rust-receipt.json), actual public NuGet C ABI loaded from the registry cache |
| Browser | [Real scalar/null/dependency/condition inference](browser-fields.json), public CDN worker/WASM/runtime, CPU llama.cpp, cached Qwen3 0.6B Q4_K_M served over loopback HTTP |

Every field run returned integer 7, decimal 324.5, boolean true with its actual
probability wrapper, actual null for the absent reference, a model-written dependent
reminder and a skipped `large_account_note`. Wording and probabilities differ
between runtimes and remain in the raw reports. No host logic manufactured answers.

Node and Rust returned CORD total 174600; Python returned the cash boolean true.
TypeScript completed its US receipt request but the model returned JPY instead of
USD. This wrong answer remains in its report. Receipt checks used explicit small
subsets, not full 14/16-field runs for every language. Expected labels were compared
only after inference. Browser image presets expose the same 14/16 schemas, matching
projector controls and a photo picker, but browser image inference was not measured
in this validation. Native image success is not relabeled as browser evidence.

Rust's final source passed locked Cargo checks for i686, x86_64 and aarch64 Windows
MSVC targets. Only Windows x64 inference was executed. The Windows downloader uses
system TLS, avoiding ring's ARM64 Clang requirement. Runtime dependencies are
packaged together in the public native package; no workspace SDK or model-decision
implementation was compiled locally. The Rust demo itself and its crates.io
dependencies were compiled normally.

The browser field run took about 102.6 seconds for five returned fields under
machine contention, including generated strings; it is not a single-choice latency
benchmark. Model load/warmup is outside that measurement. Actual responses and
timings are recorded, without claims of universal correctness or performance.

Default weights were already cached. Fresh multi-GB model downloads and the new
Rust NuGet installer were not exercised end-to-end here. The installer uses public
nuget.org and Windows PowerShell's archive module; it does not need a .NET SDK or
registry token. Neither Linux/macOS native execution nor physical x86/ARM64 execution
is claimed. Receipt attribution and TypeLLM's retained license are linked in each
demo README.
