import argparse

import httpx

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True)
    args = parser.parse_args()
    with httpx.Client(base_url=args.url, timeout=30) as client:
        assert client.get("/health").json() == {"status": "alive"}
        assert client.get("/ready").json()["status"] == "ready"
        assert client.get("/docs").status_code == 200
        response = client.post("/predict", json={"text": "I love this wonderful app!"})
        response.raise_for_status()
        assert response.json()["label"] in ("negative", "neutral", "positive")
        assert response.json()["model_version"] == "1.0.0"
        assert client.post("/predict", json={"text": " "}).status_code == 422
        assert client.post("/predict", json={"text": 123}).status_code == 422
        assert client.post("/predict", json={"text": "x" * 2001}).status_code == 422
        assert client.post("/predict", content=b"x" * 8193).status_code == 413
        print("HTTP smoke passed:", args.url, response.json())
