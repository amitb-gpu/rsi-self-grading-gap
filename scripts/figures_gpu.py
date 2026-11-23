"""v0.2 figures (enwik8 recipe loop) from runs/gpu_ledger.jsonl via rsigap.gpu.analyze_gpu.

  v02_measurement_ladder.png   every bpb measurement of the baseline and the pilot on one axis:
                               seed noise (the yardstick) next to the agent's own numbers
  v02_gains_<phase>.png        per run: true gain (sealed test) vs the loop's meter gain, by iteration
  v02_inflation_<phase>.png    E1: final-iteration inflation I_T per run, by arm, against +/- 1 seed SD

python scripts/figures_gpu.py [phase]     (phase default: main; the ladder always uses the pilot)
"""
import json
import sys
from pathlib import Path

import numpy as np
from figstyle import GRID, METER, STATED, SURFACE, TEXT, TEXT2, TRUTH, dot, plt, title

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from rsigap.gpu.analyze_gpu import summarise  # noqa: E402

OUT = ROOT / "docs" / "figures"
LEDGER = ROOT / "runs" / "gpu_ledger.jsonl"
ARM_NAME = {"self": "Self-graded loop", "external": "Externally graded loop"}


def ledger():
    return [json.loads(x) for x in LEDGER.read_text().splitlines()]


def ladder():
    recs = ledger()
    base = next(r for r in recs if r.get("kind") == "baseline" and r["phase"] == "main")
    pil = next((r for r in recs if r.get("kind") == "iteration" and r["phase"] == "pilot"), None)
    rows = [  # (label, values, color, marker, filled)
        ("baseline · test · 45 s (4 seeds)", [x["scored_bpb"] for x in base["test"]], TRUTH, "o", True),
        ("baseline · val · 45 s (4 seeds)", [x["scored_bpb"] for x in base["val"]], STATED, "o", True),
        ("baseline · test · 90 s (2 seeds)", [x["scored_bpb"] for x in base["test_scaled"]], TRUTH, "D", True),
    ]
    if pil:
        rep = pil["report"]
        rows += [
            ("agent's claimed baseline (a guess)", [rep["baseline_val_bpb"]], METER, "o", False),
            ("agent's own eval run (1 seed)", [e["bpb"] for e in pil["agent_evals"] if e.get("valid")], METER, "o", True),
            ("agent recipe · val · 45 s (harness, 2 seeds)", [x["scored_bpb"] for x in pil["dev"]], STATED, "o", True),
            ("agent recipe · test · 45 s (harness, 2 seeds)", [x["scored_bpb"] for x in pil["truth"]], TRUTH, "o", True),
            ("agent recipe · test · 90 s (harness)", [x["scored_bpb"] for x in pil["scaled"]], TRUTH, "D", True),
        ]
    rows = rows[::-1]
    fig, ax = plt.subplots(figsize=(10, 5.6))
    sd = float(np.std([x["scored_bpb"] for x in base["test"]], ddof=1))
    m = base["test_mean"]
    ax.axvspan(m - sd, m + sd, color=TRUTH, alpha=0.08, lw=0, zorder=0)
    ax.annotate(f"baseline test mean ± 1 seed SD ({sd:.3f} bpb)", (m + sd, len(rows) - 0.45), xytext=(-4, 0),
                textcoords="offset points", ha="right", fontsize=8.5, color=TEXT2)
    for y, (lab, vals, c, mk, filled) in enumerate(rows):
        for v in vals:
            if filled:
                dot(ax, v, y, c, marker=mk, ms=9 if mk == "o" else 8)
            else:
                ax.plot(v, y, mk, ms=9, mfc=SURFACE, mec=c, mew=2, zorder=3)
        if len(vals) > 1:
            ax.plot([np.mean(vals)] * 2, [y - 0.28, y + 0.28], color=TEXT, lw=1.5, zorder=2)
        ax.annotate(f"{np.mean(vals):.3f}", (min(vals), y), xytext=(9, 0), textcoords="offset points",
                    va="center", fontsize=9, color=TEXT)
    ax.set_yticks(range(len(rows)), [r[0] for r in rows], fontsize=10)
    ax.grid(axis="y", visible=False)
    if pil:
        ax.axhline(len(rows) - 3.5, color=GRID, lw=1)
    ax.set_xlabel("bits per byte on enwik8 (lower is better)")
    ax.invert_xaxis()
    top = title(fig, "v0.2 pilot: a real 0.40 bpb gain, and an agent that measured it badly",
                "Blue = sealed test (harness), aqua = validation (harness), orange = the agent's own numbers. "
                "Better is to the right; ticks mark means.")
    fig.tight_layout(rect=(0, 0, 1, top))
    fig.savefig(OUT / "v02_measurement_ladder.png")
    plt.close(fig)


