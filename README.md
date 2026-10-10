# TurboJev demos

Standalone projects using the latest published TurboJev release, **0.33.0**.
Each project owns its code and input data. Model downloads are cached, but demos
do not import another project's implementation or build a local TurboJev SDK.

| Technology                   | Projects                                                                                       | Package source                           |
| ---------------------------- | ---------------------------------------------------------------------------------------------- | ---------------------------------------- |
| [Python](python/README.md)   | Twelve workflow/thinking/probability ports, Snake, simple decisions, typed fields and receipts | PyPI                                     |
| [Node](node/README.md)       | JavaScript and TypeScript                                                                      | npm                                      |
| [.NET](dotnet/README.md)     | C#                                                                                             | NuGet                                    |
| [Webpage](webpage/README.md) | Vanilla HTML/JavaScript, text and typed/media examples                                         | Public CDNs                              |
| [Rust](rust/README.md)       | Typed decisions and structured fields                                                          | crates.io and public NuGet native assets |

## Run

```sh
cd python/category-tree
python -m pip install -r requirements.txt
python main.py
```

Text defaults to QJev3.5 0.8B v19c GGUF Q8_0 (~0.81 GB). Downloads have a progress bar, speed and ETA.
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

## Default decision model

Text demos download [QJev3.5 0.8B v19c](https://huggingface.co/ZY-Lee4/QJev3.5-0.8B-GGUF),
the standalone `qjev35-v19c-q8_0.gguf` file, pinned to revision
`008c7c7a5c35007b8ba6b06afba50f882f000667`. Native downloads verify
811,843,104 bytes and SHA-256
`7a5a50953df2fb866a2f39bc4ac8906084cac4e3a5fa8f04adc519058ceedf87`.
No separate LoRA or base-model download is needed.

QJev is specialized in finite choices, boolean gates and ordered scores. It
is not an instruction model for free-form extraction, arithmetic or planning.
For those existing examples, explicitly supply a suitable model with `--model`
or `TURBOJEV_MODEL`; browser typed generation accepts its URL. Image examples
keep their multimodal GGUF and projector. QJev does not replace an ONNX model.

The demos retain TurboJev's published prompt and scoring path. Loading these
weights does not reproduce QJev's upstream prompt, reversal averaging or
calibration; probabilities remain conditional scores. Model-selected answers
and errors stay visible.

Alternative repositories are commented in each text model configuration:

- Jev-Style Qwen3.5 2B Decision v2: requires its letter-scoring prompt.
- Jev-Style 0.8B Decision v3: requires its per-option verdict scorer.
- Jev-Style 2B Decision v3: requires block attention and verdict scoring.

These specialized alternatives are not interchangeable with general chat
models. The v3 scoring requirements are not implemented by simply changing a
GGUF path. Use the comments as integration references, not a compatibility claim.

[QJev default-model checks](validation/0.33.0/qjev-default.json) record the
actual registry-package responses, model hash and observed mistakes.
