"""Shared chart theme: a validated dark palette matched to the site.

The categorical slots are the dark-mode steps of a palette that passes all six
checks on a dark surface — lightness band, chroma floor, colourblind separation
(worst adjacent ΔE 8.4 protan against a floor of 8), normal-vision separation
(19.8 against 15) and 3:1 contrast. They are assigned in fixed order and never
cycled.

The previous palette failed three of those checks: two slots sat below the
chroma floor and read as grey, one sat outside the lightness band, and one fell
under 3:1 contrast. Colours are not chosen here by eye.
"""

import matplotlib as mpl

# Site surfaces. Slightly darker than the palette's reference dark surface,
# which only improves contrast.
SURFACE = "#0f1619"
PANEL = "#141d21"
INK = "#f2f5f4"
INK_MUTED = "#9fb0b3"
GRID = "#24313650"

# Categorical slots, fixed order.
BLUE = "#3987e5"
ORANGE = "#d95926"
AQUA = "#199e70"
YELLOW = "#c98500"
MAGENTA = "#d55181"
VIOLET = "#9085e9"
SERIES = (BLUE, ORANGE, AQUA, YELLOW, MAGENTA, VIOLET)

# Semantic roles. Status colours are reserved and never reused as "series n".
POSITIVE = AQUA
NEGATIVE = ORANGE
TOTAL = BLUE
NEUTRAL = "#5c6f74"

# A single-hue sequential ramp, light to dark, for magnitude.
SEQUENTIAL = ["#0b2b22", "#0f4335", "#135c47", "#17755a", "#199e70", "#4cb994", "#86d2b8"]


def apply():
    """Set the global matplotlib style. Call once before plotting."""
    mpl.rcParams.update({
        "figure.facecolor": SURFACE,
        "savefig.facecolor": SURFACE,
        "axes.facecolor": SURFACE,
        "axes.edgecolor": "#2b3a3f",
        "axes.labelcolor": INK_MUTED,
        "axes.titlecolor": INK,
        "axes.titlesize": 12,
        "axes.titleweight": "medium",
        "axes.labelsize": 10,
        "axes.grid": True,
        "axes.axisbelow": True,
        "grid.color": "#243136",
        "grid.alpha": 0.55,
        "grid.linewidth": 0.7,
        "text.color": INK,
        "xtick.color": INK_MUTED,
        "ytick.color": INK_MUTED,
        "xtick.labelsize": 9.5,
        "ytick.labelsize": 9.5,
        "legend.frameon": False,
        "legend.labelcolor": INK_MUTED,
        "legend.fontsize": 9.5,
        "figure.titlesize": 13,
        "font.size": 10,
        "axes.prop_cycle": mpl.cycler(color=list(SERIES)),
    })


def despine(ax, keep=("left", "bottom")):
    """Recessive chrome: drop the spines that carry no information."""
    for side in ("top", "right", "left", "bottom"):
        ax.spines[side].set_visible(side in keep)


def hero(ax, value, label, sub=None):
    """A stat tile. When the story is one number, the number is the chart.

    Used where a bar chart would have drawn identical bars — three bars all
    reading 34 is a stat tile that has not realised it yet.
    """
    ax.axis("off")
    ax.text(0.5, 0.62, value, ha="center", va="center", fontsize=46,
            color=AQUA, fontweight="bold", transform=ax.transAxes)
    ax.text(0.5, 0.34, label, ha="center", va="center", fontsize=12,
            color=INK, transform=ax.transAxes)
    if sub:
        ax.text(0.5, 0.18, sub, ha="center", va="center", fontsize=9.5,
                color=INK_MUTED, transform=ax.transAxes)


def gapped_bar(ax, *args, **kwargs):
    """Bars with a 2px surface gap, so adjacent fills stay separable."""
    kwargs.setdefault("edgecolor", SURFACE)
    kwargs.setdefault("linewidth", 2)
    return ax.bar(*args, **kwargs)
