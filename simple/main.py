"""Three typed questions over one state, using the published TurboJev package."""
import json
import os
from pathlib import Path
import sys
import time
from urllib.request import urlopen

from turbojev import TurboJev


MODEL_URL = (
    "https://huggingface.co/bartowski/Qwen_Qwen3-0.6B-GGUF/resolve/main/"
    "Qwen_Qwen3-0.6B-Q4_K_M.gguf?download=true"
)


def model_path():
    if configured := os.getenv("TURBOJEV_MODEL"):
        model = Path(configured).expanduser().resolve()
        if not model.is_file():
            raise FileNotFoundError(f"Model not found: {model}")
        return str(model)

    model = Path.home() / ".cache" / "turbojev" / "Qwen3-0.6B-Q4_K_M.gguf"
    if model.is_file():
        return str(model)
    model.parent.mkdir(parents=True, exist_ok=True)
    temporary = model.with_suffix(".gguf.part")
    print("Downloading Qwen3 0.6B Q4_K_M (about 0.48 GB)...")
    try:
        with urlopen(MODEL_URL, timeout=60) as response, temporary.open("wb") as output:
            total = int(response.headers.get("Content-Length", "0"))
            received = 0
            while chunk := response.read(1024 * 1024):
                output.write(chunk)
                received += len(chunk)
                if total:
                    ratio = min(1.0, received / total)
                    filled = round(ratio * 28)
                    bar = "#" * filled + "-" * (28 - filled)
                    progress = f"[{bar}] {ratio:5.1%}  {received / 2**20:.0f}/{total / 2**20:.0f} MB"
                else:
                    progress = f"{received / 2**20:.0f} MB downloaded"
                sys.stdout.write(f"\rQwen3 0.6B {progress}")
                sys.stdout.flush()
            if not received or (total and received != total):
                raise RuntimeError("Incomplete model download; run again to retry.")
        temporary.replace(model)
    finally:
        temporary.unlink(missing_ok=True)
        print()
    return str(model)


def main():
    request = {
        "state": "Everything is down and we have a demo with our biggest client at noon.",
        "questions": {
            "urgent": {
                "type": "noul",
                "instructions": "Does the customer need a reply within the hour?",
            },
            "team": {
                "type": "choice",
                "instructions": "Which team should handle it?",
                "criteria": {
                    "outage": "service down",
                    "billing": "charges, refunds",
                    "feature": "requests, how-to",
                },
            },
            "tone": {
                "type": "score",
                "instructions": "How upset is the customer?",
                "criteria": ["calm", "annoyed", "furious"],
            },
        },
    }

    # CPU by default. Use device="gpu" to explicitly request GPU offload.
    # "none" scores once; "balanced" averages canonical choice probabilities;
    # "cyclic" averages rotation logits. Extra passes apply only to choices.
    with TurboJev.load(
        model_path(),
        device="cpu",
        thinking=False,
        execution={"orderRobustness": "none"},
    ) as client:
        start = time.perf_counter()
        response = client.evaluate(request)
        elapsed = time.perf_counter() - start

    answers = response["answers"]
    print(f"urgent: {answers['urgent']['noul']:.4f}")
    print(f"team:   {answers['team']['choice']} (confidence: {answers['team']['confidence']:.4f})")
    print(f"tone:   {answers['tone']['score']:.4f} (0=calm, 1=annoyed, 2=furious)")
    print(f"Evaluation: {elapsed:.3f} s")
    print("\nFull response:")
    print(json.dumps(response, indent=2))


if __name__ == "__main__":
    main()
