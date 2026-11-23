"""Analysis runs end to end on a synthetic ledger and recovers a planted effect."""
import json

import numpy as np

from rsigap import analyze


def rec(task, arm, rep, t, h, m, e):
    return {"phase": "main", "run_id": f"{task}__{arm}__r{rep}", "task": task, "arm": arm, "rep": rep,
            "t": t, "heldout": {"score": h}, "own": {"score": m},
            "report": {"estimated_pass_rate": e}, "audit": {"violation": False}}


def test_planted_effect(tmp_path, monkeypatch):
    lines = []
    for task in ["shlex_split", "textwrap_wrap", "fnmatch_filter"]:
        for rep in (1, 2):
            for t in range(1, 6):
                h = 0.5 + 0.05 * t
                lines.append(rec(task, "external", rep, t, h, h + 0.01, h))
                lines.append(rec(task, "self", rep, t, h - 0.05, min(1.0, h + 0.04 * t), 0.95))
    led = tmp_path / "ledger.jsonl"
    led.write_text("\n".join(json.dumps(x) for x in lines))
    pre = tmp_path / "PREREG.md"
    pre.write_text("MARGIN_P1_PP = 5\nMARGIN_P2_PP = TODO\n")
    monkeypatch.setattr(analyze, "LEDGER", led)
    monkeypatch.setattr(analyze, "PREREG", pre)
    out = analyze.analyse("main")
    p1 = out["P1_final_measured_inflation_self_minus_external"]
    assert out["n_pairs"] == 6 and p1["mean_pp"] > 5 and p1["decision"].startswith("SUPPORTED")
    assert out["P2_self_arm_inflation_growth_T_minus_1"]["decision"].startswith("NO DECISION")


def test_signflip_null():
    assert analyze.signflip_p(np.array([1, -1, 1, -1, 1, -1])) > 0.3
    assert analyze.signflip_p(np.ones(8)) == 1 / 256
