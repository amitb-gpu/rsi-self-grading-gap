"""Preregistered estimation analysis for v0.2 (PREREGISTRATION_GPU.md section 5).

python -m rsigap.gpu.analyze_gpu [phase]  ->  results/gpu_analysis_<phase>.json + printed table
"""
from __future__ import annotations

import json
import statistics as st
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LEDGER = ROOT / "runs" / "gpu_ledger.jsonl"


def load(phase: str):
    base, its = None, {}
    for line in LEDGER.read_text().splitlines():
        r = json.loads(line)
        if r.get("kind") == "baseline" and r["phase"] in (phase, "main"):
            base = r if (base is None or r["phase"] == phase) else base
        elif r.get("kind") == "iteration" and r["phase"] == phase:
            its.setdefault(r["run_id"], {})[r["t"]] = r
    return base, its


def per_iteration(base: dict, r: dict) -> dict:
    rep = r["report"]
    tg = base["test_mean"] - r["truth_mean"]
    claimed_gain = (rep["baseline_val_bpb"] - rep["claimed_val_bpb"]) if "claimed_val_bpb" in rep else None
    mg = (base["val_mean"] - r["dev_mean"]) if r["arm"] == "external" else claimed_gain
    row = {"t": r["t"], "truth": r["truth_mean"], "dev": r["dev_mean"],
           "claimed": rep.get("claimed_val_bpb"), "claimed_base": rep.get("baseline_val_bpb"),
           "TG": tg, "MG": mg, "I": (mg - tg) if mg is not None else None,
           "CI": (claimed_gain - tg) if claimed_gain is not None else None,
           "sel_noise_leak": (rep["claimed_val_bpb"] - r["dev_mean"]) if "claimed_val_bpb" in rep else None,
           "val_to_test": r["dev_mean"] - r["truth_mean"],
           "invalid_harness_runs": sum(not x.get("valid") for x in r["truth"] + r["dev"]),
           "agent_evals": len(r["agent_evals"]),
           "agent_best_val": min((e["bpb"] for e in r["agent_evals"] if e.get("valid")), default=None),
           "violation": r["audit"]["violation"],
           "flags": [k for k, v in r["audit"]["flags"].items() if v]}
    if r.get("scaled_mean") is not None:
        row["TG2"] = base["test_scaled_mean"] - r["scaled_mean"]
        row["transfer_ratio"] = row["TG2"] / tg if tg else None
    return row


def summarise(phase: str = "main", exclude_violations: bool = False) -> dict:
    base, its = load(phase)
    sd = st.stdev([x["scored_bpb"] for x in base["test"]])
    runs = {}
    for rid, d in sorted(its.items()):
        rows = [per_iteration(base, d[t]) for t in sorted(d)]
        if exclude_violations and any(x["violation"] for x in rows):
            continue
        runs[rid] = {"arm": d[min(d)]["arm"], "rows": rows}

    def final(arm, key):
        return [r["rows"][-1][key] for r in runs.values() if r["arm"] == arm and r["rows"][-1][key] is not None]

    def mean(xs):
        return st.mean(xs) if xs else None

    e1_self, e1_ext = final("self", "I"), final("external", "I")
    e2 = [r["rows"][-1]["I"] - r["rows"][0]["I"] for r in runs.values()
          if r["arm"] == "self" and r["rows"][-1]["I"] is not None and r["rows"][0]["I"] is not None]
    share = {arm: [r["rows"][-1]["I"] / r["rows"][-1]["MG"] for r in runs.values()
                   if r["arm"] == arm and r["rows"][-1]["MG"] not in (None, 0) and r["rows"][-1]["I"] is not None]
             for arm in ("self", "external")}
    return {
        "phase": phase, "exclude_violations": exclude_violations,
        "baseline": {"test_mean": base["test_mean"], "val_mean": base["val_mean"],
                     "test_scaled_mean": base["test_scaled_mean"], "test_seed_sd": sd},
        "yardstick_1sd_bpb": sd,
        "E1_final_inflation": {"self": e1_self, "external": e1_ext, "self_mean": mean(e1_self),
                               "external_mean": mean(e1_ext),
                               "diff": (mean(e1_self) - mean(e1_ext)) if e1_self and e1_ext else None,
                               "share_of_meter_gain": {k: v for k, v in share.items()}},
        "E2_self_growth": {"values": e2, "mean": mean(e2)},
        "S1_true_gain_final": {"self": final("self", "TG"), "external": final("external", "TG")},
        "S2_self_decomposition_final": {"claimed_minus_dev": final("self", "sel_noise_leak"),
                                        "dev_minus_truth": final("self", "val_to_test")},
        "S3_transfer_ratio": {"self": final("self", "transfer_ratio"), "external": final("external", "transfer_ratio")},
        "S4_invalid_and_flags": {rid: {"invalid": sum(x["invalid_harness_runs"] for x in r["rows"]),
                                       "flags": sorted({f for x in r["rows"] for f in x["flags"]})}
                                 for rid, r in runs.items()},
        "runs": runs,
    }


def main() -> None:
    phase = sys.argv[1] if len(sys.argv) > 1 else "main"
    res = {"primary": summarise(phase), "sensitivity_no_violations": summarise(phase, True)}
    out = ROOT / "results" / f"gpu_analysis_{phase}.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(res, indent=2))
    p = res["primary"]
    print(f"baseline test {p['baseline']['test_mean']:.4f} (seed SD {p['yardstick_1sd_bpb']:.4f}), "
          f"val {p['baseline']['val_mean']:.4f}")
    print(f"{'run':22s} t  truth   dev    claimed  TG      MG      I       evals flags")
    for rid, r in p["runs"].items():
        for x in r["rows"]:
            f = lambda v: f"{v:7.4f}" if isinstance(v, (int, float)) else "   -   "  # noqa: E731
            print(f"{rid:22s} {x['t']}  {f(x['truth'])} {f(x['dev'])} {f(x['claimed'])} {f(x['TG'])} "
                  f"{f(x['MG'])} {f(x['I'])} {x['agent_evals']:5d} {','.join(x['flags'])}")
    for k in ("E1_final_inflation", "E2_self_growth", "S1_true_gain_final", "S2_self_decomposition_final",
              "S3_transfer_ratio"):
        print(k, json.dumps(p[k]))
    print("wrote", out)


if __name__ == "__main__":
    main()
