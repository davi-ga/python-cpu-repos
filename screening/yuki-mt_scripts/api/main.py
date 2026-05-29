import os
import sys
from typing import Dict, List

import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE_DIR, "py"))
sys.path.insert(0, os.path.join(BASE_DIR, "crf"))

app = FastAPI(title="yuki-mt scripts API")


# ── 1. KNN Features ──────────────────────────────────────────────────────────


class KNNRequest(BaseModel):
    X: List[List[float]]
    y: List[int]
    k_list: List[int] = [3, 8]
    metric: str = "minkowski"  # "minkowski" or "cosine"


class KNNResponse(BaseModel):
    features: List[List[float]]


@app.post("/knn/features", response_model=KNNResponse)
def knn_features(req: KNNRequest):
    from knn_feature import NearestNeighborsFeats

    X = np.array(req.X, dtype=np.float64)
    y = np.array(req.y, dtype=np.int32)
    nnf = NearestNeighborsFeats(n_jobs=1, k_list=req.k_list, metric=req.metric)
    nnf.fit(X, y)
    feats = nnf.predict(X)
    return KNNResponse(features=feats.tolist())


# ── 2. Stress Test ───────────────────────────────────────────────────────────


class StressRequest(BaseModel):
    url: str
    queries: List[str]
    concurrent_num: int = 2


class StressResponse(BaseModel):
    throughput_qps: float
    num_requests: int
    avg_latency_ms: float
    p50_latency_ms: float
    p99_latency_ms: float
    statuses: Dict[str, int]


@app.post("/stress/run", response_model=StressResponse)
def stress_run(req: StressRequest):
    import socket
    import time
    import urllib.parse
    from concurrent.futures import ThreadPoolExecutor
    from urllib.error import HTTPError
    from urllib3 import PoolManager

    manager = PoolManager(req.concurrent_num, retries=False)
    headers = {"Connection": "Close"}

    def do_request(query: str):
        param = urllib.parse.urlencode({"query": query})
        try:
            begin = time.time()
            resp = manager.request("GET", req.url + "?" + param, headers=headers)
            resp.close()
            return (time.time() - begin, 200)
        except HTTPError as e:
            return (time.time() - begin, e.code)
        except socket.timeout:
            return (time.time() - begin, 0)
        except Exception:
            return (time.time() - begin, 400)

    all_begin = time.time()
    with ThreadPoolExecutor(max_workers=req.concurrent_num) as executor:
        futures = [executor.submit(do_request, q) for q in req.queries]

    statuses: Dict[str, int] = {}
    elapses = []
    for f in futures:
        elapsed, status = f.result()
        elapses.append(elapsed * 1000)
        key = str(status)
        statuses[key] = statuses.get(key, 0) + 1
    all_end = time.time()

    arr = np.array(elapses)
    return StressResponse(
        throughput_qps=round(len(req.queries) / (all_end - all_begin), 2),
        num_requests=len(elapses),
        avg_latency_ms=round(float(arr.mean()), 2),
        p50_latency_ms=round(float(np.percentile(arr, 50)), 2),
        p99_latency_ms=round(float(np.percentile(arr, 99)), 2),
        statuses=statuses,
    )


# ── 3. CRF NER (Japanese) ────────────────────────────────────────────────────


class CRFRequest(BaseModel):
    text: str  # Japanese text


class CRFResponse(BaseModel):
    tokens: List[str]
    tags: List[str]
    entities: List[str]


@app.post("/crf/predict", response_model=CRFResponse)
def crf_predict(req: CRFRequest):
    try:
        import MeCab
    except ImportError:
        raise HTTPException(
            status_code=501, detail="MeCab not installed in this container"
        )

    from feature import sent2features
    from ml import Predictor
    from models import Morpheme, Sentence

    model_dir = os.path.join(BASE_DIR, "crf", "model")
    if not os.path.exists(os.path.join(model_dir, "crf.model")):
        raise HTTPException(
            status_code=400,
            detail="Pre-trained CRF model not found. Run crf/main.py to train first.",
        )

    tagger = MeCab.Tagger()
    node = tagger.parseToNode(req.text)
    morphemes = []
    while node:
        if node.surface:
            f = node.feature.split(",")
            morphemes.append(
                Morpheme(
                    token=node.surface,
                    pos1=f[0] if len(f) > 0 else "*",
                    pos2=f[1] if len(f) > 1 else "*",
                    type=f[4] if len(f) > 4 else "*",
                )
            )
        node = node.next

    sentence = Sentence(morphemes)
    predictor = Predictor(model_dir)
    tags = predictor.predict(sent2features(sentence))
    tokens = sentence.to_tokens()

    entities = []
    word = ""
    for tag, token in zip(tags, tokens):
        if tag.startswith("B") or tag.startswith("I"):
            word += token
        elif word:
            entities.append(word)
            word = ""
    if word:
        entities.append(word)

    return CRFResponse(tokens=tokens, tags=tags, entities=entities)


# ── 4. MLflow Predict ────────────────────────────────────────────────────────


class MLflowRequest(BaseModel):
    run_id: str
    X: List[List[float]]
    tracking_uri: str = "http://localhost:5000"


class MLflowResponse(BaseModel):
    predictions: List[float]


@app.post("/mlflow/predict", response_model=MLflowResponse)
def mlflow_predict(req: MLflowRequest):
    import mlflow.sklearn
    import pandas as pd

    mlflow.set_tracking_uri(req.tracking_uri)
    try:
        model = mlflow.sklearn.load_model(f"runs:/{req.run_id}/sk_model")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to load model: {e}")

    predictions = model.predict(pd.DataFrame(req.X))
    return MLflowResponse(predictions=predictions.tolist())


# ── 5. Metaflow Sales Pipeline ───────────────────────────────────────────────


class MetaflowRequest(BaseModel):
    sales_path: str = "data/sales_train.csv"
    items_path: str = "data/items.csv"
    test_path: str = "data/test.csv"


class MetaflowResponse(BaseModel):
    status: str
    message: str


@app.post("/metaflow/run", response_model=MetaflowResponse)
def metaflow_run(req: MetaflowRequest):
    import subprocess

    env = os.environ.copy()
    env["SALES_PATH"] = req.sales_path
    env["ITEMS_PATH"] = req.items_path
    env["TEST_PATH"] = req.test_path

    result = subprocess.run(
        [sys.executable, "py/metaflow_sample.py", "run"],
        capture_output=True,
        text=True,
        cwd=BASE_DIR,
        env=env,
        timeout=3600,
    )

    if result.returncode != 0:
        raise HTTPException(status_code=500, detail=result.stderr[-1000:])

    return MetaflowResponse(
        status="completed",
        message=result.stdout[-500:] if result.stdout else "Pipeline completed",
    )
