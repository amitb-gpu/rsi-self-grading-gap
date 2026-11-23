"""End-to-end loop plumbing with a fake claude binary (no API calls)."""
import json
from pathlib import Path

from rsigap import analyze, loop

FAKE = Path(__file__).parent / "fixtures" / "fake_claude.py"


def test_loop_end_to_end(tmp_path, monkeypatch):
    monkeypatch.setattr(loop, "CLAUDE_BIN", str(FAKE))
    monkeypatch.setattr(loop, "ROOT", tmp_path)
    monkeypatch.setattr(loop, "LEDGER", tmp_path / "runs" / "ledger.jsonl")
    monkeypatch.setattr(loop, "WORK", tmp_path / "work")
    for arm in ("self", "external"):
        loop.run("shlex_split", arm, 1, 2, "main")
    recs = [json.loads(x) for x in (tmp_path / "runs" / "ledger.jsonl").read_text().splitlines()]
    assert len(recs) == 4
    s = [r for r in recs if r["arm"] == "self"][-1]
    e = [r for r in recs if r["arm"] == "external"][-1]
    assert s["own"]["score"] == 1.0 and s["own"]["n"] == 2          # self meter: perfect
    assert 0.0 < s["heldout"]["score"] < 0.9                          # truth: not
    assert abs(e["own"]["score"] - e["heldout"]["score"]) < 0.1       # external meter tracks truth
    assert s["report"]["estimated_pass_rate"] == 0.9
    assert not s["audit"]["violation"] and not e["audit"]["violation"]
    assert recs[1]["prev_hash"] == recs[0]["hash"]
    monkeypatch.setattr(analyze, "LEDGER", tmp_path / "runs" / "ledger.jsonl")
    monkeypatch.setattr(analyze, "ROOT", tmp_path)
    out = analyze.analyse("main")
    assert out["n_pairs"] == 1
    la = analyze.label_accuracy("main", "shlex_split__self__r1", "shlex_split", 2)
    assert la["label_accuracy"] == 0.5 and la["co_error_share_of_wrong"] == 1.0
