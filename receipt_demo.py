"""Shared receipt runner; extraction and dependent answers come only from TurboJev."""
import argparse
import base64
import hashlib
import importlib.metadata
import json
import math
from pathlib import Path
import platform
import time

from demos_common import vision_models, file_sha256
from turbojev import TurboJev


def matched(actual, expected):
    if isinstance(expected,bool):
        return type(actual) is bool and actual is expected
    if isinstance(expected,(int,float)):
        return type(actual) in (int,float) and math.isclose(actual,expected,abs_tol=1e-6,rel_tol=1e-6)
    return type(actual) is type(expected) and actual==expected


def run(folder, bundled=False):
    parser=argparse.ArgumentParser(description="Extract a photographed receipt with the published TurboJev GGUF runtime.")
    parser.add_argument("--image",type=Path,default=folder/"receipt.jpg" if bundled else None,required=not bundled)
    parser.add_argument("--model",help="Vision GGUF model; default Qwen3.5 2B Q4_K_M")
    parser.add_argument("--mmproj",help="Matching vision projector; default Qwen3.5 2B F16")
    parser.add_argument("--device",choices=["cpu","gpu"],default="cpu")
    parser.add_argument("--fields",help="Comma-separated subset; dependencies are included")
    parser.add_argument("--reference-labels",action="store_true",help="Compare with the original example's labels only when using that exact reference image")
    parser.add_argument("--max-tokens",type=int,default=64)
    parser.add_argument("--output",type=Path,default=folder/"result.json")
    args=parser.parse_args()
    if not args.image.is_file() or not 0<args.image.stat().st_size<=24*2**20:
        parser.error("Provide a nonempty image of at most 24 MiB.")
    if not 1<=args.max_tokens<=32768:
        parser.error("max-tokens must be between 1 and 32768")
    questions=json.loads((folder/"questions.json").read_text(encoding="utf-8"))
    if args.fields:
        names=set(args.fields.split(','))
        if names-set(questions):
            parser.error("Unknown field names: "+', '.join(sorted(names-set(questions))))
        while True:
            expanded=names|{dep for name in names for dep in questions[name].get('depends_on',[])}
            if expanded==names: break
            names=expanded
        questions={name:field for name,field in questions.items() if name in names}
    use_labels=args.reference_labels or bundled and args.image.resolve()==(folder/"receipt.jpg").resolve()
    expected=json.loads((folder/"expected.json").read_text(encoding="utf-8")) if use_labels else {}
    expected={name:value for name,value in expected.items() if name in questions}
    model,mmproj=vision_models(args.model,args.mmproj)
    print(f"TurboJev {importlib.metadata.version('turbojev')} | {model.name} + {mmproj.name} | {args.device}")
    print(f"Reading {args.image.name}: {len(questions)} fields; values and dependent calculations are model-generated.",flush=True)
    evidence=args.image.read_bytes()
    request={"context":{"contract":"turbojev.media.v1","modality":"image","text":"Read the attached photo of a restaurant receipt.","base64":base64.b64encode(evidence).decode()},
             "questions":questions,"thinking":False,"text_max_tokens":args.max_tokens,"numeric_max_tokens":args.max_tokens}
    load_started=time.perf_counter()
    response=None
    failure=None
    load_seconds=None
    started=load_started
    try:
        with TurboJev.load(str(model),mmproj=str(mmproj),device=args.device,n_ctx=8192,n_seq_max=1,n_threads=4,n_threads_batch=4) as client:
            load_seconds=time.perf_counter()-load_started
            started=time.perf_counter()
            response=client.generate(request)
    except Exception as error:
        failure=str(error)
    seconds=time.perf_counter()-started
    result=response["result"] if response is not None else {}
    checks={name:matched(result.get(name),value) for name,value in expected.items()}
    record={"turbojev":importlib.metadata.version("turbojev"),"model":str(model),"mmproj":str(mmproj),"device":args.device,
            "model_sha256":file_sha256(model),"mmproj_sha256":file_sha256(mmproj),
            "platform":platform.platform(),"architecture":platform.machine(),"image_sha256":hashlib.sha256(evidence).hexdigest(),
            "fields":list(questions),"subset":bool(args.fields),"max_tokens":args.max_tokens,"thinking":False,
            "load_seconds":load_seconds,"evaluation_seconds":seconds,"response":response,"expected":expected,"matches":checks,
            "ok":failure is None,"error":failure}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(record,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    if failure is not None:
        print(f"Generation failed: {failure}\nBenchmark saved: {args.output}")
        raise SystemExit(2)
    print(json.dumps(result,indent=2,ensure_ascii=False))
    if checks: print(f"Reference labels: {sum(checks.values())}/{len(checks)} fields match")
    print(f"Load: {load_seconds:.3f}s | Evaluation: {seconds:.3f}s | {seconds/len(result):.3f}s per returned field (aggregate)")
    print(f"Benchmark saved: {args.output}")
