# Python Snake

A small terminal Snake game where TurboJev chooses each legal move using a local GGUF model. Its game state and question follow [LLM2Jev's Snake demo](https://github.com/Yinsongxu/LLM2Jev/blob/main/demos/snake.py); moves forced by the game rules are made directly without a model call.

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

Set `TURBOJEV_MODEL` to provide the model path without a prompt. Use `--max-turns 200` to change the default 100-turn game and `--seed 7` for repeatable food placement. The demo runs on CPU and uses cyclic option-order scoring by default, which evaluates each legal option rotation to reduce first-option bias. Pass `--fast` for a single scoring pass per move; it is quicker but more sensitive to option order.

## Platform and architecture

The Python source uses only the standard library and runs on Windows, Linux, and macOS. It installs TurboJev from PyPI; the native package must provide a wheel matching the host OS, CPU architecture, and Python ABI. PyPI release **0.29.1** currently provides Windows x86, x64, and ARM64 wheels. Check the [TurboJev PyPI files](https://pypi.org/project/turbojev/#files) for newer platform builds before installing elsewhere. A matching Python interpreter is required for each architecture.

## Benchmark

After the game ends, the last output is a benchmark containing model-load time, host and architecture, score, decision count, total and mean inference time, median and p95 decision latency, decisions per second, and the selected order-scoring mode. Inference timings measure `evaluate` only; they exclude terminal rendering and the short animation pause.
