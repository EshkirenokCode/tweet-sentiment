import argparse
import json
import platform
import subprocess
from pathlib import Path
from time import perf_counter

import httpx
import numpy as np
from threadpoolctl import threadpool_info, threadpool_limits

from tweet_sentiment.artifact import load_artifact
from tweet_sentiment.data import write_json

TEXTS = [
    "The update works really well.",
    "I cannot use the app. It keeps crashing!",
    "The next meeting starts at ten.",
    "Great, another broken update. Thanks a lot.",
    "I like the design but the service is awful.",
]


def measure(call):
    for i in range(30):
        call(TEXTS[i % len(TEXTS)])
    timings = []
    for i in range(500):
        start = perf_counter()
        call(TEXTS[i % len(TEXTS)])
        timings.append((perf_counter() - start) * 1000)
    return {
        "p50_ms": float(np.percentile(timings, 50)),
        "p95_ms": float(np.percentile(timings, 95)),
        "measurements": len(timings),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:8000")
    args = parser.parse_args()
    model, metadata = load_artifact()
    cpu = platform.processor()
    if platform.system() == "Darwin":
        cpu = subprocess.check_output(
            ["sysctl", "-n", "machdep.cpu.brand_string"], text=True
        ).strip()
    with threadpool_limits(limits=1):
        report = {
            "platform": platform.platform(),
            "cpu": cpu,
            "batch_size": 1,
            "warmup": 30,
            "threads": 1,
            "threadpools": [
                {key: value for key, value in pool.items() if key != "filepath"}
                for pool in threadpool_info()
            ],
            "model_sha256": metadata["sha256"],
            "dependencies": metadata["dependencies"],
            "artifact_bytes": metadata["artifact_bytes"],
            "final_train_seconds": metadata["final_train_seconds"],
            "in_process": measure(lambda text: model.predict([text])),
        }
        with httpx.Client(base_url=args.url, timeout=10) as client:
            client.get("/ready").raise_for_status()

            def predict(text):
                response = client.post("/predict", json={"text": text})
                response.raise_for_status()
                assert response.json()["model_version"] == metadata["model_version"]

            report["http_loopback"] = measure(predict)
            report["http_notes"] = "One uvicorn worker, keep-alive, sequential requests, loopback."
    write_json(Path("reports/benchmark.json"), report)
    print(json.dumps(report, indent=2))
