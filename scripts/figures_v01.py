"""v0.1 figure: per-target sealed held-out pass rate vs the agent's own test suite and its stated
estimate (last pilot iteration per target, from runs/ledger.jsonl).

python scripts/figures_v01.py  ->  docs/figures/v01_ceiling.png
"""
import json
import statistics as st
from pathlib import Path

import numpy as np
from figstyle import METER, STATED, TEXT, TEXT2, TRUTH, dot, plt, title

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "figures"


def rows():
    last = {}
    for line in (ROOT / "runs" / "ledger.jsonl").read_text().splitlines():
        r = json.loads(line)
        last[r["task"]] = r
    out = []
    for t, r in last.items():
        out.append({"task": t, "held": 100 * r["heldout"]["score"],
                    "own": 100 * r["own"]["score"] if r["own"].get("score") is not None else None,
                    "n_own": r["own"]["n"],
                    "est": 100 * r["report"]["estimated_pass_rate"]})
    return sorted(out, key=lambda x: (x["held"], x["est"]))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rs = rows()
    fig, ax = plt.subplots(figsize=(9.5, 6.4))
    ys = np.arange(len(rs))
    for y, r in zip(ys, rs):
        lo, hi = min(r["est"], r["held"]), max(r["est"], r["held"])
        ax.plot([lo, hi], [y, y], color=TEXT2, lw=1, alpha=0.5, zorder=1)
        dot(ax, r["est"], y, STATED)
        if r["own"] is not None:
            dot(ax, r["own"], y + 0.34, METER, ms=7, marker="s")
        dot(ax, r["held"], y, TRUTH)
        if r["own"] is not None and r["own"] - r["held"] > 2:
            ax.annotate(f"own suite says {r['own']:.0f}%,\nheld-out {r['held']:.1f}%",
                        (r["held"], y), xytext=(10, 0), textcoords="offset points", va="center",
                        fontsize=8.5, color=TEXT2)
    ax.set_yticks(ys, [r["task"] for r in rs], fontsize=10)
    ax.grid(axis="y", visible=False)
    ax.set_xlim(70, 101.5)
    ax.set_ylim(-0.6, len(rs) - 0.2)
    ax.set_xlabel("pass rate (%)  —  exact match to CPython 3.12.7 output")
    h = [plt.Line2D([], [], marker=m, ls="none", color=c, ms=8, label=lab) for m, c, lab in (
        ("o", TRUTH, "sealed held-out set (1000 cases, never seen)"),
        ("s", METER, "agent's own test suite (self arm, ≥30 cases)"),
        ("o", STATED, "agent's stated estimate in its report"))]
    ax.legend(handles=h, loc="upper left", fontsize=9.5)
    gap = st.mean(r["held"] - r["est"] for r in rs)
    top = title(fig, "v0.1: at ceiling on all 13 targets, and the agent underrated itself",
          f"{len(rs)} CPython stdlib functions reimplemented from memory. Mean held-out {st.mean(r['held'] for r in rs):.1f}%, "
          f"mean self-estimate {st.mean(r['est'] for r in rs):.1f}% (underestimate {gap:.1f} pp).")
    fig.tight_layout(rect=(0, 0, 1, top))
    fig.savefig(OUT / "v01_ceiling.png")
    print("wrote", OUT / "v01_ceiling.png")


if __name__ == "__main__":
    main()
