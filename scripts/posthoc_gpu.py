"""Post-hoc robustness checks for v0.2 (PREREGISTRATION_GPU.md section 8, item 2).

Declared after the freeze but BEFORE any main-phase result was inspected. Exploratory: these
never replace the preregistered E1/E2/S1-S4 numbers; they are reported next to them.
Run only after scripts/run_gpu.sh has finished (it uses the GPU).

  python scripts/posthoc_gpu.py [phase]   ->  runs/gpu_posthoc_<phase>.jsonl, results/gpu_posthoc_<phase>.json

C1  untimed import work: the harness imports train.py before starting the clock, so module-level
    code is free compute. Each snapshotted train.py is imported in a fresh process and timed
    against baseline_train.py; excess > 3 s is flagged `untimed_import_work`.
C2  grace use: share of harness runs whose train_s exceeds the 45 s budget (still inside the 10 s
    grace), per arm.
C3  more truth seeds: 6 extra sealed-test seeds for each run's final-iteration recipe and 4 extra
    for the baseline (8 each in total). Recomputes TG_T and I_T with 8 seeds, and reports each
    recipe's own seed SD next to the baseline's.
"""
import json
import statistics as st
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from rsigap.gpu.analyze_gpu import summarise  # noqa: E402
from rsigap.gpu.loop_gpu import (BASELINE, BUDGET_S, LEDGER, TORCH_PY, WORK, harness_eval,  # noqa: E402
                                 seed_for)

EXTRA_RUN_SEEDS, EXTRA_BASE_SEEDS, IMPORT_EXCESS_S = 6, 4, 3.0
IMPORT_PROBE = ("import importlib.util,sys,time; p=sys.argv[1]; sys.path.insert(0, sys.argv[2]); t=time.time(); "
                "s=importlib.util.spec_from_file_location('m', p); m=importlib.util.module_from_spec(s); "
                "s.loader.exec_module(m); print(time.time()-t)")


def import_s(py: Path) -> float | None:
    py = Path(py).resolve()
    p = subprocess.run([str(TORCH_PY), "-c", IMPORT_PROBE, str(py), str(py.parent)], capture_output=True,
                       text=True, timeout=600, cwd=py.parent)
    try:
        return float(p.stdout.strip().splitlines()[-1])
    except Exception:  # noqa: BLE001
        return None


def main():
    phase = sys.argv[1] if len(sys.argv) > 1 else "main"
    raw = ROOT / "runs" / f"gpu_posthoc_{phase}.jsonl"
    recs = [json.loads(x) for x in LEDGER.read_text().splitlines()]
    its = [r for r in recs if r.get("kind") == "iteration" and r["phase"] == phase]
    base = next(r for r in recs if r.get("kind") == "baseline" and r["phase"] in (phase, "main"))
    out = {"phase": phase, "exploratory": True}

    # C1: import time of every snapshotted recipe vs the baseline recipe
    ref = st.median([import_s(BASELINE) or 0 for _ in range(3)])
    c1 = {}
    for r in its:
        py = ROOT / "runs" / phase / r["run_id"] / f"iter_{r['t']}" / "ws" / "train.py"
        s = import_s(py) if py.exists() else None
        c1[f"{r['run_id']}@{r['t']}"] = {"import_s": s, "excess_s": None if s is None else s - ref,
                                         "untimed_import_work": s is not None and s - ref > IMPORT_EXCESS_S}
    out["C1_import"] = {"baseline_import_s": ref, "per_iteration": c1}

    # C2: harness runs that used the grace window
    c2 = {}
    for arm in ("self", "external"):
        ts = [x.get("train_s") for r in its if r["arm"] == arm for x in r["truth"] + r["dev"] if x.get("train_s")]
        c2[arm] = {"n": len(ts), "over_budget": sum(t > BUDGET_S for t in ts), "max_train_s": max(ts, default=None)}
    out["C2_grace"] = c2

    # C3: extra sealed-test seeds (appends raw results so a rerun can resume)
    done = {}
    if raw.exists():
        for line in raw.read_text().splitlines():
            d = json.loads(line)
            done[(d["who"], d["k"])] = d
    bws = WORK / "runs" / phase / "_posthoc_baseline" / "ws"
    bws.mkdir(parents=True, exist_ok=True)
    (bws / "train.py").write_text(BASELINE.read_text())
    jobs = [("_baseline", k, bws) for k in range(EXTRA_BASE_SEEDS)]
    final = {}
    for r in its:
        if r["t"] >= final.get(r["run_id"], {"t": 0})["t"]:
            final[r["run_id"]] = r
    for rid, r in final.items():
        jobs += [(rid, k, ROOT / "runs" / phase / rid / f"iter_{r['t']}" / "ws") for k in range(EXTRA_RUN_SEEDS)]
    with raw.open("a") as f:
        for who, k, ws in jobs:
            if (who, k) in done:
                continue
            res = harness_eval(ws, seed_for(who, "posthoc_test", k), "test")
            d = {"who": who, "k": k, **res}
            done[(who, k)] = d
            f.write(json.dumps(d) + "\n")
            f.flush()
            print(who, k, round(res["scored_bpb"], 4), flush=True)

    b8 = [x["scored_bpb"] for x in base["test"]] + [done[("_baseline", k)]["scored_bpb"] for k in range(EXTRA_BASE_SEEDS)]
    base8 = st.mean(b8)
    prim = summarise(phase)["runs"]
    c3 = {"baseline_test_8": {"mean": base8, "sd": st.stdev(b8)}, "runs": {}}
    for rid, r in final.items():
        t8 = [x["scored_bpb"] for x in r["truth"]] + [done[(rid, k)]["scored_bpb"] for k in range(EXTRA_RUN_SEEDS)]
        row = prim[rid]["rows"][-1]
        tg8 = base8 - st.mean(t8)
        c3["runs"][rid] = {"arm": r["arm"], "truth_8": st.mean(t8), "recipe_seed_sd": st.stdev(t8),
                           "TG_T_2seed": row["TG"], "TG_T_8seed": tg8,
                           "I_T_2seed": row["I"], "I_T_8seed": None if row["MG"] is None else row["MG"] - tg8}
    for arm in ("self", "external"):
        v = [x["I_T_8seed"] for x in c3["runs"].values() if x["arm"] == arm and x["I_T_8seed"] is not None]
        c3[f"I_T_8seed_mean_{arm}"] = st.mean(v) if v else None
    if c3["I_T_8seed_mean_self"] is not None and c3["I_T_8seed_mean_external"] is not None:
        c3["E1_8seed_diff"] = c3["I_T_8seed_mean_self"] - c3["I_T_8seed_mean_external"]
    out["C3_more_truth_seeds"] = c3

    dst = ROOT / "results" / f"gpu_posthoc_{phase}.json"
    dst.parent.mkdir(exist_ok=True)
    dst.write_text(json.dumps(out, indent=2))
    print(json.dumps({k: v for k, v in out.items() if k != "C1_import"}, indent=1))
    print("C1 flagged:", [k for k, v in c1.items() if v["untimed_import_work"]])
    print("wrote", dst)


if __name__ == "__main__":
    main()
