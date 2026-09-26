# Python Snake

A terminal Snake game where TurboJev evaluates one-step progress using a local GGUF model. Each legal move is grouped by whether it gets closer to, stays the same distance from, or gets farther from the food. TurboJev chooses the progress category; the host keeps moving straight when multiple directions in the chosen category are equivalent. Moves forced by the game rules are applied without a model call. This keeps the model responsible for the semantic decision while avoiding arbitrary direction tie-breaks.

The state describes positions and their meaning in plain language (for example, that the food is west and north of the head). This helps small models compare candidates without having to infer the relationship from coordinates alone. See the [decision-design guide](https://github.com/DestroyerDarkNess/TurboJev/blob/main/docs/DECISION_DESIGN.md) for the general pattern.

## Run

```sh
python -m pip install -r requirements.txt
python snake.py
```

At launch, the demo recommends **Qwen3 0.6B Instruct, GGUF Q4_K_M** (about 0.48 GB). Press Enter at the model prompt to download it with a progress bar and cache it, or enter the path to another GGUF. You can also pass a path directly:

```sh
python snake.py --model /path/to/model.gguf
```

On Windows, for example:

```powershell
py -m pip install -r requirements.txt
py snake.py --model D:\Models\model.gguf
```

Set `TURBOJEV_MODEL` to provide the model path without a prompt. Use `--max-turns 200` to change the default 100-turn game and `--seed 7` for repeatable food placement. The demo runs on CPU and uses single-pass scoring by default. Pass `--order-robustness cyclic` to reduce sensitivity to candidate order; this can increase inference time.

At startup, the demo simulates the same seed with a simple greedy reference policy and reports how much food that policy reaches within the turn limit. This confirms that the board is reachable; it does not affect TurboJev's decisions or the game.

## Platform and architecture

The Python source uses only the standard library and runs on Windows, Linux, and macOS. It installs TurboJev from PyPI; the native package must provide a wheel matching the host OS, CPU architecture, and Python ABI. PyPI release **0.29.1** currently provides Windows x86, x64, and ARM64 wheels. Check the [TurboJev PyPI files](https://pypi.org/project/turbojev/#files) for newer platform builds before installing elsewhere. A matching Python interpreter is required for each architecture.

## Benchmark

After the game ends, the benchmark reports model-load time, host and architecture, score, first food turn, the greedy-reference result, decision count, total and mean inference time, median and p95 decision latency, decisions per second, and the selected order-scoring mode. Inference timings measure `evaluate` only; they exclude terminal rendering and the short animation pause.

```powershell
py snake.py --seed 0 --max-turns 100
py snake.py --seed 0 --max-turns 100 --order-robustness cyclic
```
