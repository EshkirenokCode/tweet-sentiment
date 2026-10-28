import argparse
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen

from tweet_sentiment import LABELS
from tweet_sentiment.preprocessing import normalize

REVISION = "4fbd22cd78421f05b1ecdb4fc5725bc7a7bd8f66"
BASE = f"https://raw.githubusercontent.com/cardiffnlp/tweeteval/{REVISION}/datasets/sentiment"
COUNTS = {"train": 45615, "val": 2000, "test": 12284}
ROOT = Path("data")
MANIFEST = Path("reports/data_manifest.json")


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def load_split(split, root=ROOT):
    texts = (root / f"{split}_text.txt").read_text(encoding="utf-8").splitlines()
    labels = [int(x) for x in (root / f"{split}_labels.txt").read_text().splitlines()]
    if len(texts) != COUNTS[split] or len(labels) != len(texts):
        raise ValueError(f"Unexpected row counts for {split}: {len(texts)}, {len(labels)}")
    if any(y not in range(3) for y in labels) or any(not x.strip() for x in texts):
        raise ValueError(f"Invalid label or empty text in {split}")
    return texts, labels


def verify(root=ROOT, manifest_path=MANIFEST):
    manifest = json.loads(Path(manifest_path).read_text())
    if manifest["revision"] != REVISION:
        raise ValueError("Unexpected data revision")
    expected = {f"{s}_{kind}.txt" for s in COUNTS for kind in ("text", "labels")}
    expected.add("mapping.txt")
    if set(manifest["files"]) != expected:
        raise ValueError("Incomplete manifest")
    for name, info in manifest["files"].items():
        if sha256(root / name) != info["sha256"]:
            raise ValueError(f"Checksum mismatch: {name}; run data download again")
    if (root / "mapping.txt").read_text().splitlines() != [
        f"{i}\t{label}" for i, label in enumerate(LABELS)
    ]:
        raise ValueError("Unexpected label mapping")
    return {s: load_split(s, root) for s in COUNTS}


def groups(texts, labels, normalized):
    result = defaultdict(list)
    for i, (text, label) in enumerate(zip(texts, labels, strict=True)):
        result[normalize(text) if normalized else text].append((i, label))
    return result


def audit(splits):
    report = {"splits": {}, "overlaps": {}}
    for split, (texts, labels) in splits.items():
        row = {
            "count": len(texts),
            "class_counts": dict(Counter(LABELS[y] for y in labels)),
            "null_texts": 0,
            "empty_raw": sum(not x.strip() for x in texts),
            "empty_normalized": sum(not normalize(x) for x in texts),
            "empty_with_stopwords_removed": sum(not normalize(x, True) for x in texts),
        }
        for mode in ("raw", "normalized"):
            g = groups(texts, labels, mode == "normalized")
            row[mode] = {
                "duplicate_groups": sum(len(v) > 1 for v in g.values()),
                "excess_rows": sum(len(v) - 1 for v in g.values()),
                "conflicting_label_groups": sum(len({y for _, y in v}) > 1 for v in g.values()),
            }
        report["splits"][split] = row
    for mode in ("raw", "normalized"):
        g = {s: groups(*v, mode == "normalized") for s, v in splits.items()}
        report["overlaps"][mode] = {}
        for a, b in (("train", "val"), ("train", "test"), ("val", "test")):
            keys = g[a].keys() & g[b].keys()
            report["overlaps"][mode][f"{a}/{b}"] = {
                "shared_keys": len(keys),
                "rows_in_first": sum(len(g[a][k]) for k in keys),
                "rows_in_second": sum(len(g[b][k]) for k in keys),
                "conflicting_label_keys": sum(
                    len({y for _, y in g[a][k] + g[b][k]}) > 1 for k in keys
                ),
            }
    return report


def download(root=ROOT, manifest_path=MANIFEST):
    root.mkdir(parents=True, exist_ok=True)
    pinned = json.loads(manifest_path.read_text()) if manifest_path.exists() else None
    files = {}
    names = [f"{s}_{k}.txt" for s in COUNTS for k in ("text", "labels")] + ["mapping.txt"]
    for name in names:
        url = f"{BASE}/{name}"
        with urlopen(url, timeout=60) as response:
            content = response.read()
        digest = hashlib.sha256(content).hexdigest()
        if pinned and digest != pinned["files"][name]["sha256"]:
            raise ValueError(f"Downloaded checksum mismatch: {name}")
        temporary = root / f"{name}.part"
        temporary.write_bytes(content)
        temporary.replace(root / name)
        files[name] = {"url": url, "sha256": digest, "bytes": len(content)}
    splits = {s: load_split(s, root) for s in COUNTS}
    manifest = {
        "source": "https://github.com/cardiffnlp/tweeteval",
        "revision": REVISION,
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "files": files,
        "label_mapping": dict(enumerate(LABELS)),
        "splits": {
            s: {"count": len(x), "class_counts": dict(Counter(LABELS[i] for i in y))}
            for s, (x, y) in splits.items()
        },
    }
    # Preserve the published manifest so its hash stays tied to the evaluated artifact.
    if not pinned:
        write_json(manifest_path, manifest)
    verify(root, manifest_path)
    write_json("reports/data_audit.json", audit(splits))
    print(json.dumps(manifest["splits"], indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["download", "verify"])
    args = parser.parse_args()
    if args.command == "download":
        download()
    else:
        verify()
        print("Data checksums and counts verified")
