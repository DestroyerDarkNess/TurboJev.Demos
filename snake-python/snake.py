"""Play a small terminal Snake game with typed TurboJev choices."""

from __future__ import annotations

import argparse
import importlib.metadata
import math
import os
import platform
import random
import statistics
import sys
import time
from pathlib import Path
from urllib.request import urlopen

from turbojev import TurboJev


MODEL_URL = (
    "https://huggingface.co/bartowski/Qwen_Qwen3-0.6B-GGUF/resolve/main/"
    "Qwen_Qwen3-0.6B-Q4_K_M.gguf?download=true"
)
MODEL_NAME = "Qwen3 0.6B Instruct · GGUF · Q4_K_M (~0.48 GB)"
DIRECTIONS = {
    "up": (0, -1),
    "down": (0, 1),
    "left": (-1, 0),
    "right": (1, 0),
}
OPPOSITE = {"up": "down", "down": "up", "left": "right", "right": "left"}
WIDTH, HEIGHT = 12, 10


def download_default_model() -> Path:
    cache = Path.home() / ".cache" / "turbojev" / "Qwen3-0.6B-Q4_K_M.gguf"
    cache.parent.mkdir(parents=True, exist_ok=True)
    if cache.exists():
        print(f"Using cached model: {cache}")
        return cache

    temporary = cache.with_suffix(cache.suffix + ".part")
    print(f"Downloading {MODEL_NAME} from Hugging Face")
    try:
        with urlopen(MODEL_URL, timeout=30) as response, temporary.open("wb") as output:
            total = int(response.headers.get("Content-Length", "0"))
            received = 0
            while chunk := response.read(1024 * 1024):
                output.write(chunk)
                received += len(chunk)
                if total:
                    ratio = min(1.0, received / total)
                    width = 28
                    bar = "█" * round(ratio * width) + "─" * (width - round(ratio * width))
                    print(f"\r[{bar}] {ratio:5.1%}  {received / 2**20:.0f}/{total / 2**20:.0f} MB", end="", flush=True)
                else:
                    print(f"\rDownloaded {received / 2**20:.0f} MB", end="", flush=True)
        print()
        temporary.replace(cache)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise
    return cache


def choose_model(argument: str | None) -> str:
    configured = argument or os.getenv("TURBOJEV_MODEL")
    print("TurboJev Snake")
    print(f"Recommended model: {MODEL_NAME}")
    print("Use a local GGUF path for another llama.cpp-compatible model.")
    if configured:
        print(f"Model: {configured}")
        return configured
    value = input("GGUF path (Enter downloads/caches the recommended model): ").strip()
    if value:
        path = Path(value).expanduser()
        if not path.is_file():
            raise FileNotFoundError(f"GGUF file not found: {path}")
        return str(path.resolve())
    return str(download_default_model())


def spawn_food(
    snake: list[tuple[int, int]], rng: random.Random | None = None
) -> tuple[int, int] | None:
    free = [(x, y) for x in range(WIDTH) for y in range(HEIGHT) if (x, y) not in snake]
    chooser = rng or random
    return chooser.choice(free) if free else None


def safe_moves(snake: list[tuple[int, int]], direction: str) -> list[str]:
    head = snake[0]
    moves = []
    for name, (dx, dy) in DIRECTIONS.items():
        if len(snake) > 1 and name == OPPOSITE[direction]:
            continue
        target = (head[0] + dx, head[1] + dy)
        # Moving onto the tail is safe when it moves away on this turn.
        body = snake[:-1]
        if 0 <= target[0] < WIDTH and 0 <= target[1] < HEIGHT and target not in body:
            moves.append(name)
    return moves


def draw(snake: list[tuple[int, int]], food: tuple[int, int], score: int, step: int) -> None:
    cells = {point: "●" for point in snake[1:]}
    cells[snake[0]] = "◆"
    cells[food] = "★"
    print("\033[2J\033[H", end="")
    print(f"TurboJev Snake  ·  score {score}  ·  turn {step}  ·  food ★  snake ◆")
    print("┌" + "──" * WIDTH + "┐")
    for y in range(HEIGHT):
        print("│" + "".join(cells.get((x, y), "·") + " " for x in range(WIDTH)) + "│")
    print("└" + "──" * WIDTH + "┘")


def percentile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, math.ceil(fraction * len(ordered)) - 1)]


