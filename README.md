# TurboJev demos

Small, idiomatic examples built against the latest published TurboJev packages. Each example evaluates one request containing a `choice`, a boolean (`noul`), and an ordered `score`.

## Model

The default model is [Qwen3 0.6B, Q4_K_M](https://huggingface.co/bartowski/Qwen_Qwen3-0.6B-GGUF), about 0.48 GB. The Node, Python, and .NET demos download and cache it on first run. Set `TURBOJEV_MODEL` to use a local GGUF instead.

## Demos

| Project | Install from | Run |
|---|---|---|
| JavaScript (Node) | npm: `@turbojev/node` | `cd TurboJev-js-native && npm install && npm start` |
| TypeScript (Node) | npm: `@turbojev/node` | `cd TurboJev-TS-node && npm install && npm start` |
| Python | PyPI: `turbojev` | `cd TurboJev-Python && py -m pip install -r requirements.txt && py main.py` |
| C# / .NET | NuGet: `TurboJev` | `cd TurboJev-csharp-NET && dotnet run -c Release` |
| Rust | crates.io: `turbojev` | `cd TurboJev-rust && cargo run --release` |

On Windows, run `.\build-all.ps1` to check the three npm native packages and PyPI wheels, publish .NET builds for x86/x64/ARM64, and compile the TypeScript and Rust examples. It requires Node.js, Python, Rust, and .NET 8.

The npm, PyPI, and NuGet packages contain native artifacts for Windows x86, x64, and ARM64. Run each project using a matching Node/Python/.NET architecture to select its corresponding native binary. Cross-architecture execution requires a matching host or emulator.

The Rust crates.io package is the portable decision core. It does not bundle a GGUF inference runtime, so the Rust project prints the same typed request shape but does not score it or run Qwen. A package-only Rust inference demo needs a published TurboJev runtime crate with native runtime assets.

All package versions are kept at the latest release when these demos are updated. They are declared in each project's manifest; no project links to this repository's source tree or builds TurboJev locally.
