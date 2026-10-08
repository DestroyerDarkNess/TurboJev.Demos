"""Play a small terminal Snake game with typed TurboJev choices."""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import math
import os
import platform
import random
import statistics
import sys
import time
from pathlib import Path
from urllib.request import urlopen

from turbojev import TurboJev, LoadOptions

try:
    from rich.console import Console
    from rich.live import Live
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text

    HAS_RICH = True
    console = Console()
except ImportError:
    HAS_RICH = False
    console = None


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
        if console:
            console.print(f"[dim]Using cached model: {cache}[/dim]")
        else:
            print(f"Using cached model: {cache}")
        return cache

    temporary = cache.with_suffix(cache.suffix + ".part")
    msg = f"Downloading {MODEL_NAME} from Hugging Face"
    if console:
        console.print(f"[cyan]{msg}[/cyan]")
    else:
        print(msg)
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
                    print(
                        f"\r[{bar}] {ratio:5.1%}  {received / 2**20:.0f}/{total / 2**20:.0f} MB",
                        end="",
                        flush=True,
                    )
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
    if configured:
        return configured
    if console:
        console.print("[bold cyan]TurboJev Snake[/bold cyan]")
        console.print(
            f"Default baseline (not qualified for navigation): [green]{MODEL_NAME}[/green]"
        )
        console.print("[dim]Use a local GGUF path for another llama.cpp-compatible model.[/dim]")
    else:
        print("TurboJev Snake")
        print(f"Default baseline (not qualified for navigation): {MODEL_NAME}")
        print("Use a local GGUF path for another llama.cpp-compatible model.")
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


def draw_legacy(snake: list[tuple[int, int]], food: tuple[int, int], score: int, step: int) -> None:
    cells = {point: "●" for point in snake[1:]}
    cells[snake[0]] = "◆"
    cells[food] = "★"
    print("\033[2J\033[H", end="")
    print(f"TurboJev Snake  ·  score {score}  ·  turn {step}  ·  food ★  snake ◆")
    print("┌" + "──" * WIDTH + "┐")
    for y in range(HEIGHT):
        print("│" + "".join(cells.get((x, y), "·") + " " for x in range(WIDTH)) + "│")
    print("└" + "──" * WIDTH + "┘")


def build_rich_view(
    snake: list[tuple[int, int]],
    food: tuple[int, int] | None,
    score: int,
    step: int,
    max_turns: int,
    last_decision: dict | None,
    latencies: list[float],
) -> Table:
    # Build Board Grid String
    cells = {point: "[bold green]●[/bold green]" for point in snake[1:]}
    if snake:
        cells[snake[0]] = "[bold bright_cyan]◆[/bold bright_cyan]"
    if food:
        cells[food] = "[bold bright_red]★[/bold bright_red]"

    board_lines = []
    for y in range(HEIGHT):
        line = " ".join(cells.get((x, y), "[dim]·[/dim]") for x in range(WIDTH))
        board_lines.append(f"  {line}")

    board_content = "\n".join(board_lines)
    board_panel = Panel(
        Text.from_markup(board_content),
        title=f"[bold cyan]🐍 Board[/bold cyan] [yellow]Turn {step}/{max_turns}[/yellow] [bold gold1]Score: {score} ★[/bold gold1]",
        border_style="cyan",
        padding=(1, 1),
    )

    # Build Telemetry Panel
    telemetry_texts = []
    if last_decision:
        state_txt = last_decision.get("state", "Starting...")
        choice = last_decision.get("choice", "—")
        probs = last_decision.get("probabilities", {})
        latency = last_decision.get("latency")

        telemetry_texts.append(f"[bold]State:[/bold] [dim]{state_txt}[/dim]")
        color_tag = {"up": "cyan", "down": "yellow", "left": "magenta", "right": "green"}.get(
            choice, "white"
        )
        telemetry_texts.append(
            f"[bold]TurboJev move:[/bold] [{color_tag} bold]{choice.upper()}[/{color_tag} bold]"
        )

        # Probability Bars
        telemetry_texts.append("\n[bold]Move probabilities:[/bold]")
        for move in ("up", "down", "left", "right"):
            if move not in probs:
                continue
            p = probs[move]
            bar_len = round(p * 16)
            bar_str = "█" * bar_len + "░" * (16 - bar_len)
            c = {"up": "cyan", "down": "yellow", "left": "magenta", "right": "green"}[move]
            telemetry_texts.append(f"  {move.capitalize():<13} [{c}]{bar_str}[/{c}] {p:>4.0%}")

        if latency is not None:
            telemetry_texts.append(
                f"\n[bold]⚡ Step Latency:[/bold] [cyan]{latency * 1000:.1f} ms[/cyan]"
            )
        else:
            telemetry_texts.append("\n[bold]Step latency:[/bold] [dim]Not available[/dim]")
    else:
        telemetry_texts.append("[dim]Waiting for first turn...[/dim]")

    if latencies:
        mean_ms = statistics.mean(latencies) * 1000
        p95_ms = percentile(latencies, 0.95) * 1000
        dps = len(latencies) / max(0.0001, sum(latencies))
        telemetry_texts.append(
            f"[bold]Mean Latency:[/bold] {mean_ms:.1f} ms  [dim](p95: {p95_ms:.1f} ms)[/dim]"
        )
        telemetry_texts.append(f"[bold]Speed:[/bold] {dps:.1f} decisions/s")

    telemetry_panel = Panel(
        Text.from_markup("\n".join(telemetry_texts)),
        title="[bold magenta]⚡ TurboJev AI Telemetry[/bold magenta]",
        border_style="magenta",
        padding=(0, 1),
    )

    container = Table.grid(padding=1)
    container.add_column(no_wrap=True)
    container.add_column(no_wrap=True)
    container.add_row(board_panel, telemetry_panel)
    return container


