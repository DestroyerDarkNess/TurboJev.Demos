# TurboJev — TypeScript / Node.js

Uses **@turbojev/node 0.33.0 from npm**. The TypeScript entry point imports `EvaluationRequest` and `GenerateRequest`, then calls the published engine methods. Shared CLI/download/report code lives in `../node_demo_common.mjs` with declarations in `../node_demo_common.d.mts`; it does not implement model inference. Keep the repository layout.

```powershell
npm install
npm start -- ticket
npm start -- fields
npm start -- fair-die --device gpu
npm start -- receipt --device gpu --fields first_item,total
npm start -- receipt-us --image C:/photos/receipt.jpg --device gpu
npm start -- --help
```

`npm start` first compiles with strict TypeScript settings. `ticket` retains choice/noul/score; `fields` demonstrates scalar JSON, probabilities, actual null, dependencies and skipped conditions. `fair-die` performs real permutation evaluations (1/auto/8). `--all-permutations` adds a potentially slow 720-ordering run.

Receipts include full 14/16-field schemas. `--fields a,b` explicitly records a subset and includes dependencies. CPU is the default; GPU is requested explicitly and does not fall back. Text downloads Qwen3 0.6B (~484 MB); images download Qwen3.5 2B plus its matching projector (~1.95 GB). Downloads show progress, speed and ETA, with the same cache and verification used by Node.

Use `--model PATH` (or `TURBOJEV_MODEL` for text) and `--mmproj PATH` together for custom vision models. `--max-tokens` limits generated output per field; `--output PATH` selects the report destination. Model answers, including dependent calculations and mistakes, remain unchanged. Expected receipt labels are checked afterward; your own photo has no reference labels unless explicitly selecting the original reference with `--reference-labels`.

The published native packages cover Windows ia32/x64/ARM64; run a matching Node process. A 32-bit process may need a smaller vision model. Linux/macOS require matching published native artifacts. Each image field repeats inference, so a full receipt can take minutes. See the [Node README](../TurboJev-js-native/README.md) for all options, report semantics, runtime limits and TypeLLM/CORD attribution.


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
decoding and compares it with 1/6 per face. Auto costs six layouts, and all costs
720. Numeric limits constrain generated digits, including fractional digits.


In PowerShell, pass options directly to Node if the npm shell wrapper consumes
them. Alternatively use `npm.cmd start -- <example> <options>`.

```powershell
npm run build
node dist/main.js limits --device gpu
```
