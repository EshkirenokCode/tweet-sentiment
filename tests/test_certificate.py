import os
import subprocess
from pathlib import Path

import pytest


@pytest.mark.parametrize("failure", ["none", "check", "reload"])
def test_certificate_publish_and_rollback(tmp_path, failure):
    source = tmp_path / "tls/live/tweet-sentiment"
    destination = tmp_path / "published"
    source.mkdir(parents=True)
    destination.mkdir()
    for name in ("fullchain.pem", "privkey.pem"):
        (source / name).write_text("new")
        (destination / name).write_text("old")
    (tmp_path / "host.env").write_text(
        f"ACME_WEBROOT={tmp_path}\nCERT_DEST={destination}\nPROXY_CONTAINER=edge\n"
    )
    binary = tmp_path / "bin"
    binary.mkdir()
    docker = binary / "docker"
    docker.write_text(
        "#!/bin/sh\n"
        'if [ "$1" = run ]; then exit 0; fi\n'
        f'if [ "$(cat "{destination}/fullchain.pem")" = new ]; then\n'
        '  case "$FAILURE:$*" in\n'
        r"    check:*nginx\ -t|reload:*nginx\ -s\ reload) exit 1 ;;"
        "\n"
        "  esac\n"
        "fi\nexit 0\n"
    )
    docker.chmod(0o755)
    # macOS has no flock; the test isolates publishing rather than OS locking.
    flock = binary / "flock"
    flock.write_text("#!/bin/sh\nexit 0\n")
    flock.chmod(0o755)
    env = {
        **os.environ,
        "PATH": f"{binary}:{os.environ['PATH']}",
        "TWEET_SENTIMENT_HOME": str(tmp_path),
        "FAILURE": failure,
    }
    result = subprocess.run(
        ["sh", str(Path("deploy/renew-certificate.sh"))], env=env, capture_output=True, text=True
    )
    assert result.returncode == (0 if failure == "none" else 1), result.stderr
    for name in ("fullchain.pem", "privkey.pem"):
        assert (destination / name).read_text() == ("new" if failure == "none" else "old")