def percentile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, math.ceil(fraction * len(ordered)) - 1)]


def make_move_request(snake, direction, food, state_format="sensors"):
    """Prepare observations; sensors derives collision facts, never an action or path."""
    if state_format == "sensors":
        x, y = snake[0]
        vertical = "up" if food[1] < y else "down" if food[1] > y else None
        horizontal = "left" if food[0] < x else "right" if food[0] > x else None
        food_direction = " and ".join(value for value in (vertical, horizontal) if value)
        blocked, clear = [], []
        for move in DIRECTIONS:
            # The same rules as the game expose immediate collisions. Every
            # direction remains a model candidate, including blocked directions.
            _, _, collision = apply_move(snake, direction, food, move)
            (blocked if collision else clear).append(move)
        state = (
            f"Food direction: {food_direction}.\n"
            f"Blocked directions: {', '.join(blocked) or 'none'}.\n"
            f"Clear directions: {', '.join(clear) or 'none'}."
        )
        return {
            "state": state,
            "questions": {
                "move": {
                    "type": "choice",
                    "instructions": "Move toward the food. Choose a clear direction. Never choose a blocked direction.",
                    "criteria": {move: f"Move {move}." for move in DIRECTIONS},
                }
            },
        }
    elif state_format == "coordinates":
        state = (
            f"Board: {WIDTH} columns and {HEIGHT} rows. Coordinates are (x, y); "
            "x increases to the right and y increases downward. "
            f"Head: {snake[0]}. Body from neck to tail: {snake[1:]}. "
            f"Food: {food}. Current direction: {direction}."
        )
    elif state_format == "grid":
        rows = [["." for _ in range(WIDTH)] for _ in range(HEIGHT)]
        for x, y in snake[1:]:
            rows[y][x] = "B"
        if len(snake) > 1:
            rows[snake[-1][1]][snake[-1][0]] = "T"
        rows[food[1]][food[0]] = "F"
        rows[snake[0][1]][snake[0][0]] = "H"
        state = (
            f"Snake board: {WIDTH} columns, {HEIGHT} rows. Read rows from top to bottom "
            "and columns from left to right. H = head, B = body, T = tail, F = food, . = empty. "
            "The outside of this board is a wall.\n"
            + "\n".join(" ".join(row) for row in rows)
            + f"\nCurrent direction: {direction}."
        )
    else:
        raise ValueError("state_format must be sensors, grid or coordinates")
    return {
        "state": state,
        "questions": {
            "move": {
                "type": "choice",
                "instructions": (
                    "Choose the snake's next move to reach the food. Move one cell only. "
                    "Avoid leaving the board or entering the body. Do not reverse directly. "
                    "The tail vacates its cell unless the snake eats. Choose a direction, not a plan."
                )
                if state_format == "grid"
                else (
                    "Choose the next direction for the snake to reach the food. "
                    "Avoid the board walls and the snake's body; do not reverse directly. "
                    "The tail moves away unless the snake eats. Decide this move only."
                ),
                "criteria": {
                    "up": "Move one cell up (toward the previous row)."
                    if state_format == "grid"
                    else "Move one cell up (y - 1).",
                    "down": "Move one cell down (toward the next row)."
                    if state_format == "grid"
                    else "Move one cell down (y + 1).",
                    "left": "Move one cell left (toward the previous column)."
                    if state_format == "grid"
                    else "Move one cell left (x - 1).",
                    "right": "Move one cell right (toward the next column)."
                    if state_format == "grid"
                    else "Move one cell right (x + 1).",
                },
            }
        },
    }


