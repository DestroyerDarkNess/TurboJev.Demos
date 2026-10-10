# TurboJev demos

Standalone projects using the latest published TurboJev release, **0.33.0**.
Each project owns its code and input data. Model downloads are cached, but demos
do not import another project's implementation or build a local TurboJev SDK.

| Technology | Projects | Package source |
| --- | --- | --- |
| [Python](python/README.md) | Twelve workflow/thinking/probability ports, Snake, simple decisions, typed fields and receipts | PyPI |
| [Node](node/README.md) | JavaScript and TypeScript | npm |
| [.NET](dotnet/README.md) | C# | NuGet |
| [Webpage](webpage/README.md) | Vanilla HTML/JavaScript, text and typed/media examples | Public CDNs |
| [Rust](rust/README.md) | Typed decisions and structured fields | crates.io and public NuGet native assets |

## Run

```sh
cd python/incident
python -m pip install -r requirements.txt
python main.py
```

Text defaults to Qwen3 0.6B GGUF. Downloads have a progress bar, speed and ETA.
CPU is the default; explicit GPU requests never silently fall back. Use
`--model PATH` or `TURBOJEV_MODEL` for a compatible checkpoint. Each folder has
its own README and install/run commands.

Native packages currently contain Windows x86, x64 and ARM64 assets. Run with a
matching Node/Python/.NET architecture. Rust code uses the published C ABI for
real inference. Browser WASM is architecture independent. Linux/macOS execution
requires compatible published native assets; no local SDK build is substituted.

## Build checks and evidence

On Windows, `.\build-all.ps1` checks the registry assets, publishes the C# demo
for three architectures, builds Node/TypeScript, checks Rust targets and compiles
all Python entry points. Requires Node, Python, Rust and .NET 8. Cross-compilation
is not execution on another architecture.

[Published-package evidence](validation/0.33.0/README.md) includes model hashes,
responses and timings. New Python ports have separate records under
[python-typellm](validation/0.33.0/python-typellm/README.md). Small models may
misclassify or reason incorrectly. No host policy substitutes an expected answer.

The TypeLLM ports include their source-page attribution and upstream license.
The receipt photograph has separate CORD attribution in its demo README.
