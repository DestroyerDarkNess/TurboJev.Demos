"""Measure the installed registry package; never replace a model-selected action."""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import importlib.metadata
import io
import json
from pathlib import Path
import time

import snake
from turbojev import TurboJev

CASES = [
    ("top_wall", [(6, 0), (6, 1)], "up", (11, 0), {"right"}),
    ("bottom_wall", [(6, 9), (6, 8)], "down", (1, 9), {"left"}),
    ("left_wall", [(0, 5), (1, 5)], "left", (0, 9), {"down"}),
    ("right_wall", [(11, 5), (10, 5)], "right", (11, 0), {"up"}),
    ("diagonal_food", [(6, 5), (5, 5)], "right", (11, 0), {"up", "right"}),
    ("body_blocks_food_direction", [(6, 5), (6, 6), (7, 6), (7, 5), (8, 5)], "up", (11, 5), {"up", "left"}),
]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--max-turns", type=int, default=40)
    parser.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2])
    parser.add_argument("--output", type=Path, default=Path(".artifacts/sensors-benchmark.json"))
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    records, games = [], []
    load_started = time.perf_counter()
    with TurboJev.load(str(args.model.resolve()), device="cpu", n_gpu_layers=0,
                       n_seq_max=4, thinking=False,
                       execution={"orderRobustness": "none"}) as engine:
        load_seconds = time.perf_counter() - load_started
        runtime_info = engine.info()
        # Hide terminal drawing only; play() still evaluates each move and
        # executes the actual response using unchanged game physics and RNG.
        snake.HAS_RICH = False
        snake.console = None
        snake.draw_legacy = lambda *args: None
        for fmt in ("coordinates", "sensors"):
            cases = CASES[:1] if fmt == "coordinates" else CASES
            for name, body, direction, food, expected in cases:
                for rotation in range(4):
                    request = snake.make_move_request(body, direction, food, fmt)
                    entries = list(request["questions"]["move"]["criteria"].items())
                    request["questions"]["move"]["criteria"] = dict(entries[rotation:] + entries[:rotation])
                    start = time.perf_counter()
                    response = engine.evaluate(request)
                    seconds = time.perf_counter() - start
                    move = response["answers"]["move"]["choice"]
                    after, ate, collision = snake.apply_move(body, direction, food, move)
                    result = {"case": name, "format": fmt, "rotation": rotation,
                              "expected_choices": sorted(expected), "correct": move in expected and collision is None,
                              "request": request, "response": response, "seconds": seconds,
                              "model_choice": move, "applied_choice": move, "collision": collision}
                    records.append(result)
                    print(f"{fmt} {name} rotation={rotation}: {move} correct={result['correct']} {seconds:.3f}s", flush=True)
            if fmt == "sensors":
                for seed in args.seeds:
                    trace = args.output.with_name(f"{args.output.stem}-seed-{seed}.jsonl")
                    with contextlib.redirect_stdout(io.StringIO()):
                        summary = snake.play(engine, str(args.model), args.max_turns, load_seconds,
                                             "none", seed, trace, "sensors", False)
                    entries = [json.loads(line) for line in trace.read_text().splitlines()]
                    decisions = [entry for entry in entries if entry["event"] == "decision"]
                    assert all(entry["model_choice"] == entry["applied_choice"] ==
                               entry["response"]["answers"]["move"]["choice"] for entry in decisions)
                    games.append(summary)
                    print(f"seed={seed}: food={summary['score']} decisions={summary['model_decisions']} "
                          f"mean={summary['latency_mean_ms']:.1f}ms end={summary['end_reason']}", flush=True)
    digest = hashlib.sha256()
    with args.model.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    checksum = digest.hexdigest()
    report = {"package_source": "PyPI registry; no local native library or source engine override",
              "turbojev": importlib.metadata.version("turbojev"), "model": args.model.name,
              "model_sha256": checksum, "demo_sha256": hashlib.sha256(Path(snake.__file__).read_bytes()).hexdigest(),
              "device": "cpu", "thinking": False, "order_robustness": "none", "n_seq_max": 4,
              "runtime_info": runtime_info, "records": records, "games": games,
              "host_observation_preprocessing": "sensors derives relative food direction and immediate collision facts",
              "host_selects_or_replaces_actions": False,
              "limitations": "Sensors simplify perception; no optimal-path search or general spatial-reasoning qualification. Six small probes and three seeds are not a reliability guarantee."}
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Saved {args.output}")


if __name__ == "__main__":
    main()
