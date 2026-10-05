"""CORD receipt example adapted from Apache-2.0 TypeLLM."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from receipt_demo import run

if __name__=="__main__":
    run(Path(__file__).resolve().parent,bundled=True)
