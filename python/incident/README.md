# Incident

Evaluate incident severity, then decide whether to roll back, then draft a status message using both earlier answers.

Port of [TypeLLM's example](https://typellm.ai/examples/incident), accessed 2026-10-10.
Uses **TurboJev 0.33.1 from PyPI**, not local SDK source or a hosted API.

Run from this folder, or copy it anywhere:

```sh
python -m pip install -r requirements.txt
python main.py
python main.py --device gpu
python main.py --model /path/to/model.gguf
python main.py --dry-run
```

Defaults to QJev3.5 0.8B v19c Q8_0 (~0.81 GB). The download shows progress, speed and
ETA, verifies its checksum and caches under `~/.cache/turbojev`. CPU is the
default; requesting an unsupported GPU returns an error without fallback.

`--context "..."` replaces the input. `--thinking example|off|auto|low|medium|high`
overrides reasoning. `--permutations 1|auto|8|all` overrides finite-field budgets;
`--max-tokens` bounds generated values. Thinking can exhaust its budget/context.

`result.json` retains the request, actual response, skipped fields, probabilities,
reasoning, usage, model hash and loading/inference times. Use `--output PATH` for
another destination. Model errors retain their message and available partial usage.
Small-model mistakes remain visible; hosted TypeLLM results are not promised.
Probabilities are conditional model scores, not fitted calibration.

All Python code belongs to this folder; there are no imports or invocations of
other demos. Native wheels currently cover Windows x86/x64/ARM64. Other systems
need compatible registry packages; portable code does not establish execution
on every architecture. Source attribution/license: `TYPELLM-LICENSE`.

QJev is specialized in bounded decisions. For open text/number extraction,
arrays or model reasoning, select a general instruction GGUF with `--model PATH`
(or `TURBOJEV_MODEL`). The example schemas stay unchanged; the host never
fabricates an answer. QJev is not expected to reproduce those generation demos.
Its upstream accuracy/calibration figures use a different prompt/scoring path
and do not describe these TurboJev runs. Alternative model URLs and integration
requirements are commented next to the model configuration in each entry point.

Thinking defaults to `off`. `--thinking example` retains the original
source schema settings when using a compatible general model.
