# TurboJev demos

Small, idiomatic examples built against the latest published TurboJev packages,
currently **0.31.0**. The introductory examples show `choice`, a boolean (`noul`),
and an ordered `score`. Snake demonstrates repeated directional decisions.

## Model

The default model is [Qwen3 0.6B, Q4_K_M](https://huggingface.co/bartowski/Qwen_Qwen3-0.6B-GGUF), about 0.48 GB. The Node, Python, and .NET demos download and cache it on first run. Set `TURBOJEV_MODEL` to use a local GGUF instead.

First-time downloads show a progress bar and are cached under the user's home directory. Later runs reuse the cached file.

## Demos

| Project | Install from | Run |
|---|---|---|
| [JavaScript (Node)](TurboJev-js-native/README.md) | npm: `@turbojev/node` | `cd TurboJev-js-native && npm install && npm start -- fields` |
| JavaScript (browser) | jsDelivr (`@turbojev/web`, `@turbojev/wasm`, `@turbojev/runtime-llamacpp-wasm`, `@wllama/wllama`) + esm.sh (Transformers.js runtime) | `cd TurboJev-js-browser && py -m http.server 4174`, then open `http://localhost:4174`; choose Transformers.js or llama.cpp in Runtime |
| [TypeScript (Node)](TurboJev-TS-node/README.md) | npm: `@turbojev/node` | `cd TurboJev-TS-node && npm install && npm start -- fields` |
| [Python](TurboJev-Python/README.md) | PyPI: `turbojev` | `cd TurboJev-Python && py -m pip install -r requirements.txt && py main.py fields` |
| Python, original Jev example | PyPI: `turbojev` | `cd simple && py -m pip install -r requirements.txt && py main.py` |
| Python fair die | PyPI: `turbojev` | `cd fair-die-python && py -m pip install -r requirements.txt && py main.py` |
| Python receipt | PyPI: `turbojev` | `cd receipt-python && py -m pip install -r requirements.txt && py main.py` |
| Python US receipt | PyPI: `turbojev` | `cd receipt-us-python && py -m pip install -r requirements.txt && py main.py --image receipt.jpg` |
| Python Snake | PyPI: `turbojev` | `cd snake-python && py -m pip install -r requirements.txt && py snake.py` |
| [C# / .NET](TurboJev-csharp-NET/README.md): ticket, typed fields, fair die, image receipts | NuGet: `TurboJev` | `cd TurboJev-csharp-NET && dotnet run -c Release -- ticket` |
| [Rust](TurboJev-rust/README.md) | crates.io: `turbojev` + public NuGet native runtime | `cd TurboJev-rust && cargo run --release -- fields` |

On Windows, run `.\build-all.ps1` to check the three npm native packages and PyPI wheels, publish .NET builds for x86/x64/ARM64, and compile the TypeScript and Rust examples. It requires Node.js, Python, Rust, and .NET 8.

The Rust checks install the selected toolchain's three standard-library targets.
Set `TURBOJEV_DEMO_BUILD_DIR` to a directory on a disk with free space to relocate
Rust build artifacts when running that script.

The npm, PyPI, and NuGet packages contain native artifacts for Windows x86, x64, and ARM64. Run each project using a matching Node/Python/.NET architecture to select its corresponding native binary. Cross-architecture execution requires a matching host or emulator. The Python Snake source is OS-independent, but PyPI 0.31.0 currently publishes Windows x86, x64, and ARM64 wheels; Linux and macOS need matching TurboJev wheels before the demo can run there.

The browser example needs no package installation or build step. It loads the published TurboJev browser package plus the selected model runtime from public CDNs, downloads ONNX or GGUF model files from Hugging Face, and runs inference in a browser worker. Serve it over localhost or HTTPS; browsers block module workers from `file://` pages. Its new `typed.html` page covers typed fields, fair die and both image receipt definitions. Native Node, TypeScript, Python, .NET and Rust examples all execute the published GGUF runtime.

The native inference demos set `orderRobustness` to `none` for one evaluation pass. Set it to `balanced` for canonical option layouts with probability averaging, or `cyclic` for legacy rotation/logit averaging. These policies apply to unordered `choice` questions and preserve ordered `score` scales. Balanced takes K evaluations for an even number of options, 2K for an odd number, and supports at most 32 options. It costs additional inference and cannot guarantee correct reasoning. New `generate` enum fields have a separate per-field `permutations` budget, demonstrated by fair die.

The Rust example installs its contract crate from crates.io and dynamically loads
the stable C ABI from the public NuGet package. Its Windows installer downloads
all three native architectures; the Rust process picks its matching library.
This avoids building a local engine or linking an unpublished shim. Rust 1.97.1
is selected by the demo's toolchain file. Other OS targets require matching public
native assets; none are fabricated or built from workspace SDK source.

All package versions are kept at the latest release when these demos are updated. They are declared in each project's manifest; no project links to this repository's source tree or builds TurboJev locally.

Every Python demo folder contains its own implementation and required input data.
Copy the desired folder, install its `requirements.txt`, and run it independently;
Python demos do not import parent utilities or execute other demo projects.

The root `NuGet.Config` uses only nuget.org and an isolated package cache so .NET demos cannot reuse a package installed by a local publishing test.

The new TypeLLM example ports use `generate` for scalar JSON fields, probabilities and dependencies. See each folder's README for commands, model selection, CPU/GPU selection, attribution and measured output. Receipt demos run a real image through a matching GGUF/projector; they never put expected labels in a model request. The US receipt demo accepts your own photo because the reference image's redistribution license is not established.

The Node, TypeScript, Python, C# and Rust entry points accept `ticket`, `fields`,
`fair-die`, `receipt` and `receipt-us`. The receipt modes default to Qwen3.5 2B
Q4_K_M plus its F16 projector, with progress on first download. `--fields` selects
an explicit subset with dependency closure. Full receipt extraction can take
minutes and can contain OCR/arithmetic mistakes; actual answers remain in reports.
The browser's typed page offers the same new examples through editable JSON and
a photo picker, with CPU/GPU and GGUF/ONNX controls where supported.

## Source formatting

Run these commands from this repository:

```powershell
npx --yes prettier@3.6.2 --write "**/*.{html,css,js,mjs,ts,json}"
ruff format .
dotnet format whitespace TurboJev-csharp-NET/TurboJev-csharp-NET.csproj --no-restore
rustfmt --edition 2021 TurboJev-rust/src/main.rs TurboJev-rust/src/models.rs TurboJev-rust/src/native.rs
```

Use Prettier `--check` and `ruff format --check` to verify formatting. The local
configuration excludes dependencies, generated output and saved benchmark
reports. JavaScript, TypeScript, HTML and CSS use two-space indentation; Python,
Rust and C# use four spaces.
