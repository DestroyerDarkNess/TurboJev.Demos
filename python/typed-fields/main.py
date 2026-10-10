"""Self-contained published-package ticket, fields, fair-die and receipt examples."""

from pathlib import Path
import hashlib
import os
import sys
import time
from urllib.request import Request, urlopen
import argparse
import importlib.metadata
import json
import platform
from turbojev import Dice, TurboJev
import math
import base64

FOLDER = Path(__file__).resolve().parent

CACHE = Path.home() / ".cache" / "turbojev"


TEXT_MODEL_URL = "https://huggingface.co/bartowski/Qwen_Qwen3-0.6B-GGUF/resolve/60b85c0e3d8fe0f6474f406922a26d12aca4550d/Qwen_Qwen3-0.6B-Q4_K_M.gguf"


VISION_REVISION = "f6d5376be1edb4d416d56da11e5397a961aca8ae"


VISION_BASE = f"https://huggingface.co/unsloth/Qwen3.5-2B-GGUF/resolve/{VISION_REVISION}/"


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
    return download(TEXT_MODEL_URL, CACHE / "Qwen3-0.6B-Q4_K_M.gguf")


def vision_models(model=None, mmproj=None):
    model = (
        Path(model).expanduser().resolve()
        if model
        else download(VISION_BASE + "Qwen3.5-2B-Q4_K_M.gguf", CACHE / "Qwen3.5-2B-Q4_K_M.gguf")
    )
    projector = (
        Path(mmproj).expanduser().resolve()
        if mmproj
        else download(VISION_BASE + "mmproj-F16.gguf", CACHE / "Qwen3.5-2B-mmproj-F16.gguf")
    )
    if not model.is_file() or not projector.is_file():
        raise FileNotFoundError("Provide an existing model and matching projector.")
    return model, projector


LABELS = ["one", "two", "three", "four", "five", "six"]


def matched(actual, expected):
    if isinstance(expected, bool):
        return type(actual) is bool and actual is expected
    if isinstance(expected, (int, float)):
        return type(actual) in (int, float) and math.isclose(
            actual, expected, abs_tol=1e-6, rel_tol=1e-6
        )
    return type(actual) is type(expected) and actual == expected


