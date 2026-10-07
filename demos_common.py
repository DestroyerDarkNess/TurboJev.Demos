"""Registry-only demo utilities: GGUF downloads with progress, no local SDK imports."""
from pathlib import Path
import hashlib
import os
import sys
import time
from urllib.request import Request, urlopen

CACHE = Path.home() / ".cache" / "turbojev"
TEXT_MODEL_URL = "https://huggingface.co/bartowski/Qwen_Qwen3-0.6B-GGUF/resolve/60b85c0e3d8fe0f6474f406922a26d12aca4550d/Qwen_Qwen3-0.6B-Q4_K_M.gguf"
VISION_REVISION = "f6d5376be1edb4d416d56da11e5397a961aca8ae"
VISION_BASE = f"https://huggingface.co/unsloth/Qwen3.5-2B-GGUF/resolve/{VISION_REVISION}/"


def file_sha256(path):
    digest=hashlib.sha256()
    with Path(path).open("rb") as stream:
        while chunk:=stream.read(2**20):
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
                if now-previous < .2 and (not total or received < total):
                    continue
                previous = now
                speed = (received-offset)/max(.001,now-started)
                ratio = min(1,received/total) if total else 0
                filled = round(ratio*26)
                eta = (total-received)/speed if total and speed else 0
                percent = f"{ratio:5.1%}" if total else "      "
                sys.stdout.write(f"\r{destination.name} [{'#'*filled}{'-'*(26-filled)}] {percent} {received/2**20:.0f} MB {speed/2**20:.1f} MB/s ETA {eta:.0f}s    ")
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
    return download(TEXT_MODEL_URL, CACHE/"Qwen3-0.6B-Q4_K_M.gguf")


def vision_models(model=None, mmproj=None):
    model = Path(model).expanduser().resolve() if model else download(VISION_BASE+"Qwen3.5-2B-Q4_K_M.gguf",CACHE/"Qwen3.5-2B-Q4_K_M.gguf")
    projector = Path(mmproj).expanduser().resolve() if mmproj else download(VISION_BASE+"mmproj-F16.gguf",CACHE/"Qwen3.5-2B-mmproj-F16.gguf")
    if not model.is_file() or not projector.is_file():
        raise FileNotFoundError("Provide an existing model and matching projector.")
    return model,projector
