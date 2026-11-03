import argparse

import httpx

from tweet_sentiment import __version__

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True)
    args = parser.parse_args()
    with httpx.Client(base_url=args.url, timeout=30) as client:
        redirect = client.get("/")
        assert redirect.status_code == 307 and redirect.headers["location"] == "/docs"
        assert client.get("/health").json() == {"status": "alive"}
        readiness = client.get("/ready").json()
        assert readiness["status"] == "ready"
        info = client.get("/model").json()
        assert info["api_version"] == __version__
        assert info["model_version"] == readiness["model_version"]
        assert info["max_tokens"] == 256
        assert client.get("/docs").status_code == 200
        schema = client.get("/openapi.json").json()
        assert schema["info"]["version"] == __version__
        response = client.post("/predict", json={"text": "I love this wonderful app!"})
        response.raise_for_status()
        assert response.json()["label"] in ("negative", "neutral", "positive")
        assert response.json()["model_version"] == readiness["model_version"]
        assert client.post("/predict", json={"text": " "}).status_code == 422
        assert client.post("/predict", json={"text": 123}).status_code == 422
        assert client.post("/predict", json={"text": "x" * 2001}).status_code == 422
        assert client.post("/predict", content=b"x" * 8193).status_code == 413
        for body in (b'{"text":NaN}', b'{"text":"\\ud800"}', b'{"text":"\\udfff"}'):
            assert (
                client.post(
                    "/predict", content=body, headers={"content-type": "application/json"}
                ).status_code
                == 422
            )
        print("HTTP smoke passed:", args.url, response.json())
