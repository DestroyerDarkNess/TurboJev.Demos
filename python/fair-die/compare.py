"""Standalone fair-die demo using the published TurboJev package."""

from pathlib import Path
import hashlib
import os
import sys
import time
from urllib.request import Request, urlopen
import argparse
import importlib.metadata
import json
import math
import platform
from turbojev import Dice, TurboJev

CACHE = Path.home() / ".cache" / "turbojev"


# Default text model: QJev3.5 0.8B v19c, standalone Q8_0 (811,843,104 bytes).
# Decision-trained weights; not a general extraction, reasoning or vision model.
# TurboJev uses its normal prompt/scoring path; upstream benchmark claims do not transfer.
# Alternatives (download locally and pass --model PATH; no automatic fallback):
# Jev-Style 2B v2 (letter scoring; requires its trained prompt)
# https://huggingface.co/chaoliangUNSW/Jev-Style-Qwen3.5-2B-Decision-v2-GGUF
# Jev-Style 0.8B v3 (requires a per-option verdict scorer)
# https://huggingface.co/chaoliangUNSW/Jev-Style-0.8B-Decision-v3-GGUF
# Jev-Style 2B v3 (requires block attention and a verdict scorer)
# https://huggingface.co/chaoliangUNSW/Jev-Style-2B-Decision-v3-GGUF
TEXT_MODEL_URL = "https://huggingface.co/ZY-Lee4/QJev3.5-0.8B-GGUF/resolve/008c7c7a5c35007b8ba6b06afba50f882f000667/qjev35-v19c-q8_0.gguf"
TEXT_MODEL_NAME = "qjev35-v19c-q8_0.gguf"
TEXT_MODEL_BYTES = 811843104
TEXT_MODEL_SHA256 = "7a5a50953df2fb866a2f39bc4ac8906084cac4e3a5fa8f04adc519058ceedf87"


def file_sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        while chunk := stream.read(2**20):
            digest.update(chunk)
    return digest.hexdigest()


def download(url, destination):
    destination = Path(destination).expanduser().resolve()
    if destination.exists():
        with destination.open("rb") as stream:
            if stream.read(4) != b"GGUF":
                raise ValueError(f"Not a GGUF file: {destination}")
        return destination
    destination.parent.mkdir(parents=True, exist_ok=True)
    partial = destination.with_suffix(destination.suffix + ".part")
    offset = partial.stat().st_size if partial.exists() else 0
    request = Request(url, headers={"Range": f"bytes={offset}-"} if offset else {})
    started = previous = time.monotonic()
    with urlopen(request, timeout=60) as response:
        if response.status != 206:
            offset = 0
        total = offset + int(response.headers.get("Content-Length", "0"))
        received = offset
        with partial.open("ab" if offset else "wb") as output:
            while chunk := response.read(2**20):
                output.write(chunk)
                received += len(chunk)
                now = time.monotonic()
                if now - previous < 0.2 and (not total or received < total):
                    continue
                previous = now
                speed = (received - offset) / max(0.001, now - started)
                ratio = min(1, received / total) if total else 0
                filled = round(ratio * 26)
                eta = (total - received) / speed if total and speed else 0
                percent = f"{ratio:5.1%}" if total else "      "
                sys.stdout.write(
                    f"\r{destination.name} [{'#' * filled}{'-' * (26 - filled)}] {percent} {received / 2**20:.0f} MB {speed / 2**20:.1f} MB/s ETA {eta:.0f}s    "
                )
                sys.stdout.flush()
    print()
    if not received or total and received != total:
        raise RuntimeError("Incomplete download; rerun to resume.")
    with partial.open("rb") as stream:
        if stream.read(4) != b"GGUF":
            partial.unlink()
            raise ValueError("The downloaded file is not GGUF.")
    partial.replace(destination)
    return destination


def text_model(model=None):
    if configured := model or os.getenv("TURBOJEV_MODEL"):
        path = Path(configured).expanduser().resolve()
        if not path.is_file():
            raise FileNotFoundError(path)
        return path
    path = download(TEXT_MODEL_URL, CACHE / TEXT_MODEL_NAME)
    if path.stat().st_size != TEXT_MODEL_BYTES or file_sha256(path) != TEXT_MODEL_SHA256:
        raise ValueError(
            "QJev model size or SHA-256 mismatch; remove the invalid cache file and retry."
        )
    return path


LABELS = ["one", "two", "three", "four", "five", "six"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model")
    parser.add_argument("--device", choices=["cpu", "gpu"], default="cpu")
    parser.add_argument(
        "--all-permutations",
        action="store_true",
        help="Include 720 real evaluations; potentially very slow",
    )
    parser.add_argument("--output", type=Path, default=Path(__file__).with_name("result.json"))
    args = parser.parse_args()
    model = text_model(args.model)
    print(f"TurboJev {importlib.metadata.version('turbojev')} | model: {model} | {args.device}")
    runs = {}
    with TurboJev.load(
        str(model), device=args.device, n_ctx=8192, n_seq_max=1, n_threads=4, n_threads_batch=4
    ) as client:
        for budget in [1, "auto", 8] + (["all"] if args.all_permutations else []):
            print(f"Evaluating permutation budget {budget}...", flush=True)
            start = time.perf_counter()
            response = client.generate(
                context="A single roll of a fair die.",
                mode="argmax",
                temperature=1,
                seed=42,
                questions={"roll": Dice(permutations=budget).to_schema()},
            )
            answer = response["result"]["roll"]
            probabilities = answer["probabilities"]
            if (
                set(probabilities) != set(LABELS)
                or any(not math.isfinite(p) or not 0 <= p <= 1 for p in probabilities.values())
                or not math.isclose(sum(probabilities.values()), 1, abs_tol=1e-9)
            ):
                raise ValueError("Invalid model distribution")
            divergence = (
                sum(math.log((1 / 6) / p) / 6 for p in probabilities.values())
                if all(probabilities.values())
                else None
            )
            runs[str(budget)] = {
                "response": response,
                "seconds": time.perf_counter() - start,
                "kl_uniform_to_prediction": divergence,
            }
            print(json.dumps(runs[str(budget)], indent=2))
    record = {
        "turbojev": importlib.metadata.version("turbojev"),
        "model": str(model),
        "model_sha256": file_sha256(model),
        "platform": platform.platform(),
        "architecture": platform.machine(),
        "device": args.device,
        "seed": 42,
        "ground_truth": dict.fromkeys(LABELS, 1 / 6),
        "runs": runs,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(f"Benchmark saved: {args.output}")


if __name__ == "__main__":
    main()
