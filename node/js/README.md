# TurboJev — Node.js

Run from this folder with Node.js 20 or later. Install **@turbojev/node 0.33.0 from npm**, including the native package matching your Node process architecture.

```powershell
npm install
npm start -- ticket
npm start -- fields
npm start -- fair-die --device gpu
npm start -- receipt --device gpu --fields first_item,total
npm start -- receipt-us --image C:/photos/receipt.jpg --device gpu
```

`ticket` uses `evaluate` for choice/noul/score. `fields` uses `generate` for integers, decimals, boolean probabilities, actual null, dependencies and conditions. `fair-die` compares real model distributions for budgets 1/auto/8; add `--all-permutations` only to opt into 720 evaluations. Permutation averaging is extra inference, not a guarantee of correctness.

Receipts request all 14 CORD or 16 US fields unless `--fields` selects a recorded subset; dependencies are included. Images and arithmetic are processed by the model. Ground-truth labels are compared afterward and never supplied in its request. The bundled CORD photo uses its labels automatically. For your own images no labels apply; `--reference-labels` is only for the exact original reference photo. The original US image is not bundled.

CPU is the default; `--device gpu` explicitly requests a supported native GPU backend and does not fall back. Text defaults to QJev3.5 0.8B v19c Q8_0 (~0.81 GB). Images default to Qwen3.5 2B Q4_K_M plus matching F16 projector (~1.95 GB together). Pinned downloads show percentage, speed and ETA and share `~/.cache/turbojev` with the other demos. Interrupted downloads restart; default file sizes/GGUF headers are checked, plus a SHA-256 check for the default text model.

```powershell
npm start -- ticket --model C:/models/text.gguf
npm start -- receipt --model C:/models/vision.gguf --mmproj C:/models/mmproj.gguf --image C:/photos/receipt.jpg
npm start -- fields --output C:/results/fields.json
npm start -- --help
```

Text also accepts `TURBOJEV_MODEL`. Custom vision models require both paths. Generated strings/numbers are limited to 64 tokens per field by default (`--max-tokens`). Receipt extraction repeats image processing per field and can take minutes. Errors and incorrect answers remain in JSON reports; typed output does not guarantee model accuracy. The `evaluate` order-robustness comment explains the slower `cyclic` option; `generate` uses per-field `permutations` instead.

`main.js` imports the published SDK. The application owns its `demo.mjs` download/CLI/report code and all input data. It contains no inference implementation and imports no other demo. You can copy this folder independently. Reports default to `result-<example>.json` and include actual responses, timing, model hashes, device, architecture and errors.

Current native npm packages cover Windows ia32/x64/ARM64. Run with the matching Node architecture; CPU/GPU backend support and available memory still apply. A 32-bit process may not fit the default vision pair. Other OS targets require matching published native packages; no local SDK is built as a workaround.

Fair die and receipt definitions are adapted from TypeLLM, Apache-2.0; see [its retained license](TYPELLM-LICENSE). The CORD photograph is separately CC BY 4.0, NAVER/CLOVA, Park et al. (2019); attribution and source are in the [receipt README](../../python/receipt/README.md).

## Structured SDK examples (TurboJev 0.33.0)

```sh
npm start -- structured
npm start -- hierarchical
npm start -- discover-categories
npm start -- dice
npm start -- limits
```

All use the registry package, never a workspace build. Dice samples from the
model distribution with seed 42; fair-die measures the distribution with greedy
decoding and compares it with 1/6 per face. Auto costs six layouts, and all costs 720. Numeric limits constrain generated digits, including fractional digits.

In PowerShell, pass options directly to Node if the npm shell wrapper consumes
them. Alternatively use `npm.cmd start -- <example> <options>`.

```powershell
node main.js dice --device gpu
```

Bundled image attribution: [data/receipt/ATTRIBUTION.md](data/receipt/ATTRIBUTION.md).

QJev is specialized in bounded decisions. For open text/number extraction,
arrays or model reasoning, select a general instruction GGUF with `--model PATH`
(or `TURBOJEV_MODEL`). The example schemas stay unchanged; the host never
fabricates an answer. QJev is not expected to reproduce those generation demos.
Its upstream accuracy/calibration figures use a different prompt/scoring path
and do not describe these TurboJev runs. Alternative model URLs and integration
requirements are commented next to the model configuration in each entry point.
