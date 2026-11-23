"""Shared matplotlib style for README/paper figures (dataviz reference palette, light mode)."""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

SURFACE, TEXT, TEXT2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
# Categorical slots 1-3 (validated all-pairs in light mode). Roles are fixed across every figure:
TRUTH = "#2a78d6"     # sealed / harness-measured truth          (slot 1, blue)
METER = "#eb6834"     # the loop's own meter / agent's claim      (slot 2, orange)
STATED = "#1baf7a"    # agent's stated estimate / external dev   (slot 3, aqua; always legend-labelled)

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "axes.edgecolor": GRID, "axes.labelcolor": TEXT2, "xtick.color": TEXT2, "ytick.color": TEXT2,
    "text.color": TEXT, "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.8,
    "axes.spines.top": False, "axes.spines.right": False, "axes.spines.left": False,
    "font.size": 11, "axes.titlesize": 12, "axes.titleweight": "bold", "axes.titlelocation": "left",
    "legend.frameon": False, "legend.fontsize": 10, "savefig.dpi": 200,
})


def dot(ax, x, y, color, ms=9, marker="o", z=3, **kw):
    """Data marker with a 2px surface ring so overlapping marks stay separable."""
    ax.plot(x, y, marker, ms=ms, color=color, mec=SURFACE, mew=2, zorder=z, linestyle="none", **kw)


def title(fig, text, sub=None):
    """Title + optional subtitle anchored in inches from the top; returns the top for tight_layout."""
    h = fig.get_figheight()
    fig.suptitle(text, x=0.01, y=1 - 0.12 / h, ha="left", va="top", fontsize=13, fontweight="bold")
    if sub:
        fig.text(0.01, 1 - 0.47 / h, sub, color=TEXT2, fontsize=10, ha="left", va="top")
    return 1 - (0.85 if sub else 0.55) / h