def jev_choose_move(
    engine: TurboJev,
    snake: list[tuple[int, int]],
    direction: str,
    food: tuple[int, int],
    state_format: str = "sensors",
) -> tuple[str, dict, float]:
    request = make_move_request(snake, direction, food, state_format)
    state = request["state"]
    started = time.perf_counter()
    response = engine.evaluate(request)
    latency = time.perf_counter() - started
    answer = response["answers"]["move"]
    move = answer.get("choice")
    if answer.get("type") != "choice" or move not in DIRECTIONS:
        raise RuntimeError(
            f"Invalid TurboJev direction response: {answer!r}. No fallback move was applied."
        )
    decision = {
        "state": state,
        "choice": move,
        "probabilities": answer.get("probabilities") or {},
        "latency": latency,
        "request": request,
        "response": response,
    }
    return move, decision, latency


def apply_move(
    snake: list[tuple[int, int]],
    direction: str,
    food: tuple[int, int],
    move: str,
) -> tuple[list[tuple[int, int]], bool, str | None]:
    """Apply game physics to the model's exact choice; collisions end the game."""
    dx, dy = DIRECTIONS[move]
    target = (snake[0][0] + dx, snake[0][1] + dy)
    if len(snake) > 1 and move == OPPOSITE[direction]:
        return snake, False, "model selected a direct reversal"
    if not (0 <= target[0] < WIDTH and 0 <= target[1] < HEIGHT):
        return snake, False, "model hit a wall"
    ate = target == food
    occupied = snake if ate else snake[:-1]
    if target in occupied:
        return snake, False, "model hit the snake body"
    return [target, *(snake if ate else snake[:-1])], ate, None


