"""Instrument checks on the generated case files (run in the full rsigap env)."""
import collections
import hashlib
import json
from pathlib import Path

import pytest

from rsigap.tasks import TASKS

ROOT = Path(__file__).resolve().parents[1]
MAX_MODAL_SHARE = 0.40  # a constant answer must not score above this


def load(kind, name):
    d = ROOT / ("cases/dev" if kind == "dev" else "sealed/heldout")
    return json.loads((d / f"{name}.json").read_text())


@pytest.mark.parametrize("name", list(TASKS))
@pytest.mark.parametrize("kind", ["dev", "heldout"])
def test_not_degenerate(name, kind):
    cs = load(kind, name)
    counts = collections.Counter(json.dumps(c["expected"], sort_keys=True) for c in cs)
    modal_share = counts.most_common(1)[0][1] / len(cs)
    assert modal_share < MAX_MODAL_SHARE, (name, kind, counts.most_common(3))


@pytest.mark.parametrize("name", list(TASKS))
def test_dev_heldout_disjoint(name):
    k = lambda c: json.dumps([c["args"], c["kwargs"]], sort_keys=True)  # noqa: E731
    assert not ({k(c) for c in load("dev", name)} & {k(c) for c in load("heldout", name)})


def test_manifest_hashes_match():
    m = json.loads((ROOT / "sealed/MANIFEST.json").read_text())
    for rel, h in m["files"].items():
        assert hashlib.sha256((ROOT / rel).read_bytes()).hexdigest() == h, rel
