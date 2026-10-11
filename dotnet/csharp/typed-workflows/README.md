# TurboJev â€” C# / .NET

Five examples using **TurboJev 0.33.1 from nuget.org**, with no project reference or local engine build. This application targets .NET 8; use the .NET 8 SDK and runtime or a supported later SDK with that runtime installed. The TurboJev package also supports .NET Framework 4.8 and .NET Core through its `net48` and `netstandard2.0` assemblies. Run the commands from this directory.

```powershell
dotnet restore
dotnet run -c Release -- ticket
dotnet run -c Release -- fields
dotnet run -c Release -- fair-die
dotnet run -c Release -- receipt
dotnet run -c Release -- receipt-us --image C:/photos/restaurant-receipt.jpg
```

## Examples

| Command            | What the model does                                                                                                                        |
| ------------------ | ------------------------------------------------------------------------------------------------------------------------------------------ |
| `ticket` (default) | `evaluate`: choose a support team, score urgency, decide whether a refund is requested                                                     |
| `fields`           | `generate`: extract integer, decimal, boolean probabilities and nullable text; run a dependent reminder and skip a conditional field       |
| `fair-die`         | Score six faces with permutation budgets `1`, `auto` and `8`; report actual probabilities, latency and divergence from a uniform reference |
| `receipt`          | Read the bundled CORD photo: 14 text, numeric, boolean and dependent fields                                                                |
| `receipt-us`       | Read your photo using 16 US receipt fields, including currency, tips and dependent tax/per-person amounts                                  |

The receipt calculations and text come from model inference. Expected values are used only for comparisons **after** inference. Receipt OCR and arithmetic may be wrong; the report keeps those errors. The die example does not sample a physical die or replace model probabilities with a uniform distribution. Permutation averaging costs additional evaluations and does not guarantee correctness.

## Models, downloads and devices

Text defaults to QJev3.5 0.8B v19c Q8_0 (~0.81 GB). Receipts default to Qwen3.5 2B Q4_K_M (~1.28 GB) with its matching F16 projector (~668 MB). Downloads use pinned Hugging Face revisions and show a progress bar, transfer speed and ETA. Files are cached in `~/.cache/turbojev`; cached models shared with the Python demos are reused. File sizes and GGUF headers are checked; the default text model is also SHA-256 verified. Interrupted downloads restart on the next run.

CPU is the default. GPU is an explicit request and fails when unsupported, without switching to CPU:

```powershell
dotnet run -c Release -- fair-die --device gpu
dotnet run -c Release -- receipt --device gpu --fields first_item,total
dotnet run -c Release -- receipt-us --device gpu --image C:/photos/receipt.jpg --fields store,total,currency
dotnet run -c Release -- ticket --model C:/models/text.gguf
dotnet run -c Release -- receipt --image C:/photos/receipt.jpg --model C:/models/vision.gguf --mmproj C:/models/mmproj.gguf
```

For text, `TURBOJEV_MODEL` also selects a local model. A custom vision model requires **both** `--model` and `--mmproj`; the projector must match that model. `--fields` explicitly selects a subset and includes its dependencies. Full receipt extraction repeats image inference for each field and can take several minutes. `--max-tokens 64` bounds generated output per field. Media thinking is disabled because that runtime mode is unsupported.

```csharp
// Typed fields use the same JSON contract as every other binding.
var responseJson = await engine.GenerateJsonAsync(JsonSerializer.Serialize(request));
// Original choice/noul/score requests still use EvaluateJsonAsync.
```

`fair-die --all-permutations` additionally evaluates all **720** orderings; this is intentionally opt-in. `evaluate` uses `orderRobustness = "none"`; `Program.cs` documents the optional `"balanced"` canonical probability mean and `"cyclic"` rotation logit mean. Both cost extra inference and preserve score scales. The `generate` API uses its separate per-field `permutations` setting.

## Results and architecture

