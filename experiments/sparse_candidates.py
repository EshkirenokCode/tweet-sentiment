import json
from pathlib import Path
from time import perf_counter

import joblib
from sklearn.linear_model import LogisticRegression
from sklearn.multiclass import OneVsRestClassifier
from sklearn.svm import LinearSVC
from threadpoolctl import threadpool_limits

from tweet_sentiment.data import verify, write_json
from tweet_sentiment.evaluate import metrics
from tweet_sentiment.model import build_model
from tweet_sentiment.nb_logistic import NBLogistic


def run():
    output = Path("experiments/v1.2-sparse")
    if output.exists():
        raise FileExistsError(output)
    output.mkdir(parents=True)
    splits = verify()
    config = json.loads(Path("configs/experiment.json").read_text())
    config["word_max_features"] = config["char_max_features"] = 150000
    candidates = (
        [
            {
                "name": f"nb_words_{'stop' if stop else 'keep'}_C{c}",
                "kind": "nb",
                "remove_stopwords": stop,
                "char": False,
                "C": c,
            }
            for stop in (False, True)
            for c in (1, 4)
        ]
        + [
            {
                "name": f"nb_wordchar_keep_C{c}",
                "kind": "nb",
                "remove_stopwords": False,
                "char": True,
                "C": c,
            }
            for c in (1, 4)
        ]
        + [
            {
                "name": "svc_wordchar_balanced",
                "kind": "svc",
                "C": 0.1,
                "remove_stopwords": False,
                "char": True,
            },
            {
                "name": "lr_wordchar_balanced",
                "kind": "lr",
                "C": 4,
                "remove_stopwords": False,
                "char": True,
            },
        ]
    )
    write_json(output / "config.json", {"features": config, "candidates": candidates})
    rows = []
    with threadpool_limits(1):
        for candidate in candidates:
            construction = {**candidate, "kind": "svc"}
            model = build_model(construction, config)
            if candidate["kind"] == "nb":
                classifier = OneVsRestClassifier(NBLogistic(candidate["C"]), n_jobs=1)
            elif candidate["kind"] == "svc":
                classifier = LinearSVC(
                    C=0.1, class_weight="balanced", random_state=42, dual=True, max_iter=5000
                )
            else:
                classifier = LogisticRegression(
                    C=4, class_weight="balanced", max_iter=1000, random_state=42
                )
            model.set_params(classifier=classifier)
            start = perf_counter()
            model.fit(*splits["train"])
            result = {
                "config": candidate,
                "train_seconds": perf_counter() - start,
                "validation": metrics(splits["val"][1], model.predict(splits["val"][0])),
            }
            rows.append(result)
            write_json(output / "validation.json", rows)
            print(
                candidate["name"],
                result["validation"]["accuracy"],
                result["validation"]["macro_f1"],
                flush=True,
            )
            if result is max(rows, key=lambda row: row["validation"]["macro_f1"]):
                joblib.dump(model, output / "best.joblib", compress=3)
                write_json(output / "best.json", result)


if __name__ == "__main__":
    run()
