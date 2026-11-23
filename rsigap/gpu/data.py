"""enwik8 byte splits: train 90M / val 5M / test 5M (the standard split).

train.bin and val.bin are hard-linked into each workspace. test.bin is sealed under
~/rsigap-work/data/sealed and is only ever read by the harness's evaluator.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

DATA = Path.home() / "rsigap-work" / "data"
PUB = DATA / "pub"
SEALED = DATA / "sealed"
ROOT = Path(__file__).resolve().parents[2]
EXPECTED_ENWIK8_SHA256_PREFIX = "2b49720ec4d78c3c"


def prepare() -> dict:
    raw = (DATA / "enwik8").read_bytes()
    assert len(raw) == 100_000_000
    h = hashlib.sha256(raw).hexdigest()
    assert h.startswith(EXPECTED_ENWIK8_SHA256_PREFIX), h
    PUB.mkdir(parents=True, exist_ok=True)
    SEALED.mkdir(parents=True, exist_ok=True)
    splits = {PUB / "train.bin": raw[:90_000_000], PUB / "val.bin": raw[90_000_000:95_000_000],
              SEALED / "test.bin": raw[95_000_000:]}
    man = {"enwik8_sha256": h, "files": {}}
    for p, b in splits.items():
        p.write_bytes(b)
        p.chmod(0o444)
        man["files"][p.name] = {"bytes": len(b), "sha256": hashlib.sha256(b).hexdigest()}
    (ROOT / "sealed" / "gpu_MANIFEST.json").write_text(json.dumps(man, indent=2))
    return man


if __name__ == "__main__":
    print(json.dumps(prepare(), indent=2))
