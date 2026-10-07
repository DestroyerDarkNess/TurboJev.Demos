"""Published-package examples: ticket, typed fields, fair die and image receipts."""
import argparse
import importlib.metadata
import json
from pathlib import Path
import platform
import runpy
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from demos_common import text_model, file_sha256
from turbojev import TurboJev


def main():
    forwarded = {"fair-die": "fair-die-python", "receipt": "receipt-python", "receipt-us": "receipt-us-python"}
    if len(sys.argv) > 1 and sys.argv[1] in forwarded:
        example = sys.argv.pop(1)
        sys.argv[0] = str(ROOT / forwarded[example] / "main.py")
        runpy.run_path(sys.argv[0], run_name="__main__")
        return
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("example", choices=["ticket", "fields", *forwarded], nargs="?", default="ticket")
    parser.add_argument("--device", choices=["cpu", "gpu"], default="cpu")
    parser.add_argument("--model")
    parser.add_argument("--max-tokens", type=int, default=64)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if not 1 <= args.max_tokens <= 32768:
        parser.error("max-tokens must be 1–32768")
    request = json.loads((ROOT / "demo-requests" / f"{args.example}.json").read_text())
    if args.example == "fields":
        request.update(text_max_tokens=args.max_tokens, numeric_max_tokens=args.max_tokens)
    record = dict(example=args.example, package_version=importlib.metadata.version("turbojev"),
                  architecture=platform.machine(), platform=platform.platform(), device=args.device)
    try:
        model = text_model(args.model)
        record.update(model=str(model), model_sha256=file_sha256(model))
        start = time.perf_counter()
        # evaluate: cyclic averages extra candidate rotations. generate: permutations is per field.
        with TurboJev.load(str(model), device=args.device, n_ctx=8192, n_seq_max=1, n_threads=4,
                           n_threads_batch=4, execution={"orderRobustness": "none"}) as engine:
            record["load_seconds"] = time.perf_counter() - start
            start = time.perf_counter()
            record["response"] = engine.evaluate(request) if args.example == "ticket" else engine.generate(request)
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