def closest_safe_move(
    snake: list[tuple[int, int]], direction: str, food: tuple[int, int]
) -> str | None:
    """Simple model-free reference: minimize the next-step Manhattan distance."""
    options = safe_moves(snake, direction)
    if not options:
        return None
    head_x, head_y = snake[0]
    distances = {
        name: abs(head_x + DIRECTIONS[name][0] - food[0])
        + abs(head_y + DIRECTIONS[name][1] - food[1])
        for name in options
    }
    best = min(distances.values())
    tied = [name for name in options if distances[name] == best]
    return direction if direction in tied else min(tied)


def greedy_reference(seed: int, max_turns: int) -> tuple[int, int | None]:
    """Verify that the seeded board is reachable without calling a model."""
    rng = random.Random(seed)
    snake = [(WIDTH // 2, HEIGHT // 2), (WIDTH // 2 - 1, HEIGHT // 2)]
    direction = "right"
    food = spawn_food(snake, rng)
    assert food is not None
    score = 0
    first_food_turn: int | None = None
    for step in range(1, max_turns + 1):
        direction = closest_safe_move(snake, direction, food)
        if direction is None:
            break
        dx, dy = DIRECTIONS[direction]
        head = (snake[0][0] + dx, snake[0][1] + dy)
        snake.insert(0, head)
        if head == food:
            score += 1
            first_food_turn = first_food_turn or step
            food = spawn_food(snake, rng)
            if food is None:
                break
        else:
            snake.pop()
    return score, first_food_turn


def play(engine: TurboJev, model: str, max_turns: int, load_seconds: float,
         order_robustness: str, seed: int, reference_score: int,
         reference_first_food: int | None) -> None:
    rng = random.Random(seed)
    snake = [(WIDTH // 2, HEIGHT // 2), (WIDTH // 2 - 1, HEIGHT // 2)]
    direction = "right"
    food = spawn_food(snake, rng)
    assert food is not None
    score = 0
    first_food_turn: int | None = None
    latencies: list[float] = []
    forced_moves = 0
    game_started = time.perf_counter()
    game_over = "turn limit reached"

    for step in range(1, max_turns + 1):
        draw(snake, food, score, step)
        options = safe_moves(snake, direction)
        if not options:
            game_over = "no safe moves"
            break
        if len(options) == 1:
            # Like the reference demo, skip inference when the game rules force a move.
            direction = options[0]
            forced_moves += 1
        else:
            head_x, head_y = snake[0]
            food_x, food_y = food
            current_distance = abs(head_x - food_x) + abs(head_y - food_y)
            move_details = {}
            move_groups: dict[str, list[str]] = {}
            for name in options:
                dx, dy = DIRECTIONS[name]
                target = (head_x + dx, head_y + dy)
                distance_after = abs(target[0] - food_x) + abs(target[1] - food_y)
                change = distance_after - current_distance
                progress = "closer" if change < 0 else "farther" if change > 0 else "same distance"
                move_groups.setdefault(progress, []).append(name)
                move_details[name] = f"{name} (distance {distance_after})"
            # Let TurboJev choose the semantic progress class. The host resolves
            # equivalent directions with a fixed tie-break, rather than asking a
            # 0.6B model to distinguish equally good route steps.
            decision_criteria = {
                progress: "Safe legal moves: " + ", ".join(move_details[name] for name in move_groups[progress])
                for progress in ("closer", "same distance", "farther")
                if progress in move_groups
            }

            if len(move_groups) == 1:
                choice, selected_moves = next(iter(move_groups.items()))
                direction = direction if direction in selected_moves else min(selected_moves)
                forced_moves += 1
                print(f"Decision {step}: only {choice} moves are legal; continue {direction}.")
            else:
                horizontal = (
                    f"{abs(head_x - food_x)} squares {'west' if food_x < head_x else 'east'}"
                    if food_x != head_x else "in the same column"
                )
                vertical = (
                    f"{abs(head_y - food_y)} squares {'north' if food_y < head_y else 'south'}"
                    if food_y != head_y else "in the same row"
                )
                state = (
                    f"Food is {horizontal} and {vertical} relative to the snake head. "
                    f"Manhattan distance: {current_distance}."
                )
                request = {
                    "state": state,
                    "questions": {
                        "move": {
                            "type": "choice",
                            "instructions": (
                            "Choose the category with the lowest resulting Manhattan distance. "
                            "Decide one step only; the host resolves ties."
                            ),
                            "criteria": decision_criteria,
                        }
                    },
                }
                started = time.perf_counter()
                response = engine.evaluate(request)["answers"]["move"]
                latency = time.perf_counter() - started
                latencies.append(latency)
                choice = response.get("choice")
                if choice not in move_groups:
                    choice = max(response["probabilities"], key=response["probabilities"].get)
                selected_moves = move_groups.get(choice, options)
                direction = direction if direction in selected_moves else min(selected_moves)
                probability_text = ", ".join(
                    f"{category} {probability:.0%}"
                    for category, probability in response["probabilities"].items()
                )
                print(
                    f"Decision {step}: head ({head_x}, {head_y}), food ({food_x}, {food_y}); "
                    f"chose {choice} → {direction} — {probability_text}"
                )

        dx, dy = DIRECTIONS[direction]
        head = (snake[0][0] + dx, snake[0][1] + dy)
        snake.insert(0, head)
        if head == food:
            score += 1
            first_food_turn = first_food_turn or step
            food = spawn_food(snake, rng)
            if food is None:
                game_over = "board filled"
                break
        else:
            snake.pop()
        time.sleep(0.12)
    else:
        step = max_turns

    elapsed = time.perf_counter() - game_started
    draw(snake, food if food is not None else snake[0], score, step)
    print(f"Game over: {game_over}.")

    print("\nBenchmark")
    print(f"  Model:             {Path(model).name}")
    print(f"  TurboJev:          {importlib.metadata.version('turbojev')}")
    print(f"  Host:              {platform.system()} {platform.machine()} · Python {platform.python_version()}")
    print(f"  Model load:        {load_seconds:.2f} s")
    print(f"  Game seed:         {seed}")
    print(f"  Score / food:      {score}")
    print(f"  First food turn:   {first_food_turn or '—'}")
    print(f"  Greedy reference:  {reference_score} food; first at turn {reference_first_food or '—'}")
    print(f"  Steps:             {step}")
    print(f"  Model decisions:   {len(latencies)}")
    print(f"  Forced moves:      {forced_moves}")
    print(f"  Game time:         {elapsed:.2f} s")
    if latencies:
        print(f"  Inference total:   {sum(latencies):.2f} s")
        print(f"  Latency mean:      {statistics.mean(latencies):.3f} s")
        print(f"  Latency median:    {statistics.median(latencies):.3f} s")
        print(f"  Latency p95:       {percentile(latencies, 0.95):.3f} s")
        print(f"  Decisions / sec:   {len(latencies) / sum(latencies):.2f}")
    description = "none (single pass; fastest)" if order_robustness == "none" else "cyclic (one order rotation per option)"
    print(f"  Order robustness:  {description}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Play Snake using TurboJev and a local GGUF model.")
    parser.add_argument("--model", help="Path to a GGUF model; alternatively set TURBOJEV_MODEL.")
    parser.add_argument("--max-turns", type=int, default=100, help="Maximum turns before the benchmark (default: 100).")
    parser.add_argument("--seed", type=int, default=0, help="Seed for reproducible food placement (default: 0).")
    parser.add_argument(
        "--order-robustness", choices=("none", "cyclic"), default="none",
        help="Option-order scoring mode (default: none; cyclic reduces order bias at extra cost).",
    )
    args = parser.parse_args()
    if args.max_turns < 1:
        parser.error("--max-turns must be at least 1")
    model = choose_model(args.model)
    reference_score, reference_first_food = greedy_reference(args.seed, args.max_turns)
    print(
        f"Seeded-board check: simple greedy reference reaches "
        f"{reference_score} food(s) in {args.max_turns} turns; "
        f"first at turn {reference_first_food or '—'}."
    )
    print("Loading model on CPU; set device='gpu' in snake.py to request GPU offload.")
    load_started = time.perf_counter()
    order_robustness = args.order_robustness
    execution = {"execution": {"orderRobustness": order_robustness}}
    with TurboJev.load(model, device="cpu", n_gpu_layers=0, **execution) as engine:
        load_seconds = time.perf_counter() - load_started
        print(f"Model ready in {load_seconds:.2f}s. Starting game...")
        play(
            engine, model, args.max_turns, load_seconds, order_robustness, args.seed,
            reference_score, reference_first_food,
        )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopped.")
