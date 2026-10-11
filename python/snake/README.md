# Python Snake

A terminal Snake game controlled by TurboJev using the installed PyPI package
and a local GGUF model. Every turn calls `evaluate` with four choices: `up`,
`down`, `left`, and `right`. The state contains the board size, head, body,
food, current direction, and coordinate convention in the raw-board modes.
The default `sensors` mode supplies only relative food direction and immediate
collision observations, reducing the arithmetic required from a small model.

The host implements game physics and random food placement. It does not compute
food distances, group moves by progress, mask options, resolve ties, skip
inference for forced moves, or replace a returned choice. Collisions and direct
reversals end the game. Invalid responses raise an error without a fallback.
Incorrect choices remain visible, including moves away from food. In `sensors`
mode the host checks the four adjacent cells using the game's collision rules
and reports clear/blocked directions. This is explicit perception assistance,
not a raw-board reasoning test. All four choices remain available, and the host
never chooses, filters or replaces an action. It does not search for a route.

Earlier versions asked the model for a progress category and selected directions
in host code. Their scores measured an assisted policy and must not be presented
as evidence of model-controlled Snake or compared with this version's scores.

## Run

```sh
python -m pip install -r requirements.txt
python snake.py
```

The default download is **QJev3.5 0.8B v19c GGUF Q8_0**, about 0.81 GB, with a progress
bar and a local cache. Supply another compatible GGUF through the prompt,
`TURBOJEV_MODEL`, or a command-line path:

```sh
python snake.py --model /path/to/model.gguf --seed 0 --max-turns 100
```

On Windows:

```powershell
py snake.py --model D:/Models/model.gguf --seed 0 --max-turns 100
```

CPU and single-pass scoring are the defaults. `--order-robustness cyclic` enables
optional candidate-order correction; it costs extra inference and does not
guarantee correct decisions. The prompt does not provide a precomputed route or
best action, so a small model may fail at arithmetic, navigation, or survival.

## Audit and benchmark

Each run writes a timestamped JSONL file under `.artifacts/`. Set `--trace` to
choose an output file; an explicitly supplied file is overwritten:

```sh
python snake.py --model /path/to/model.gguf --trace .artifacts/audit.jsonl
```

Each decision contains the full request and response, model choice, applied
choice, before/after positions, food, collision, and `evaluate` latency. The
model and applied choices must match. The final record reports score, executed
steps, model decision count, load time, latency mean/median/p95, and the game's
end reason. An attempted collision counts as a decision but not an executed
step. No success or latency is credited to a host-selected move.

Integrity regressions use scripted responses to confirm that incorrect choices
are not rescued. They do not measure real model quality:

```sh
python -m unittest test_snake.py
```

## Platform and architecture

Install TurboJev from PyPI for the target OS, CPU architecture, and Python ABI;
the demo does not load library code or native builds from a TurboJev checkout.
The optional Rich terminal UI is used when available; otherwise a standard
terminal board is printed. Check the
[published wheel files](https://pypi.org/project/turbojev/#files) before assuming
platform support. A matching Python interpreter is needed for each wheel.

## Recorded smoke test

On 2026-10-04, the installed PyPI TurboJev 0.29.1 package with Qwen3 0.6B
Q4_K_M, seed 0, and single-pass scoring chose `up` six times. Five moves were
executed; the sixth hit the wall. Score: **0 food**. Mean `evaluate` latency:
**2.32 s** on this Windows x64 machine. No choice was replaced by the host.

The [recorded requests and responses](validation/qwen-direct-movement.json)
include the model hash and all six decisions. This is a failed navigation run,
not a claim that Snake is solved. It replaces earlier assisted-policy claims.

## Experimental representation and reasoning

`--state-format sensors` is the default: relative food direction plus clear and
blocked directions. The request contains no distances, optimal path, preferred
action or host-selected movement. This representation exposes fewer facts than
the full board and cannot reason about distant traps or future body positions.

`--state-format coordinates` restores the original raw state. `--state-format grid` supplies
an ASCII board with H (head), B (body), T (tail), F (food) and empty cells. Both
formats expose all four directions and execute the returned choice unchanged.
The grid experiment did not qualify Qwen3.5-2B for reliable navigation; changing
representation alone is not a demonstrated fix. The default Qwen0.6B download
is a small baseline, not a recommended autonomous navigation policy.

`--thinking --max-thinking-tokens 512` enables optional native model reasoning
when a published TurboJev package supporting those fields is installed. It is
off by default, consumes extra model tokens and can return an explicit budget
error. This demo still imports TurboJev from PyPI, with no local engine override.
The pinned PyPI package 0.33.1 supports this optional native text mode.

The 0.33.1 package also accepts `--order-robustness balanced`. It averages
probabilities from canonical option layouts at extra inference cost. This is
optional and does not select, replace or simulate moves on the host.

## Simplified-input results with 0.30.1

The [registry-package report](validation/qwen-sensors-0292.json) uses Qwen3
0.6B Q4_K_M on Windows x64, CPU, `n_seq_max=4`, single-pass scoring and `thinking=False`.
Three 40-turn games, seeds 0/1/2, ate **3/4/3 food** and all reached the turn
limit without a collision. All 120 model choices were applied unchanged.
Mean per-decision times were approximately **459/513/766 ms**, excluding load
time. An additional prompt experiment overlapped part of the run, so these
timings are diagnostic observations, not a controlled speed comparison.

The six-state/four-order probe passed **18/24** and still has errors; inspect the per-case results
in the report. Successful fixed-order games do not imply order independence,
optimal paths or general navigation reliability. The raw-coordinate wall probe
remains a separate baseline in the same report. No model choice was rescued.

To reproduce with the installed PyPI package:

```sh
python benchmark.py --model /path/to/Qwen3-0.6B-Q4_K_M.gguf --seeds 0 1 2 --max-turns 40
```

This writes full requests, responses, timings and game traces to `.artifacts/`.

The default is QJev3.5 0.8B v19c Q8_0. This is a decision-specialized
checkpoint, not a guarantee of correct routing, tone or Snake navigation.
Alternative GGUF repositories are commented in the entry point.
