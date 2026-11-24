"""Narrative one-image summary of the v0.2 mechanism, for a general audience (LinkedIn, 1080x1350).

All values are validation-split bpb from runs/gpu_ledger.jsonl (main phase), so 'before' and 'after'
are on the same scale: the harness's 4 baseline seeds vs the self-arm agents' single seed-1 baseline,
and the harness's 2 seeds per self-arm final recipe vs the agents' claimed numbers.

  python scripts/figure_linkedin.py   ->  docs/figures/linkedin_mechanism.png
"""
import json
from pathlib import Path

import numpy as np
from figstyle import METER, SURFACE, TEXT, TEXT2, TRUTH, dot, plt

ROOT = Path(__file__).resolve().parents[1]
recs = [json.loads(x) for x in (ROOT / "runs" / "gpu_ledger.jsonl").read_text().splitlines()]
base = next(r for r in recs if r.get("kind") == "baseline" and r["phase"] == "main")
finals = [r for r in recs if r.get("kind") == "iteration" and r["phase"] == "main" and r["arm"] == "self" and r["t"] == 3]

b_h = [x["scored_bpb"] for x in base["val"]]                       # harness, 4 seeds
b_ai = [r["report"]["baseline_val_bpb"] for r in finals]           # agent's one measurement, per run
a_h = [x["scored_bpb"] for r in finals for x in r["dev"]]          # harness, 2 seeds x 2 runs
a_ai = [r["report"]["claimed_val_bpb"] for r in finals]            # agent's claim, per run
mb_h, ma_h, mb_ai, ma_ai = map(np.mean, (b_h, a_h, b_ai, a_ai))

fig, ax = plt.subplots(figsize=(7.2, 9))
fig.subplots_adjust(left=0.13, right=0.97, top=0.80, bottom=0.17)
X_B, X_A, X_REAL, X_CLAIM = 0.0, 1.25, 2.05, 2.45

# dots: harness (blue) jittered left, AI (orange) right of each column
for xs, vals, c, off in ((X_B, b_h, TRUTH, -0.14), (X_B, b_ai, METER, 0.2), (X_A, a_h, TRUTH, -0.14), (X_A, a_ai, METER, 0.2)):
    jit = np.linspace(-0.07, 0.07, len(vals)) if len(vals) > 1 else [0]
    dot(ax, [xs + off + j for j in jit], vals, c, ms=13)
for xs, m in ((X_B, mb_h), (X_A, ma_h)):
    ax.plot([xs - 0.27, xs - 0.01], [m, m], color=TRUTH, lw=2.5, zorder=2)

# spread bracket for the 'before' measurements
lo, hi = min(b_h), max(b_h)
ax.plot([X_B - 0.36] * 2, [lo, hi], color=TEXT2, lw=1.5)
for y in (lo, hi):
    ax.plot([X_B - 0.39, X_B - 0.33], [y, y], color=TEXT2, lw=1.5)

# gain arrows
def arrow(x, y0, y1, c, label):
    ax.annotate("", (x, y1), (x, y0), arrowprops=dict(arrowstyle="-|>", color=c, lw=3, mutation_scale=22))
    ax.text(x, min(ma_h, ma_ai) - 0.018, label, ha="center", va="top", fontsize=11.5, color=TEXT, fontweight="bold")

arrow(X_REAL, mb_h, ma_h, TRUTH, "real\ngain")
arrow(X_CLAIM, mb_ai, ma_ai, METER, "claimed\ngain")
for y, c in ((mb_h, TRUTH), (mb_ai, METER)):
    ax.plot([X_B + 0.3, X_CLAIM + 0.08 if c == METER else X_REAL + 0.08], [y, y], color=c, lw=1, ls=(0, (2, 3)), zorder=1)
ax.axhspan(mb_h, mb_ai, xmin=0.79, xmax=0.99, color=METER, alpha=0.15, lw=0)

kw = dict(fontsize=12, color=TEXT, va="center")
ax.text(X_B + 0.33, mb_ai + 0.055, "The AI measured its starting\npoint once, and got an\nunlucky, too-high number", **kw)
ax.text(X_B - 0.33, lo - 0.05, "Measure it again and it lands\nanywhere in this range. A low draw\nwould have made the AI undersell itself.",
        fontsize=11, color=TEXT2, va="top")
ax.text(X_A - 0.05, ma_h + 0.11, "Its improved model:\nmeasured accurately", ha="center", **kw)
ax.text(X_CLAIM + 0.02, mb_ai + 0.04, "the extra 'gain'\ncame from the\nunlucky start", ha="center", fontsize=10.5, color=TEXT2, va="bottom")

ax.set_xticks([X_B, X_A], ["BEFORE\noriginal model", "AFTER\n3 rounds of AI changes"], fontsize=12, color=TEXT)
ax.set_xlim(-0.75, 2.75)
ax.set_ylim(1.5, 2.22)
ax.set_ylabel("prediction error (lower is better)", fontsize=12)
ax.grid(axis="x", visible=False)

fig.text(0.03, 0.975, "The AI measured its progress well.\nIt measured its starting point badly.",
         fontsize=19, fontweight="bold", va="top", linespacing=1.15)
fig.text(0.03, 0.875, "Self-graded runs of an AI improving a small text model. Each dot is one\n"
         "measurement on the same data.", fontsize=11.5, color=TEXT2, va="top")
h = [plt.Line2D([], [], marker="o", ls="none", ms=11, color=TRUTH, mec=SURFACE, mew=2,
                label="independent measurement (repeated)"),
     plt.Line2D([], [], marker="o", ls="none", ms=11, color=METER, mec=SURFACE, mew=2, label="the AI's own measurement")]
fig.legend(handles=h, loc="upper left", bbox_to_anchor=(0.02, 0.825), ncol=2, fontsize=10.5, handletextpad=0.2,
           columnspacing=1.2)
fig.text(0.03, 0.065, "Lesson: measure \"before\" as carefully as \"after\".", fontsize=14, fontweight="bold")
fig.text(0.03, 0.03, "github.com/amitb-gpu/rsi-self-grading-gap  ·  2 self-graded runs; values are bits per byte",
         fontsize=9.5, color=TEXT2)
fig.savefig(ROOT / "docs" / "figures" / "linkedin_mechanism.png", dpi=150)
print({k: round(float(v), 3) for k, v in dict(before_h=mb_h, before_ai=mb_ai, after_h=ma_h, after_ai=ma_ai).items()})
