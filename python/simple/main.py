"""Three typed questions over one state, using the published TurboJev package."""

import json
import hashlib
import os
from pathlib import Path
import sys
import time
from urllib.request import urlopen

from turbojev import TurboJev


# Default text model: QJev3.5 0.8B v19c, standalone Q8_0 (811,843,104 bytes).
# Decision-trained weights; not a general extraction, reasoning or vision model.
# TurboJev uses its normal prompt/scoring path; upstream benchmark claims do not transfer.
# Alternatives (download locally and set TURBOJEV_MODEL; no automatic fallback):
# Jev-Style 2B v2 (letter scoring; requires its trained prompt)
# https://huggingface.co/chaoliangUNSW/Jev-Style-Qwen3.5-2B-Decision-v2-GGUF
# Jev-Style 0.8B v3 (requires a per-option verdict scorer)
# https://huggingface.co/chaoliangUNSW/Jev-Style-0.8B-Decision-v3-GGUF
# Jev-Style 2B v3 (requires block attention and a verdict scorer)
# https://huggingface.co/chaoliangUNSW/Jev-Style-2B-Decision-v3-GGUF
MODEL_URL = "https://huggingface.co/ZY-Lee4/QJev3.5-0.8B-GGUF/resolve/008c7c7a5c35007b8ba6b06afba50f882f000667/qjev35-v19c-q8_0.gguf"
MODEL_FILE = "qjev35-v19c-q8_0.gguf"
MODEL_BYTES = 811843104
MODEL_SHA256 = "7a5a50953df2fb866a2f39bc4ac8906084cac4e3a5fa8f04adc519058ceedf87"


def valid_default_model(path: Path) -> bool:
    if not path.is_file() or path.stat().st_size != MODEL_BYTES:
        return False
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest() == MODEL_SHA256


def model_path():
    if configured := os.getenv("TURBOJEV_MODEL"):
        model = Path(configured).expanduser().resolve()
        if not model.is_file():
            raise FileNotFoundError(f"Model not found: {model}")
        return str(model)

    model = Path.home() / ".cache" / "turbojev" / MODEL_FILE
    if valid_default_model(model):
        return str(model)
    model.parent.mkdir(parents=True, exist_ok=True)
    temporary = model.with_suffix(".gguf.part")
    print("Downloading QJev3.5 0.8B v19c Q8_0 (about 0.81 GB)...")
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
                    progress = (
                        f"[{bar}] {ratio:5.1%}  {received / 2**20:.0f}/{total / 2**20:.0f} MB"
                    )
                else:
                    progress = f"{received / 2**20:.0f} MB downloaded"
                sys.stdout.write(f"\rQJev3.5 0.8B {progress}")
                sys.stdout.flush()
            if not received or (total and received != total):
                raise RuntimeError("Incomplete model download; run again to retry.")
        if not valid_default_model(temporary):
            raise ValueError("QJev download size or SHA-256 mismatch.")
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
