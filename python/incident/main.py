"""incident: standalone TurboJev port of the TypeLLM example."""

from __future__ import annotations

import argparse
import copy
import dataclasses
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import struct
import sys
import time
from urllib.request import urlopen

from turbojev import TurboJev, compile_json_schema

VERSION = "0.33.0"
SOURCE = "https://typellm.ai/examples/incident"
MODEL_NAME = "Qwen3-0.6B-Q4_K_M.gguf"
MODEL_URL = (
    "https://huggingface.co/bartowski/Qwen_Qwen3-0.6B-GGUF/resolve/"
    "60b85c0e3d8fe0f6474f406922a26d12aca4550d/" + MODEL_NAME
)
MODEL_BYTES = 484220320
MODEL_SHA256 = "9acfc1e001311f34b4252001b626f2e466d592a42065f66571bff3790d4e1b14"
FOLDER = Path(__file__).resolve().parent

# The model produces every answer. The host never substitutes expected results.
REQUEST = {
    "context": "Alert at 14:02: checkout API error rate 38% (normal: under 1%) since the 13:55 "
    "deploy of payments-service v2.14. p95 latency 4.1 s. About 1,200 customers "
    "affected so far.",
    "questions": {
        "severity": {
            "type": "string",
            "enum": ["low", "medium", "high", "critical"],
            "instructions": "How severe is this incident?",
        },
        "roll_back": {
            "type": "boolean",
            "depends_on": ["severity"],
            "instructions": "Given the incident and its severity, should the "
            "deploy be rolled back now?",
        },
        "status_message": {
            "type": "string",
            "depends_on": ["severity", "roll_back"],
            "instructions": "One sentence for the status page, saying "
            "what is affected and what is being done.",
        },
    },
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def model_path(custom: str | None) -> Path:
    if custom:
        path = Path(custom).expanduser().resolve()
        if not path.is_file():
            raise FileNotFoundError(f"Model not found: {path}")
        return path

    path = Path.home() / ".cache" / "turbojev" / MODEL_NAME
    if path.is_file() and path.stat().st_size == MODEL_BYTES:
        if sha256(path) == MODEL_SHA256:
            print(f"Model cache hit: {path}")
            return path

    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_suffix(".gguf.part")
    started = time.perf_counter()
    received = 0
    last_update = 0.0
    with urlopen(MODEL_URL, timeout=60) as response, partial.open("wb") as output:
        total = int(response.headers.get("Content-Length", MODEL_BYTES))
        while chunk := response.read(1024 * 1024):
            output.write(chunk)
            received += len(chunk)
            now = time.perf_counter()
            if now - last_update >= 0.15 or received == total:
                elapsed = max(now - started, 0.001)
                speed = received / elapsed
                ratio = min(received / total, 1.0)
                bar = "#" * int(ratio * 30) + "-" * (30 - int(ratio * 30))
                eta = max(total - received, 0) / speed
                print(
                    f"\r[{bar}] {ratio:6.1%}  "
                    f"{received / 2**20:.1f}/{total / 2**20:.1f} MiB  "
                    f"{speed / 2**20:.1f} MiB/s  ETA {eta:.0f}s",
                    end="",
                    flush=True,
                )
                last_update = now
    print()
    if received != MODEL_BYTES or sha256(partial) != MODEL_SHA256:
        raise ValueError("Model download size or SHA-256 mismatch; rerun to download again.")
    partial.replace(path)
    return path


def configure_fields(value: object, thinking: str, permutations: str | None) -> None:
    if isinstance(value, list):
        for child in value:
            configure_fields(child, thinking, permutations)
    elif isinstance(value, dict):
        if "type" in value and value["type"] not in ("object", "array"):
            if thinking != "example":
                for key in ("thinking", "thinking_effort", "thinking_budget"):
                    value.pop(key, None)
                if thinking == "off":
                    value["thinking"] = False
                elif thinking == "auto":
                    value["thinking"] = "auto"
                else:
                    value["thinking_effort"] = thinking
            if permutations is not None and (
                "enum" in value or "choices" in value or value["type"] == "boolean"
            ):
                value["permutations"] = (
                    permutations if permutations in ("auto", "all") else int(permutations)
                )
        for key in ("properties", "items"):
            if key in value:
                children = value[key]
                if key == "properties":
                    for child in children.values():
                        configure_fields(child, thinking, permutations)
                else:
                    # Object-array rows are decoded as a single JSON object.
                    # Their property-level reasoning/permutation options are unsupported.
                    if children.get("type") != "object":
                        configure_fields(children, thinking, permutations)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default=os.environ.get("TURBOJEV_MODEL"))
    parser.add_argument("--device", choices=("cpu", "gpu"), default="cpu")
    parser.add_argument("--context", help="Replace the example's input text.")
    parser.add_argument(
        "--thinking", choices=("example", "off", "auto", "low", "medium", "high"), default="example"
    )
    parser.add_argument("--permutations", help="Override finite-field budgets: 1, auto, 8 or all.")
    parser.add_argument("--max-tokens", type=int, default=256)
    parser.add_argument("--timeout", type=float, default=300)
    parser.add_argument("--output", type=Path, default=FOLDER / "result.json")
    parser.add_argument(
        "--dry-run", action="store_true", help="Compile the schema without loading a model."
    )
    args = parser.parse_args()
    if args.max_tokens < 1 or args.timeout <= 0:
        parser.error("Token limit and timeout must be positive.")
    if args.permutations is not None and args.permutations not in ("auto", "all"):
        if not args.permutations.isdecimal() or not 1 <= int(args.permutations) <= 720:
            parser.error("Permutation budget must be auto, all, or an integer from 1 to 720.")

    request = copy.deepcopy(REQUEST)
    if args.context is not None:
        request["context"] = args.context
    for field in request["questions"].values():
        configure_fields(field, args.thinking, args.permutations)
    request.update(
        mode="argmax",
        temperature=0,
        seed=42,
        text_max_tokens=args.max_tokens,
        numeric_max_tokens=args.max_tokens,
    )
    report = {
        "demo": "incident",
        "source": SOURCE,
        "package_version": importlib.metadata.version("turbojev"),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "python_bits": struct.calcsize("P") * 8,
        "device": args.device,
        "request": request,
    }
    try:
        if report["package_version"] != VERSION:
            raise RuntimeError(f"Install the demo requirements; expected TurboJev {VERSION}.")
        compiled = compile_json_schema({"type": "object", "properties": request["questions"]})
        print(
            f"TurboJev {VERSION} | incident | {args.device} | {len(compiled)} compiled fields",
            flush=True,
        )
        if args.dry_run:
            print(json.dumps(request, indent=2))
            return 0
        model = model_path(args.model)
        report.update(model=str(model), model_sha256=sha256(model))
        print(f"Model: {model.name}", flush=True)
        started = time.perf_counter()
        with TurboJev.load(
            str(model),
            device=args.device,
            n_gpu_layers=-1 if args.device == "gpu" else 0,
            n_threads=4,
            n_ctx=16384,
            n_seq_max=1,
            execution={"policy": "reference", "orderRobustness": "none"},
        ) as client:
            report["load_seconds"] = time.perf_counter() - started
            started = time.perf_counter()
            print("Evaluating workflow; thinking and permutations add model work...", flush=True)
            report["response"] = client.generate(request, timeout=args.timeout)
            report["inference_seconds"] = time.perf_counter() - started
        print(json.dumps(report["response"], indent=2))
        print(
            f"Decision workflow: {report['inference_seconds']:.3f}s; load: {report['load_seconds']:.3f}s"
        )
        result = 0
    except Exception as error:
        report["error"] = {"type": type(error).__name__, "message": str(error)}
        usage = getattr(error, "usage", None)
        if usage is not None:
            report["error"]["usage"] = (
                dataclasses.asdict(usage) if dataclasses.is_dataclass(usage) else usage
            )
        print(f"Error: {error}", file=sys.stderr)
        result = 1
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, default=str) + "\n", encoding="utf-8")
    print(f"Report: {args.output.resolve()}")
    return result


if __name__ == "__main__":
    raise SystemExit(main())
