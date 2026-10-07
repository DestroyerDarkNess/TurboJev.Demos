# TurboJev demos

Small, idiomatic examples built against the latest published TurboJev packages,
currently **0.30.1**. The introductory examples show `choice`, a boolean (`noul`),
and an ordered `score`. Snake demonstrates repeated directional decisions.

## Model

The default model is [Qwen3 0.6B, Q4_K_M](https://huggingface.co/bartowski/Qwen_Qwen3-0.6B-GGUF), about 0.48 GB. The Node, Python, and .NET demos download and cache it on first run. Set `TURBOJEV_MODEL` to use a local GGUF instead.

First-time downloads show a progress bar and are cached under the user's home directory. Later runs reuse the cached file.

## Demos

| Project | Install from | Run |
|---|---|---|
| JavaScript (Node) | npm: `@turbojev/node` | `cd TurboJev-js-native && npm install && npm start` |
| JavaScript (browser) | jsDelivr (`@turbojev/web`, `@turbojev/wasm`, `@turbojev/runtime-llamacpp-wasm`, `@wllama/wllama`) + esm.sh (Transformers.js runtime) | `cd TurboJev-js-browser && py -m http.server 4174`, then open `http://localhost:4174`; choose Transformers.js or llama.cpp in Runtime |
| TypeScript (Node) | npm: `@turbojev/node` | `cd TurboJev-TS-node && npm install && npm start` |
| Python | PyPI: `turbojev` | `cd TurboJev-Python && py -m pip install -r requirements.txt && py main.py` |
| Python, original Jev example | PyPI: `turbojev` | `cd simple && py -m pip install -r requirements.txt && py main.py` |
| Python fair die | PyPI: `turbojev` | `cd fair-die-python && py -m pip install -r requirements.txt && py main.py` |
| Python receipt | PyPI: `turbojev` | `cd receipt-python && py -m pip install -r requirements.txt && py main.py` |
| Python US receipt | PyPI: `turbojev` | `cd receipt-us-python && py -m pip install -r requirements.txt && py main.py --image receipt.jpg` |
| Python Snake | PyPI: `turbojev` | `cd snake-python && py -m pip install -r requirements.txt && py snake.py` |
| [C# / .NET](TurboJev-csharp-NET/README.md): ticket, typed fields, fair die, image receipts | NuGet: `TurboJev` | `cd TurboJev-csharp-NET && dotnet run -c Release -- ticket` |
| Rust | crates.io: `turbojev` | `cd TurboJev-rust && cargo run --release` |

On Windows, run `.\build-all.ps1` to check the three npm native packages and PyPI wheels, publish .NET builds for x86/x64/ARM64, and compile the TypeScript and Rust examples. It requires Node.js, Python, Rust, and .NET 8.

The npm, PyPI, and NuGet packages contain native artifacts for Windows x86, x64, and ARM64. Run each project using a matching Node/Python/.NET architecture to select its corresponding native binary. Cross-architecture execution requires a matching host or emulator. The Python Snake source is OS-independent, but PyPI 0.30.1 currently publishes Windows x86, x64, and ARM64 wheels; Linux and macOS need matching TurboJev wheels before the demo can run there.

The browser example needs no package installation or build step. It loads the latest published TurboJev browser package plus the selected model runtime from public CDNs, downloads ONNX or GGUF model files from Hugging Face, and runs inference in a browser worker. Serve it over localhost or HTTPS; browsers block module workers from `file://` pages. The native Node, TypeScript, Python, and .NET demos use llama.cpp; the Rust example demonstrates the portable contract without model inference.

The Node, TypeScript, Python, and .NET inference demos set `orderRobustness` to `none` for one evaluation pass. Set it to `cyclic` in the engine options to average candidate-order rotations; this can improve order consistency, but requires additional model evaluations and is slower. The Rust demo uses only the portable core crate and does not load a model, so this runtime option does not apply.

The Rust example installs only the portable core and prints the typed request;
it does not score it or run Qwen. The separate `turbojev-runtime-llamacpp` crate
is published on crates.io, but its `ffi` feature still requires linking a
matching native shim. This introductory demo does not build a local engine.

All package versions are kept at the latest release when these demos are updated. They are declared in each project's manifest; no project links to this repository's source tree or builds TurboJev locally.

The root `NuGet.Config` uses only nuget.org and an isolated package cache so .NET demos cannot reuse a package installed by a local publishing test.

The new TypeLLM example ports use `generate` for scalar JSON fields, probabilities and dependencies. See each folder's README for commands, model selection, CPU/GPU selection, attribution and measured output. Receipt demos run a real image through a matching GGUF/projector; they never put expected labels in a model request. The US receipt demo accepts your own photo because the reference image's redistribution license is not established.
