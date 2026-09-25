import json
import os
from pathlib import Path
import sys
from urllib.request import urlopen
import time
from turbojev import TurboJev

MODEL_URL = "https://huggingface.co/bartowski/Qwen_Qwen3-0.6B-GGUF/resolve/main/Qwen_Qwen3-0.6B-Q4_K_M.gguf?download=true"
MODEL = os.getenv("TURBOJEV_MODEL")
if not MODEL:
    cache = Path.home() / ".cache" / "turbojev" / "Qwen3-0.6B-Q4_K_M.gguf"
    cache.parent.mkdir(parents=True, exist_ok=True)
    if not cache.exists():
        temporary = cache.with_suffix(".gguf.part")
        print("Downloading Qwen3 0.6B Q4_K_M (~0.48 GB)...")
        with urlopen(MODEL_URL) as response, temporary.open("wb") as output:
            total = int(response.headers.get("Content-Length", "0"))
            received = 0
            while chunk := response.read(1024 * 1024):
                output.write(chunk)
                received += len(chunk)
                if total:
                    ratio = min(1.0, received / total)
                    width = 28
                    filled = round(ratio * width)
                    bar = "█" * filled + "─" * (width - filled)
                    sys.stdout.write(f"\rQwen3 0.6B [{bar}] {ratio:5.1%}  {received / 2**20:.0f} / {total / 2**20:.0f} MB")
                else:
                    sys.stdout.write(f"\rDownloading Qwen3 0.6B: {received / 2**20:.0f} MB")
                sys.stdout.flush()
        print()
        temporary.replace(cache)
    MODEL = str(cache)
request = {
    "state": {"ticket": "My package arrived broken. Please send a replacement."},
    "questions": {
        "team": {
            "type": "choice",
            "instructions": "Which team should handle this ticket?",
            "criteria": {
                "billing": "Payments and refunds",
                "technical": "Bugs and outages",
                "shipping": "Delivery problems",
            },
        },
        "urgency": {
            "type": "score",
            "instructions": "How urgent is this ticket?",
            "criteria": ["Can wait", "This week", "Today"],
        },
        "wantsRefund": {
            "type": "noul",
            "instructions": "Does the customer ask for a refund?",
        },
    },
}

# Use "cyclic" to average candidate-order rotations; it is slower.
with TurboJev.load(
    MODEL,
    n_gpu_layers=0,
    execution={"orderRobustness": "none"},  # Change to "cyclic" for order robustness at extra inference cost.
) as engine:
    start = time.perf_counter()
    response = engine.evaluate(request)
    print(json.dumps(response, indent=2))
    print(f"Elapsed: {time.perf_counter() - start:.2f} s")
