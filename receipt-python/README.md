# Receipt extraction — Python

Port of TypeLLM's photographed CORD receipt example. Uses the published `turbojev` wheel and a vision GGUF plus matching projector. Default: Qwen3.5 2B Q4_K_M and F16 projector from a pinned Unsloth revision. Both downloads have progress, speed and ETA; interrupted downloads can resume. There is no TypeLLM service or local TurboJev source dependency.

Run from this folder. The model download and demo code are contained in `main.py`; no other demo folder is needed.

```powershell
python -m pip install -r requirements.txt
python main.py
python main.py --device gpu
python main.py --fields first_item,total
python main.py --image C:/photos/my-receipt.jpg --model C:/models/vision.gguf --mmproj C:/models/mmproj.gguf
```

The 14 fields cover text, integer/decimal extraction, a boolean, dependent arithmetic and an expense note. Those calculations are decisions made by the model, not host arithmetic. Each generated field currently performs separate inference and repeats image preprocessing; a complete run can be slow on CPU. `--fields` is an explicitly recorded subset, with required dependencies included. `--max-tokens` bounds output per field (default 64). Media reasoning is disabled because that runtime mode is unsupported.

`result.json` records model, projector, package, hardware, image hash, subset status, full typed response, matched reference labels and timing. Labels are checked after inference, never sent to the model. When supplying your own image, labels are omitted unless you explicitly choose `--reference-labels` for the exact original image. Model loading successfully is not a guarantee of OCR accuracy. A larger capable vision model may be needed for small/blurred print.

The Python code is portable; native installation follows the Python process architecture. Registry wheels currently cover Windows x86/x64/ARM64. A 32-bit process may not have enough address space for the default model; use a smaller compatible vision GGUF/projector rather than claiming the model fits every target. Other operating systems require a matching built native package. GPU is an explicit request and may fail where unsupported.

Code and question/label definitions are adapted from [TypeLLM](https://github.com/TypeLLM/TypeLLM/tree/main/examples/receipt), Apache-2.0; see `TYPELLM-LICENSE`. The included photograph is CORD-v2 test receipt 4, attributed to Park et al., *CORD: A Consolidated Receipt Dataset for Post-OCR Parsing* (2019), NAVER/CLOVA. The dataset is [CC BY 4.0](https://huggingface.co/datasets/naver-clova-ix/cord-v2); [license terms](https://creativecommons.org/licenses/by/4.0/). The image is retained as supplied in the reference example; it is not covered by the code's Apache license.

The [published 0.30.1 full run](../validation/0.30.1/receipt.json) generated all 14 fields with Qwen3.5 2B and its F16 projector on Vulkan GPU: 10/13 reference labels matched. Evaluation took 588.489 seconds; other machine work overlapped. The report retains OCR/arithmetic mistakes and the unscored expense note, which can also contain errors. This is functional evidence, not a guarantee of perfect extraction or an isolated speed comparison.