def run_receipt(folder, bundled=False, argv=None):
    parser = argparse.ArgumentParser(
        description="Extract a photographed receipt with the published TurboJev GGUF runtime."
    )
    parser.add_argument(
        "--image",
        type=Path,
        default=folder / "receipt.jpg" if bundled else None,
        required=not bundled,
    )
    parser.add_argument("--model", help="Vision GGUF model; default Qwen3.5 2B Q4_K_M")
    parser.add_argument("--mmproj", help="Matching vision projector; default Qwen3.5 2B F16")
    parser.add_argument("--device", choices=["cpu", "gpu"], default="cpu")
    parser.add_argument("--fields", help="Comma-separated subset; dependencies are included")
    parser.add_argument(
        "--reference-labels",
        action="store_true",
        help="Compare with the original example's labels only when using that exact reference image",
    )
    parser.add_argument("--max-tokens", type=int, default=64)
    parser.add_argument(
        "--output",
        type=Path,
        default=FOLDER / ("result-receipt.json" if bundled else "result-receipt-us.json"),
    )
    args = parser.parse_args(argv)
    if not args.image.is_file() or not 0 < args.image.stat().st_size <= 24 * 2**20:
        parser.error("Provide a nonempty image of at most 24 MiB.")
    if not 1 <= args.max_tokens <= 32768:
        parser.error("max-tokens must be between 1 and 32768")
    questions = json.loads((folder / "questions.json").read_text(encoding="utf-8"))
    if args.fields:
        names = set(args.fields.split(","))
        if names - set(questions):
            parser.error("Unknown field names: " + ", ".join(sorted(names - set(questions))))
        while True:
            expanded = names | {
                dep for name in names for dep in questions[name].get("depends_on", [])
            }
            if expanded == names:
                break
            names = expanded
        questions = {name: field for name, field in questions.items() if name in names}
    use_labels = (
        args.reference_labels
        or bundled
        and args.image.resolve() == (folder / "receipt.jpg").resolve()
    )
    expected = (
        json.loads((folder / "expected.json").read_text(encoding="utf-8")) if use_labels else {}
    )
    expected = {name: value for name, value in expected.items() if name in questions}
    model, mmproj = vision_models(args.model, args.mmproj)
    print(
        f"TurboJev {importlib.metadata.version('turbojev')} | {model.name} + {mmproj.name} | {args.device}"
    )
    print(
        f"Reading {args.image.name}: {len(questions)} fields; values and dependent calculations are model-generated.",
        flush=True,
    )
    evidence = args.image.read_bytes()
    request = {
        "context": {
            "contract": "turbojev.media.v1",
            "modality": "image",
            "text": "Read the attached photo of a restaurant receipt.",
            "base64": base64.b64encode(evidence).decode(),
        },
        "questions": questions,
        "thinking": False,
        "text_max_tokens": args.max_tokens,
        "numeric_max_tokens": args.max_tokens,
    }
    load_started = time.perf_counter()
    response = None
    failure = None
    load_seconds = None
    started = load_started
    try:
        with TurboJev.load(
            str(model),
            mmproj=str(mmproj),
            device=args.device,
            n_ctx=8192,
            n_seq_max=1,
            n_threads=4,
            n_threads_batch=4,
        ) as client:
            load_seconds = time.perf_counter() - load_started
            started = time.perf_counter()
            response = client.generate(request)
    except Exception as error:
        failure = str(error)
    seconds = time.perf_counter() - started
    result = response["result"] if response is not None else {}
    checks = {name: matched(result.get(name), value) for name, value in expected.items()}
    record = {
        "turbojev": importlib.metadata.version("turbojev"),
        "model": str(model),
        "mmproj": str(mmproj),
        "device": args.device,
        "model_sha256": file_sha256(model),
        "mmproj_sha256": file_sha256(mmproj),
        "platform": platform.platform(),
        "architecture": platform.machine(),
        "image_sha256": hashlib.sha256(evidence).hexdigest(),
        "fields": list(questions),
        "subset": bool(args.fields),
        "max_tokens": args.max_tokens,
        "thinking": False,
        "load_seconds": load_seconds,
        "evaluation_seconds": seconds,
        "response": response,
        "expected": expected,
        "matches": checks,
        "ok": failure is None,
        "error": failure,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    if failure is not None:
        print(f"Generation failed: {failure}\nBenchmark saved: {args.output}")
        raise SystemExit(2)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    if checks:
        print(f"Reference labels: {sum(checks.values())}/{len(checks)} fields match")
    print(
        f"Load: {load_seconds:.3f}s | Evaluation: {seconds:.3f}s | {seconds / len(result):.3f}s per returned field (aggregate)"
    )
    print(f"Benchmark saved: {args.output}")


def run_fair_die(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model")
    parser.add_argument("--device", choices=["cpu", "gpu"], default="cpu")
    parser.add_argument(
        "--all-permutations",
        action="store_true",
        help="Include 720 real evaluations; potentially very slow",
    )
    parser.add_argument("--output", type=Path, default=FOLDER / "result-fair-die.json")
    args = parser.parse_args(argv)
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


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "fair-die":
        run_fair_die(sys.argv[2:])
        return
    if len(sys.argv) > 1 and sys.argv[1] in {"receipt", "receipt-us"}:
        bundled = sys.argv[1] == "receipt"
        run_receipt(
            FOLDER / "receipts" / ("cord" if bundled else "us"), bundled=bundled, argv=sys.argv[2:]
        )
        return
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "example",
        choices=[
            "ticket",
            "fields",
            "structured",
            "hierarchical",
            "discover-categories",
            "dice",
            "limits",
            "fair-die",
            "receipt",
            "receipt-us",
        ],
        nargs="?",
        default="ticket",
    )
    parser.add_argument("--device", choices=["cpu", "gpu"], default="cpu")
    parser.add_argument("--model")
    parser.add_argument("--max-tokens", type=int, default=64)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if not 1 <= args.max_tokens <= 32768:
        parser.error("max-tokens must be 1–32768")
    request = json.loads((FOLDER / "requests" / f"{args.example}.json").read_text())
    if args.example == "fields":
        request.update(text_max_tokens=args.max_tokens, numeric_max_tokens=args.max_tokens)
    record = dict(
        example=args.example,
        package_version=importlib.metadata.version("turbojev"),
        architecture=platform.machine(),
        platform=platform.platform(),
        device=args.device,
    )
    try:
        model = text_model(args.model)
        record.update(model=str(model), model_sha256=file_sha256(model))
        start = time.perf_counter()
        # evaluate: balanced averages canonical probabilities; cyclic averages rotation logits.
        # Both cost extra choice passes. generate: permutations is per field.
        with TurboJev.load(
            str(model),
            device=args.device,
            n_ctx=8192,
            n_seq_max=1,
            n_threads=4,
            n_threads_batch=4,
            execution={"orderRobustness": "none"},
        ) as engine:
            record["load_seconds"] = time.perf_counter() - start
            start = time.perf_counter()
            record["response"] = (
                engine.evaluate(request) if args.example == "ticket" else engine.generate(request)
            )
            record["evaluation_seconds"] = time.perf_counter() - start
        record.update(ok=True, error=None)
        print(json.dumps(record["response"], indent=2))
        print(f"Evaluation: {record['evaluation_seconds']:.3f}s")
    except Exception as error:
        record.update(ok=False, error=str(error))
    output = args.output or Path(f"result-{args.example}.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(f"Report saved: {output.resolve()}")
    if not record["ok"]:
        print(record["error"], file=sys.stderr)
        raise SystemExit(2)


if __name__ == "__main__":
    main()
