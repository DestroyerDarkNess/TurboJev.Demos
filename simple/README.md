# Simple Python demo

The original Jev three-question example, implemented with TurboJev's `evaluate`
API: one message produces an urgency gate (`noul`), a team (`choice`), and an
ordered assessment of tone (`score`). All answers come from the model.

## Run

From this folder, with Python 3.9 or newer:

```sh
python -m pip install --upgrade -r requirements.txt
python main.py
```

The demo installs TurboJev 0.29.2 from PyPI. It does not build TurboJev or import
its local source. The default Qwen3-0.6B Q4_K_M GGUF downloads with a progress
bar on first run and is reused from `~/.cache/turbojev/` afterwards. CPU is the
default; model loading happens before the printed evaluation timer starts.

To use another local GGUF, set `TURBOJEV_MODEL`:

```powershell
$env:TURBOJEV_MODEL = "C:\models\model.gguf"
python main.py
```

```sh
TURBOJEV_MODEL=/path/to/model.gguf python main.py
```

## Read the answers

TurboJev returns a dictionary, rather than the original SDK's attribute groups:

```python
answers = response["answers"]
answers["urgent"]["noul"]
answers["team"]["choice"]
answers["team"]["confidence"]
answers["tone"]["score"]
```

`noul` is the relative score of the affirmative answer, not a Python boolean.
`score` is the expected zero-based level across `calm`, `annoyed`, and `furious`,
so it may be fractional. The demo prints the actual values and full response;
it does not promise or substitute the original example's 1.00/2.00 results.
Candidate probabilities are not calibrated confidence.

One real Windows x64 CPU run with the PyPI 0.29.2 wheel and Qwen3-0.6B Q4_K_M
returned `urgent=0.9776`, `team="outage"` (relative confidence `0.9952`), and
`tone=1.0023`. Evaluating all three questions took 12.309 seconds, excluding
model loading. These are observed results from one run, not expected outputs
or a latency guarantee.

`thinking=False` and `orderRobustness="none"` keep the normal scoring path.
Change robustness to `"cyclic"` to average choice rotations at extra inference
cost, or enable native thinking when using a suitable model and token budget.

## Platforms

The Python source is portable. PyPI 0.29.2 supplies Windows x86, x64, and ARM64
wheels; use Python matching the desired architecture. Linux and macOS require
matching published native wheels and are not validated by this example.
