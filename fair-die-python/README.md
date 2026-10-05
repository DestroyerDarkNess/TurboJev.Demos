# Fair die — Python

Uses the published TurboJev package with Qwen3 0.6B GGUF (download progress included). Compares one order, a balanced `auto` design and eight sampled permutations. The optional full run evaluates all 720 permutations. Every option score comes from the model; there is no host-generated uniform answer.

```powershell
python -m pip install -r fair-die-python/requirements.txt
python fair-die-python/main.py
python fair-die-python/main.py --model C:/models/model.gguf --device gpu
python fair-die-python/main.py --all-permutations
```

CPU is the default. Only request GPU with a supported native package/backend. Output records the actual distribution, latency, package version and KL divergence from uniform; this is a permutation demonstration, not proof of calibrated confidence or reasoning accuracy. `result.json` is a local run artifact. Model paths can be supplied or set with `TURBOJEV_MODEL`.

Portable Python code uses the installed wheel matching the Python process architecture. Current native wheels cover Windows x86/x64/ARM64; the same source can run elsewhere with a built TurboJev native package. Memory and GPU availability still depend on the target.

Adapted from [TypeLLM's fair_die example](https://github.com/TypeLLM/TypeLLM/tree/main/examples/fair_die), Apache-2.0. Its original model results are not TurboJev evidence; the retained license and source attribution are in this folder.

The [published-package run](../validation/0.30.1/fair-die.json) with Qwen3 0.6B and explicit GPU measured KL from uniform of 5.7107 (one order), 0.1188 (`auto`) and 0.8674 (eight sampled orders). These are real model distributions; improvement is not guaranteed for every model or budget.