def play(
    engine: TurboJev,
    model: str,
    max_turns: int,
    load_seconds: float,
    order_robustness: str,
    seed: int,
    trace_path: Path,
    state_format: str = "sensors",
    thinking: bool = False,
) -> dict:
    rng = random.Random(seed)
    snake = [(WIDTH // 2, HEIGHT // 2), (WIDTH // 2 - 1, HEIGHT // 2)]
    direction = "right"
    food = spawn_food(snake, rng)
    assert food is not None
    score = 0
    first_food_turn: int | None = None
    latencies: list[float] = []
    steps = 0
    game_started = time.perf_counter()
    game_over = "turn limit reached"
    last_decision: dict | None = None
    trace_path.parent.mkdir(parents=True, exist_ok=True)
    live = Live(console=console, refresh_per_second=15) if HAS_RICH and console else None

    with trace_path.open("w", encoding="utf-8") as trace:

        def record(event: dict) -> None:
            trace.write(json.dumps(event) + "\n")
            trace.flush()

        record(
            {
                "event": "start",
                "model": model,
                "turbojev": importlib.metadata.version("turbojev"),
                "seed": seed,
                "order_robustness": order_robustness,
                "state_format": state_format,
                "thinking": thinking,
                "host_observation_preprocessing": "relative food direction and immediate collision facts"
                if state_format == "sensors"
                else "board serialization",
            }
        )
        if live:
            live.start()
        try:
            for step in range(1, max_turns + 1):
                if live:
                    live.update(
                        build_rich_view(
                            snake, food, score, step, max_turns, last_decision, latencies
                        )
                    )
                else:
                    draw_legacy(snake, food, score, step)
                before = list(snake)
                food_before = food
                move, last_decision, latency = jev_choose_move(
                    engine, snake, direction, food, state_format
                )
                latencies.append(latency)
                snake, ate, collision = apply_move(snake, direction, food, move)
                record(
                    {
                        "event": "decision",
                        "turn": step,
                        "snake_before": before,
                        "food": food_before,
                        "request": last_decision["request"],
                        "response": last_decision["response"],
                        "model_choice": move,
                        "applied_choice": move,
                        "latency_s": latency,
                        "snake_after": snake,
                        "ate": ate,
                        "collision": collision,
                    }
                )
                if collision:
                    game_over = collision
                    break
                direction = move
                steps += 1
                if ate:
                    score += 1
                    first_food_turn = first_food_turn or step
                    food = spawn_food(snake, rng)
                    if food is None:
                        game_over = "board filled"
                        break
                time.sleep(0.10)
            if live:
                live.update(
                    build_rich_view(snake, food, score, step, max_turns, last_decision, latencies)
                )
            else:
                draw_legacy(snake, food if food is not None else snake[0], score, step)
        except Exception as error:
            record({"event": "error", "turn": step, "error": str(error)})
            raise
        finally:
            if live:
                live.stop()
        summary = {
            "event": "benchmark",
            "model": Path(model).name,
            "turbojev": importlib.metadata.version("turbojev"),
            "host": f"{platform.system()} {platform.machine()} · Python {platform.python_version()}",
            "model_load_s": load_seconds,
            "seed": seed,
            "score": score,
            "first_food_turn": first_food_turn,
            "executed_steps": steps,
            "model_decisions": len(latencies),
            "host_selected_moves": 0,
            "game_time_s": time.perf_counter() - game_started,
            "inference_total_s": sum(latencies),
            "order_robustness": order_robustness,
            "state_format": state_format,
            "host_observation_preprocessing": "relative food direction and immediate collision facts"
            if state_format == "sensors"
            else "board serialization",
            "end_reason": game_over,
            "trace": str(trace_path.resolve()),
        }
        if latencies:
            summary.update(
                latency_mean_ms=statistics.mean(latencies) * 1000,
                latency_median_ms=statistics.median(latencies) * 1000,
                latency_p95_ms=percentile(latencies, 0.95) * 1000,
                decisions_per_s=len(latencies) / max(sum(latencies), 1e-9),
            )
        record(summary)

    if console:
        bench_table = Table(title="TurboJev Snake benchmark", border_style="cyan")
        bench_table.add_column("Metric", style="bold cyan")
        bench_table.add_column("Value")
        for key, value in summary.items():
            if key != "event":
                bench_table.add_row(key.replace("_", " "), str(value))
        console.print(bench_table)
    else:
        print("Benchmark")
        print(json.dumps(summary, indent=2))
    return summary


def main() -> None:
    # Redirected Windows consoles otherwise use cp1252 and cannot print the board.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(
        description="Play Snake using TurboJev and a local GGUF model."
    )
    parser.add_argument("--model", help="Path to a GGUF model; alternatively set TURBOJEV_MODEL.")
    parser.add_argument(
        "--max-turns",
        type=int,
        default=100,
        help="Maximum turns before the benchmark (default: 100).",
    )
    parser.add_argument(
        "--seed", type=int, default=0, help="Seed for reproducible food placement (default: 0)."
    )
    parser.add_argument(
        "--order-robustness",
        choices=("none", "cyclic", "balanced"),
        default="none",
        help="Option-order mode: none (one pass), cyclic (rotations), balanced (canonical probability mean; extra passes).",
    )
    parser.add_argument(
        "--trace",
        type=Path,
        help="JSONL audit file; defaults to a timestamped file under .artifacts/.",
    )
    parser.add_argument(
        "--state-format",
        choices=["sensors", "grid", "coordinates"],
        default="sensors",
        help="sensors derives food direction and collision facts; grid/coordinates expose the board directly",
    )
    parser.add_argument(
        "--thinking",
        action="store_true",
        help="Native model reasoning, off by default; requires a supporting TurboJev release",
    )
    parser.add_argument("--max-thinking-tokens", type=int, default=512)
    args = parser.parse_args()
    if args.thinking and "thinking" not in LoadOptions.__dataclass_fields__:
        parser.error(
            "--thinking requires a published TurboJev package with native reasoning support; the installed package does not provide it yet"
        )
    if args.max_turns < 1:
        parser.error("--max-turns must be at least 1")
    model = choose_model(args.model)
    trace_path = args.trace or Path(".artifacts") / f"snake-{time.time_ns()}.jsonl"
    print(
        "Every direction comes from TurboJev. Invalid moves end the game; no host rescue is used."
    )
    if args.state_format == "sensors":
        print(
            "Sensors prepare relative food direction and immediate collision facts; the model chooses the move."
        )
    print("Loading model on CPU.")
    load_started = time.perf_counter()
    order_robustness = args.order_robustness
    execution = {"execution": {"orderRobustness": order_robustness}}
    thinking_options = (
        {"thinking": True, "max_thinking_tokens": args.max_thinking_tokens} if args.thinking else {}
    )
    with TurboJev.load(
        model, device="cpu", n_gpu_layers=0, n_seq_max=4, **execution, **thinking_options
    ) as engine:
        load_seconds = time.perf_counter() - load_started
        if console:
            console.print(
                f"[bold green]Model ready in {load_seconds:.2f}s. Starting game...[/bold green]\n"
            )
        else:
            print(f"Model ready in {load_seconds:.2f}s. Starting game...")
        play(
            engine,
            model,
            args.max_turns,
            load_seconds,
            order_robustness,
            args.seed,
            trace_path,
            args.state_format,
            args.thinking,
        )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopped.")
