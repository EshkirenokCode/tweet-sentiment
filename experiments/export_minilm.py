import json
import shutil
from pathlib import Path

import onnx
import torch
from onnxruntime.quantization import QuantType, quantize_dynamic
from transformers import AutoModelForSequenceClassification, AutoTokenizer

from tweet_sentiment.data import verify, write_json
from tweet_sentiment.evaluate import metrics
from tweet_sentiment.onnx_classifier import OnnxClassifier
from tweet_sentiment.preprocessing import normalize

DIRECTORY = Path("experiments/v1.2-finetuned")


def run():
    checkpoint = DIRECTORY / "checkpoint"
    model = AutoModelForSequenceClassification.from_pretrained(
        checkpoint, attn_implementation="eager", local_files_only=True
    ).eval()
    tokenizer = AutoTokenizer.from_pretrained(checkpoint, local_files_only=True)
    torch.set_num_threads(4)

    class Logits(torch.nn.Module):
        def __init__(self, model):
            super().__init__()
            self.model = model

        def forward(self, input_ids, attention_mask, token_type_ids):
            return self.model(
                input_ids=input_ids, attention_mask=attention_mask, token_type_ids=token_type_ids
            ).logits

    example = tokenizer("A small example.", return_tensors="pt")
    names = ["input_ids", "attention_mask", "token_type_ids"]
    with torch.inference_mode():
        torch.onnx.export(
            Logits(model),
            tuple(example[key] for key in names),
            str(DIRECTORY / "float.onnx"),
            input_names=names,
            output_names=["logits"],
            opset_version=17,
            dynamo=False,
            dynamic_axes={
                **{key: {0: "batch", 1: "sequence"} for key in names},
                "logits": {0: "batch"},
            },
        )
    quantize_dynamic(
        str(DIRECTORY / "float.onnx"),
        str(DIRECTORY / "int8.onnx"),
        weight_type=QuantType.QInt8,
        per_channel=False,
    )
    for name in ("float", "int8"):
        graph = onnx.load(str(DIRECTORY / f"{name}.onnx"))
        onnx.helper.set_model_props(
            graph,
            {
                "source": "sentence-transformers/all-MiniLM-L6-v2",
                "source_revision": "1110a243fdf4706b3f48f1d95db1a4f5529b4d41",
                "changes": "Ilia Gulevskii: sentiment fine-tuning on TweetEval train; ONNX export.",
                "license": "Apache-2.0; see accompanying LICENSE and NOTICE",
            },
        )
        onnx.save(graph, str(DIRECTORY / f"{name}.onnx"))
    splits = verify()
    texts = [normalize(text, False) for text in splits["val"][0]]
    rows = []
    for precision in ("float", "int8"):
        folder = DIRECTORY / precision
        folder.mkdir(exist_ok=True)
        shutil.copyfile(DIRECTORY / f"{precision}.onnx", folder / "model.onnx")
        shutil.copyfile(checkpoint / "tokenizer.json", folder / "tokenizer.json")
        classifier = OnnxClassifier(str(folder), batch_size=1, threads=1)
        row = {
            "precision": precision,
            "batch_size": 1,
            "threads": 1,
            "validation": metrics(splits["val"][1], classifier.predict(texts)),
        }
        rows.append(row)
        print(json.dumps(row), flush=True)
    write_json(DIRECTORY / "serving_validation.json", rows)
    selected = (
        rows[1]
        if rows[1]["validation"]["macro_f1"] >= rows[0]["validation"]["macro_f1"] - 0.005
        else rows[0]
    )
    write_json(
        DIRECTORY / "selection.json",
        {
            "precision": selected["precision"],
            "selected": selected,
            "metric": "validation macro-F1",
            "int8_max_f1_drop": 0.005,
        },
    )


if __name__ == "__main__":
    run()