Each command writes `result-<example>.json`; use `--output PATH` to change it. Reports record package version, process architecture, device, model/projector hashes, real responses, errors and timing. Receipts also record image hash and selected fields. The bundled receipt uses its original labels automatically; your own photo has no labels unless `--reference-labels` explicitly selects the original example's labels. Never use that flag to score an unrelated photo.

```powershell
dotnet publish -c Release -r win-x86 --self-contained false
dotnet publish -c Release -r win-x64 --self-contained false
dotnet publish -c Release -r win-arm64 --self-contained false
```

The published NuGet package contains native Windows x86/x64/ARM64 assets. Execute each build on a matching host or emulator. A successful cross-build is not proof of execution on that architecture. Linux/macOS require matching published native assets before these demos can run there. A 32-bit process may not fit the default vision model and projector; choose a smaller compatible pair. GPU support depends on the packaged backend and hardware.

## Verified execution

The Windows x64 runs below used the public NuGet package and cached models. These are integration checks, not isolated speed comparisons. All three RID builds passed; their native PE architectures and library hashes match the registry package. x86 and ARM64 were compiled, not executed. Fresh network downloads and the optional 720-ordering run were not exercised.

| Run               | Evidence                                                                                                                                                                                     |
| ----------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `ticket`, CPU     | [Actual response](../../../validation/0.30.1/csharp-ticket.json): shipping selected; 17.849s evaluation                                                                                         |
| `fields`, CPU     | [Actual response](../../../validation/0.30.1/csharp-fields.json): integer 7, decimal 324.5, boolean probability wrapper, actual null, dependent reminder and skipped conditional field; 23.311s |
| `fair-die`, GPU   | [Three distributions](../../../validation/0.30.1/csharp-fair-die.json) for budgets 1/auto/8; all normalized                                                                                     |
| `receipt`, GPU    | [Explicit three-field subset](../../../validation/0.30.1/csharp-receipt.json): first item, total and cash boolean; 3/3 labels match, 149.144s                                                   |
| `receipt-us`, GPU | [Explicit four-field subset](../../../validation/0.30.1/csharp-receipt-us.json): selecting per-person and currency included total/guests dependencies; 2/4 labels match, about 56s              |

The US model output misidentified currency and failed the per-person division. Those answers remain unchanged in the report. Full 14/16-field C# receipt runs were not measured here; both complete question sets are available through the commands without `--fields`. [Build evidence](../../../validation/0.30.1/csharp-builds.json) records the native payload checks.

## Attribution

Fair-die and receipt question/reference definitions are adapted from [TypeLLM](https://github.com/TypeLLM/TypeLLM/tree/main/examples), Apache-2.0; see `TYPELLM-LICENSE`.

The included photo is CORD-v2 test receipt 4: Park et al., _CORD: A Consolidated Receipt Dataset for Post-OCR Parsing_ (2019), NAVER/CLOVA, [CC BY 4.0](https://huggingface.co/datasets/naver-clova-ix/cord-v2). The image is retained unchanged and its separate license is [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/), rather than the code license. The US receipt reference photo is not redistributed because its image license has not been established; supply your own photo.

## Structured SDK examples (TurboJev 0.33.1)

```sh
dotnet run -- structured
dotnet run -- hierarchical
dotnet run -- discover-categories
dotnet run -- dice
dotnet run -- limits
```

All use the registry package, never a workspace build. Dice samples from the
model distribution with seed 42; fair-die measures the distribution with greedy
decoding and compares it with 1/6 per face. Auto costs six layouts, and all costs 720. Numeric limits constrain generated digits, including fractional digits.

QJev is specialized in bounded decisions. For open text/number extraction,
arrays or model reasoning, select a general instruction GGUF with `--model PATH`
(or `TURBOJEV_MODEL`). The example schemas stay unchanged; the host never
fabricates an answer. QJev is not expected to reproduce those generation demos.
Its upstream accuracy/calibration figures use a different prompt/scoring path
and do not describe these TurboJev runs. Alternative model URLs and integration
requirements are commented next to the model configuration in each entry point.
