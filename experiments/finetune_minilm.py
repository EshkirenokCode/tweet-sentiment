import random
from pathlib import Path
from time import perf_counter

import numpy as np
import torch
from torch.utils.data import DataLoader
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    get_linear_schedule_with_warmup,
)

from tweet_sentiment.data import verify, write_json
from tweet_sentiment.evaluate import metrics
from tweet_sentiment.preprocessing import normalize

MODEL = "sentence-transformers/all-MiniLM-L6-v2"
REVISION = "1110a243fdf4706b3f48f1d95db1a4f5529b4d41"
OUTPUT = Path("experiments/v1.2-finetuned")


def run():
    if OUTPUT.exists():
        raise FileExistsError(OUTPUT)
    OUTPUT.mkdir()
    random.seed(42)
    np.random.seed(42)
    torch.manual_seed(42)
    torch.set_num_threads(4)
    torch.set_num_interop_threads(1)
    tokenizer = AutoTokenizer.from_pretrained(MODEL, revision=REVISION, trust_remote_code=False)
    model = AutoModelForSequenceClassification.from_pretrained(
        MODEL,
        revision=REVISION,
        num_labels=3,
        trust_remote_code=False,
        attn_implementation="eager",
        use_safetensors=True,
    ).to("cpu")
    splits = verify()
    datasets = {}
    for split in ("train", "val"):
        encoded = tokenizer(
            [normalize(text, False) for text in splits[split][0]], truncation=False, padding=False
        )
        assert max(map(len, encoded["input_ids"])) <= 256
        datasets[split] = [
            {**{key: values[i] for key, values in encoded.items()}, "labels": splits[split][1][i]}
            for i in range(len(splits[split][0]))
        ]

    def collate(rows):
        labels = torch.tensor([row["labels"] for row in rows], dtype=torch.long)
        batch = tokenizer.pad(
            [{k: v for k, v in row.items() if k != "labels"} for row in rows],
            padding=True,
            return_tensors="pt",
        )
        return {**batch, "labels": labels}

    train = DataLoader(
        datasets["train"],
        batch_size=32,
        shuffle=True,
        collate_fn=collate,
        generator=torch.Generator().manual_seed(42),
    )
    val = DataLoader(datasets["val"], batch_size=64, collate_fn=collate)
    optimizer = torch.optim.AdamW(model.parameters(), lr=3e-5, weight_decay=0.01)
    scheduler = get_linear_schedule_with_warmup(
        optimizer, int(len(train) * 2 * 0.1), len(train) * 2
    )
    best = -1
    rows = []
    start = perf_counter()
    for epoch in range(2):
        model.train()
        loss_sum = 0
        for step, batch in enumerate(train):
            optimizer.zero_grad(set_to_none=True)
            output = model(**batch)
            output.loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            scheduler.step()
            loss_sum += output.loss.item()
            if (step + 1) % 100 == 0:
                print(
                    "epoch",
                    epoch + 1,
                    "step",
                    step + 1,
                    "/",
                    len(train),
                    "loss",
                    round(loss_sum / (step + 1), 4),
                    "seconds",
                    round(perf_counter() - start, 1),
                    flush=True,
                )
        model.eval()
        predictions = []
        with torch.inference_mode():
            for batch in val:
                predictions.extend(model(**batch).logits.argmax(1).tolist())
        result = {
            "epoch": epoch + 1,
            "elapsed_seconds": perf_counter() - start,
            "validation": metrics(splits["val"][1], predictions),
        }
        rows.append(result)
        write_json(OUTPUT / "validation.json", rows)
        print(result, flush=True)
        if result["validation"]["macro_f1"] > best:
            best = result["validation"]["macro_f1"]
            model.save_pretrained(OUTPUT / "checkpoint", safe_serialization=True)
            tokenizer.save_pretrained(OUTPUT / "checkpoint")
            write_json(OUTPUT / "best.json", result)
    write_json(
        OUTPUT / "training.json",
        {
            "source": MODEL,
            "revision": REVISION,
            "seed": 42,
            "epochs": 2,
            "batch_size": 32,
            "learning_rate": 3e-5,
            "weight_decay": 0.01,
            "warmup_fraction": 0.1,
            "threads": 4,
            "seconds": perf_counter() - start,
        },
    )


if __name__ == "__main__":
    run()