def gains(res, phase):
    runs = res["runs"]
    if not runs:
        return
    order = sorted(runs, key=lambda k: (runs[k]["arm"] != "self", k))
    arms = [a for a in ("self", "external") if any(runs[k]["arm"] == a for k in order)]
    ncol = max(sum(runs[k]["arm"] == a for k in order) for a in arms)
    fig, axes = plt.subplots(len(arms), ncol, figsize=(max(10, 4.6 * ncol + 1), 3.6 * len(arms) + 1.4),
                             sharey=True, squeeze=False)
    sd = res["yardstick_1sd_bpb"]
    ymax = max([0.1] + [v for r in runs.values() for x in r["rows"] for v in (x["TG"], x["MG"] or 0)]) + 0.08
    ymin = min([0] + [v for r in runs.values() for x in r["rows"] for v in (x["TG"], x["MG"] or 0)]) - 0.05
    for i, arm in enumerate(arms):
        ks = [k for k in order if runs[k]["arm"] == arm]
        for j in range(ncol):
            ax = axes[i][j]
            if j >= len(ks):
                ax.set_visible(False)
                continue
            rows = runs[ks[j]]["rows"]
            xs = [0] + [x["t"] for x in rows]
            tg = [0] + [x["TG"] for x in rows]
            mg = [0] + [np.nan if x["MG"] is None else x["MG"] for x in rows]
            ax.fill_between(xs, np.array(tg) - sd, np.array(tg) + sd, color=TRUTH, alpha=0.08, lw=0)
            for ys, c, ls in ((tg, TRUTH, "-"), (mg, METER, (0, (4, 3)))):
                ax.plot(xs, ys, color=c, lw=2, ls=ls, solid_capstyle="round", zorder=2)
                dot(ax, xs[1:], ys[1:], c, ms=8)
            last = rows[-1]
            if last["I"] is not None:
                ax.annotate(f"I = {last['I']:+.3f}", (xs[-1], (tg[-1] + mg[-1]) / 2), xytext=(8, 0),
                            textcoords="offset points", va="center", fontsize=9, color=TEXT)
            ax.set_title(f"{ARM_NAME[arm]}, run {j + 1}", fontsize=11)
            ax.set_xticks(xs)
            ax.set_xlim(-0.2, xs[-1] + 0.9)
            ax.set_ylim(ymin, ymax)
            ax.axhline(0, color=TEXT2, lw=0.8, zorder=1)
            if i == len(arms) - 1:
                ax.set_xlabel("iteration (0 = baseline)")
            if j == 0:
                ax.set_ylabel("gain over baseline (bpb)")
    h = [plt.Line2D([], [], color=TRUTH, lw=2, marker="o", label="true gain (sealed test)"),
         plt.Line2D([], [], color=METER, lw=2, marker="o", label="meter gain (what the loop sees)"),
         plt.Rectangle((0, 0), 1, 1, color=TRUTH, alpha=0.15, label="± 1 baseline seed SD")]
    fig.legend(handles=h, loc="lower left", ncol=3, fontsize=9, bbox_to_anchor=(0.01, 0.0))
    top = title(fig, "What the loop thinks it gained vs what it really gained",
                "Meter: self arm = agent's claim; external arm = harness val shown to it. I = meter − true (bpb).")
    fig.tight_layout(rect=(0, 0.07, 1, top))
    fig.savefig(OUT / f"v02_gains_{phase}.png")
    plt.close(fig)


def inflation(res, phase):
    e1, sd = res["E1_final_inflation"], res["yardstick_1sd_bpb"]
    arms = [a for a in ("self", "external") if e1[a]]
    if not arms:
        return
    post = {}
    pf = ROOT / "results" / f"gpu_posthoc_{phase}.json"
    if pf.exists():
        for r in json.loads(pf.read_text())["C3_more_truth_seeds"]["runs"].values():
            if r["I_T_8seed"] is not None:
                post.setdefault(r["arm"], []).append(r["I_T_8seed"])
    fig, ax = plt.subplots(figsize=(9, 1.3 * len(arms) + 2))
    ax.axvspan(-sd, sd, color=TRUTH, alpha=0.08, lw=0)
    ax.axvline(0, color=TEXT2, lw=1)
    for y, arm in enumerate(arms[::-1]):
        vals = e1[arm]
        for v in vals:
            dot(ax, v, y, METER if arm == "self" else STATED)
        mu = float(np.mean(vals))
        ax.plot([mu, mu], [y - 0.3, y + 0.3], color=TEXT, lw=2)
        for v8 in post.get(arm, []):
            ax.plot(v8, y - 0.16, "o", ms=8, mfc=SURFACE, mec=METER if arm == "self" else STATED, mew=2, zorder=3)
        ax.annotate(f"mean {mu:+.3f}", (mu, y + 0.3), xytext=(0, 4), textcoords="offset points", ha="center",
                    fontsize=9, color=TEXT)
    ax.set_yticks(range(len(arms)), [ARM_NAME[a] for a in arms[::-1]])
    ax.set_ylim(-0.7, len(arms) - 0.3)
    ax.grid(axis="y", visible=False)
    lim = max([sd * 1.6] + [abs(v) * 1.25 for a in arms for v in e1[a]])
    ax.set_xlim(-lim, lim)
    ax.set_xlabel("final-iteration inflation I_T = meter gain − true gain (bpb)\n"
                  "right of 0: the loop overstates its progress · shaded: ± 1 baseline seed SD")
    if post:
        h = [plt.Line2D([], [], marker="o", ls="none", ms=8, color=TEXT2, mec=SURFACE, mew=2,
                        label="preregistered (2 truth seeds)"),
             plt.Line2D([], [], marker="o", ls="none", ms=8, mfc=SURFACE, mec=TEXT2, mew=2,
                        label="exploratory check C3 (8 truth seeds)")]
        ax.legend(handles=h, loc="upper left", fontsize=9)
    d = e1.get("diff")
    sub = (f"Self minus external = {d:+.3f} bpb = {d / sd:.2f} baseline seed SD "
           f"(the preregistered 'material' line is 1 SD). 2 runs per arm." if d is not None else "One arm only (preview).")
    top = title(fig, "E1: does a self-graded loop overstate its progress more?", sub)
    fig.tight_layout(rect=(0, 0, 1, top))
    fig.savefig(OUT / f"v02_inflation_{phase}.png")
    plt.close(fig)


def main():
    phase = sys.argv[1] if len(sys.argv) > 1 else "main"
    OUT.mkdir(parents=True, exist_ok=True)
    ladder()
    res = summarise(phase)
    gains(res, phase)
    inflation(res, phase)
    print("wrote", sorted(p.name for p in OUT.glob("v02_*")))


if __name__ == "__main__":
    main()
