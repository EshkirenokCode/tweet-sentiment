import json

import pytest

from tweet_sentiment.data import audit, sha256, verify


def test_duplicates_and_conflicts():
    report = audit(
        {
            "train": (["Good!", "Good!", "@alice nice"], [2, 0, 2]),
            "val": (["@bob nice"], [1]),
            "test": (["Other text"], [1]),
        }
    )
    assert report["splits"]["train"]["raw"]["duplicate_groups"] == 1
    assert report["splits"]["train"]["raw"]["conflicting_label_groups"] == 1
    assert report["overlaps"]["normalized"]["train/val"]["shared_keys"] == 1
    assert report["overlaps"]["normalized"]["train/val"]["conflicting_label_keys"] == 1


def test_checksum_corruption(tmp_path):
    manifest = json.loads(open("reports/data_manifest.json").read())
    for name, info in manifest["files"].items():
        path = tmp_path / name
        path.write_text("fixture")
        info["sha256"] = sha256(path)
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest))
    (tmp_path / "train_text.txt").write_text("corrupted")
    with pytest.raises(ValueError, match="Checksum mismatch"):
        verify(tmp_path, path)
