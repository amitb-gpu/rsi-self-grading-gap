"""Figures from results/analysis_<phase>.json (written by rsigap.analyze).

fig1_trajectories.png  small multiples by arm: own-meter score vs sealed held-out score per
                       iteration (thin lines = runs, thick = mean)
fig2_inflation.png     per-pair final measured inflation difference (self - external), with
                       mean, bootstrap 95% CI and the preregistered practical margin
Usage: python scripts/figures.py [phase]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
# Reference palette (dataviz skill, light mode): categorical slots 1-2, text and surface tokens.
SURFACE, TEXT, TEXT2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
TRUTH, METER = "#2a78d6", "#eb6834"  # held-out truth = slot 1 blue, own meter = slot 2 orange
ARM_LABEL = {"external": "External grader (CPython-labelled dev set)",
             "self": "Self-grader (agent writes its own eval set)"}

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "axes.edgecolor": GRID, "axes.labelcolor": TEXT2, "xtick.color": TEXT2, "ytick.color": TEXT2,
    "text.color": TEXT, "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.8,
    "grid.linestyle": "-", "axes.spines.top": False, "axes.spines.right": False,
    "font.size": 11, "axes.titlesize": 12, "axes.titleweight": "semibold",
})


def line(ax, x, y, color, lw, alpha=1.0, end_marker=False, z=2):
    ax.plot(x, y, color=color, lw=lw, alpha=alpha, solid_capstyle="round", solid_joinstyle="round", zorder=z)
    if end_marker:
        ax.plot(x[-1], y[-1], "o", ms=8, color=color, mec=SURFACE, mew=2, zorder=z + 1)


def fig_trajectories(res: dict, out: Path) -> None:
    runs = list(res["runs"].values())
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.4), sharey=True)
    for ax, arm in zip(axes, ("external", "self")):
        rs = [r for r in runs if r["arm"] == arm]
        T = max((r["T"] for r in rs), default=5)
        xs = np.arange(1, T + 1)
        for key, color in (("h", TRUTH), ("m", METER)):
            mat = []
            for r in rs:
                ys = [p[key] for p in r["traj"]]
                ys = [np.nan if v is None else 100 * v for v in ys]
                line(ax, xs[:len(ys)], ys, color, 1.0, alpha=0.25, z=1)
                if len(ys) == T:
                    mat.append(ys)
            if mat:
                mean = np.nanmean(np.array(mat), axis=0)
                line(ax, xs, mean, color, 2.4, end_marker=True, z=3)
                lab = "own meter" if key == "m" else "held-out truth"
                ax.annotate(f"{lab}  {mean[-1]:.0f}%", (xs[-1], mean[-1]), xytext=(10, 0),
                            textcoords="offset points", va="center", color=TEXT, fontsize=10)
        ax.set_title(ARM_LABEL[arm], loc="left", color=TEXT)
        ax.set_xticks(xs)
        ax.set_xlabel("loop iteration (fresh session each)")
        ax.set_xlim(0.8, T + 1.6)
        ax.set_ylim(0, 102)
    axes[0].set_ylabel("pass rate (%)")
    n = res["n_runs"]
    fig.suptitle("What the loop's own meter says vs. what a sealed held-out set says",
                 x=0.01, ha="left", fontsize=13, fontweight="semibold")
    fig.text(0.01, 0.005, f"Thin lines: individual runs (n = {n}); thick: mean. "
             "Orange = own meter, blue = sealed held-out truth.", color=TEXT2, fontsize=9)
    fig.tight_layout(rect=(0, 0.03, 1, 0.95))
    fig.savefig(out, dpi=200)
    plt.close(fig)


def fig_inflation(res: dict, out: Path) -> None:
    p1 = res["P1_final_measured_inflation_self_minus_external"]
    pairs = []
    for rid, s in res["runs"].items():
        if s["arm"] != "self":
            continue
        e = res["runs"].get(rid.replace("__self__", "__external__"))
        if e:
            pairs.append((f"{s['task']} r{s['rep']}", 100 * (s["MI_T"] - e["MI_T"])))
    pairs.sort(key=lambda t: t[1])
    fig, ax = plt.subplots(figsize=(8, 0.42 * len(pairs) + 2.2))
    ys = np.arange(len(pairs))
    ax.scatter([v for _, v in pairs], ys, s=64, color=METER, edgecolors=SURFACE, linewidths=2, zorder=3)
    ax.set_yticks(ys, [n for n, _ in pairs])
    ax.axvline(0, color=TEXT2, lw=1, zorder=1)
    if p1.get("margin_pp") is not None:
        ax.axvline(p1["margin_pp"], color=TEXT2, lw=1, zorder=1)
        ax.annotate(f"margin {p1['margin_pp']:g} pp", (p1["margin_pp"], len(pairs) - 0.4), xytext=(4, 0),
                    textcoords="offset points", color=TEXT2, fontsize=9)
    if p1.get("n"):
        lo, hi = p1["ci95_pp"]
        ym = -1.2
        ax.plot([lo, hi], [ym, ym], color=TEXT, lw=2, solid_capstyle="round")
        ax.plot(p1["mean_pp"], ym, "D", ms=8, color=TEXT, mec=SURFACE, mew=2)
        ax.annotate(f"mean {p1['mean_pp']:.1f} pp  [95% CI {lo:.1f}, {hi:.1f}]  p = {p1['p_one_sided']:.3g}",
                    (hi, ym), xytext=(8, 0), textcoords="offset points", va="center", fontsize=9, color=TEXT)
        ax.set_ylim(-2, len(pairs))
    ax.set_xlabel("final measured inflation, self-graded minus externally graded (pp)\n"
                  "measured inflation = own-meter pass rate - sealed held-out pass rate")
    ax.set_title("H1: how much more the self-graded loop overstates its progress", loc="left", color=TEXT)
    fig.tight_layout()
    fig.savefig(out, dpi=200)
    plt.close(fig)


def main() -> None:
    phase = sys.argv[1] if len(sys.argv) > 1 else "main"
    res = json.loads((ROOT / "results" / f"analysis_{phase}.json").read_text())["primary_itt"]
    outdir = ROOT / "results"
    fig_trajectories(res, outdir / f"fig1_trajectories_{phase}.png")
    fig_inflation(res, outdir / f"fig2_inflation_{phase}.png")
    print("wrote figures to", outdir)


if __name__ == "__main__":
    main()
