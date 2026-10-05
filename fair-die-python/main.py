"""Permutation probability averaging, adapted from Apache-2.0 TypeLLM."""
import argparse
import importlib.metadata
import json
import math
import platform
from pathlib import Path
import sys
import time

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from demos_common import text_model, file_sha256
from turbojev import TurboJev

LABELS = ["one","two","three","four","five","six"]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model")
    parser.add_argument("--device",choices=["cpu","gpu"],default="cpu")
    parser.add_argument("--all-permutations",action="store_true",help="Include 720 real evaluations; potentially very slow")
    parser.add_argument("--output",type=Path,default=Path(__file__).with_name("result.json"))
    args=parser.parse_args()
    model=text_model(args.model)
    print(f"TurboJev {importlib.metadata.version('turbojev')} | model: {model} | {args.device}")
    runs={}
    with TurboJev.load(str(model),device=args.device,n_ctx=8192,n_seq_max=1,n_threads=4,n_threads_batch=4) as client:
        for budget in [1,"auto",8]+(["all"] if args.all_permutations else []):
            print(f"Evaluating permutation budget {budget}...",flush=True)
            start=time.perf_counter()
            response=client.generate(context="A single roll of a fair die.",seed=42,questions={"roll":{
                "type":"string","enum":LABELS,"instructions":"What number will come up on a single roll of a fair six-sided die?",
                "permutations":budget,"return_probabilities":True,
            }})
            answer=response["result"]["roll"]
            probabilities=answer["probabilities"]
            if set(probabilities)!=set(LABELS) or any(not math.isfinite(p) or not 0<=p<=1 for p in probabilities.values()) or not math.isclose(sum(probabilities.values()),1,abs_tol=1e-9):
                raise ValueError("Invalid model distribution")
            divergence=sum(math.log((1/6)/p)/6 for p in probabilities.values()) if all(probabilities.values()) else None
            runs[str(budget)]={"response":response,"seconds":time.perf_counter()-start,"kl_uniform_to_prediction":divergence}
            print(json.dumps(runs[str(budget)],indent=2))
    record={"turbojev":importlib.metadata.version("turbojev"),"model":str(model),"model_sha256":file_sha256(model),
            "platform":platform.platform(),"architecture":platform.machine(),"device":args.device,"seed":42,
            "ground_truth":dict.fromkeys(LABELS,1/6),"runs":runs}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(record,indent=2)+"\n",encoding="utf-8")
    print(f"Benchmark saved: {args.output}")


if __name__=="__main__":
    main()
