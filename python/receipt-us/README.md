# US receipt extraction — Python

Port of TypeLLM's US receipt field definitions: store, date, items, table, guests, totals, currency, tips and model-computed dependent tax/per-person amounts. Uses only the published TurboJev wheel. Qwen3.5 2B GGUF plus its matching F16 projector downloads with progress by default; custom compatible vision model paths are supported.

Run from this folder. The model download and demo code are contained in `main.py`; no other demo folder is needed.

```powershell
python -m pip install -r requirements.txt
python main.py --image C:/photos/restaurant-receipt.jpg
python main.py --image C:/photos/restaurant-receipt.jpg --device gpu
python main.py --image C:/photos/restaurant-receipt.jpg --fields store,total,currency
python main.py --image C:/photos/original-sushi-yasuda.jpg --reference-labels
```

Supply your own image. The original WildReceipt photograph is not redistributed here because its separate image license has not been established. `--reference-labels` is only for the exact original Sushi Yasuda example; other images do not use its labels. This is an after-inference comparison, with no expected values in the prompt. The JSON report records full actual results, model/projector/package identity, image hash, latency, hardware and any reference matches. Small models can misread receipts or compute incorrectly; no host calculation substitutes for their answers.

CPU is the default; GPU must be explicitly requested with a supported backend. The code is portable and installed native assets follow Python's architecture. Current wheels cover Windows x86/x64/ARM64; a 32-bit process may need a smaller vision model. Other OS targets require matching native builds. Each field currently repeats image inference, so full extraction can be slow; `--fields` records a subset and includes its dependencies.

Adapted from [TypeLLM's receipt_us example](https://github.com/TypeLLM/TypeLLM/tree/main/examples/receipt_us), Apache-2.0; see `TYPELLM-LICENSE`. Reference labels originate from WildReceipt and the additional manually read fields described in that example. No TypeLLM benchmark result is represented as TurboJev evidence.

The [published 0.30.1 full run](../../validation/0.30.1/receipt-us.json) generated all 16 fields with Qwen3.5 2B and its F16 projector on Vulkan GPU: 11/15 reference labels matched. Evaluation took 177.319 seconds; other machine work overlapped. The report retains incorrect table/currency recognition and dependent arithmetic; its unscored expense note can also contain mistakes. The original photo was used only as local validation input and is not redistributed.
