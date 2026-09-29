"""Figures for the research-track case studies.

Real market data where the project used it; clearly-labelled method diagrams
where the project's own results are not in hand. Nothing here invents a result.

Usage:  py -3 make_figures.py
"""

import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yfinance as yf

# The chart theme lives with the payroll project; both tracks share it so the
# whole site reads as one system.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "pakistan-payroll"))
from payroll import chart_theme as T  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
T.apply()

OUT = os.path.join(os.path.dirname(__file__), "..", "..", "public", "images", "projects")


def eli_lilly():
    d = yf.Ticker("LLY").history(period="6y", interval="1d")
    d.index = d.index.tz_localize(None)
    d = d[d.index >= "2021-01-01"]

    fig, ax = plt.subplots(figsize=(11.5, 5.6))
    ax.fill_between(d.index, d["Close"], color=T.AQUA, alpha=0.13, lw=0)
    ax.plot(d.index, d["Close"], color=T.AQUA, lw=1.9)

    for when, label in [("2022-05-13", "Mounjaro approved\ntype 2 diabetes"),
                        ("2023-11-08", "Zepbound approved\nchronic weight management")]:
        ts = pd.Timestamp(when)
        nearest = d.index[d.index.get_indexer([ts], method="nearest")][0]
        price = d.loc[nearest, "Close"]
        ax.axvline(nearest, color=T.ORANGE, ls="--", lw=1.2, alpha=0.85)
        ax.scatter([nearest], [price], s=70, color=T.ORANGE, zorder=4,
                   edgecolor=T.SURFACE, linewidth=2)
        ax.annotate(label, xy=(nearest, price), xytext=(nearest, d["Close"].max() * 0.86),
                    fontsize=9.5, color=T.ORANGE, ha="center",
                    arrowprops=dict(arrowstyle="-", color=T.ORANGE, lw=0.9, alpha=0.7))

    ax.set_title("Eli Lilly (LLY): a re-rating you can date\n"
                 "from conventional pharma stock to GLP-1 growth story")
    ax.set_ylabel("Share price (USD)")
    ax.margins(x=0.01)
    T.despine(ax); ax.grid(axis="x", visible=False)
    fig.tight_layout(); fig.savefig(f"{OUT}/res-eli-lilly.png", dpi=140); plt.close(fig)
    print("eli lilly:", len(d), "days")


def jpmorgan():
    d = yf.Ticker("JPM").history(period="6y", interval="1d")
    d.index = d.index.tz_localize(None)
    ret = d["Close"].pct_change().dropna() * 100

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11.5, 6.6), sharex=True)
    ax1.plot(d.index, d["Close"], color=T.BLUE, lw=1.8)
    ax1.set_ylabel("Price (USD)")
    ax1.set_title("JPMorgan Chase: why the stationarity test comes first")
    ax1.text(0.012, 0.9, "Price — trending, non-stationary.\n"
             "Regress on this and R² flatters a model that only predicts \"roughly yesterday\".",
             transform=ax1.transAxes, fontsize=9.5, color=T.INK_MUTED, va="top")
    T.despine(ax1); ax1.grid(axis="x", visible=False)

    ax2.axhline(0, color="#2b3a3f", lw=1)
    ax2.plot(ret.index, ret, color=T.AQUA, lw=0.65, alpha=0.9)
    ax2.set_ylabel("Daily return (%)")
    ax2.text(0.012, 0.94, "Returns — mean-reverting. This is the series worth modelling.",
             transform=ax2.transAxes, fontsize=9.5, color=T.INK_MUTED, va="top")
    T.despine(ax2); ax2.grid(axis="x", visible=False); ax2.margins(x=0.01)

    fig.tight_layout(); fig.savefig(f"{OUT}/res-jpmorgan.png", dpi=140); plt.close(fig)
    print("jpmorgan:", len(d), "days")


def bank_classifier():
    """Part-to-whole plus a matrix — schematic, labelled as such."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12.5, 5), width_ratios=[1, 1.15])

    ax1.barh([0], [88], color=T.NEUTRAL, height=0.42, edgecolor=T.SURFACE, linewidth=2)
    ax1.barh([0], [12], left=[88], color=T.AQUA, height=0.42,
             edgecolor=T.SURFACE, linewidth=2)
    ax1.text(44, 0, "88%  did not subscribe", ha="center", va="center",
             fontsize=11, color=T.INK)
    ax1.text(94, -0.42, "12%\nsubscribed", ha="center", va="top",
             fontsize=10.5, color=T.AQUA)
    ax1.set_xlim(0, 100); ax1.set_ylim(-1.1, 0.8)
    ax1.axis("off")
    ax1.text(50, 0.62, "The class balance is the problem", ha="center",
             fontsize=11.5, color=T.INK)
    ax1.text(50, -0.82, 'A model that answers "no" to everyone scores 88%\n'
             "accuracy and finds nobody.", ha="center", fontsize=10, color=T.ORANGE)

    grid = np.array([[0.88, 0.16], [0.14, 0.55]])
    ax2.imshow(grid, cmap=matplotlib.colors.LinearSegmentedColormap.from_list(
        "seq", T.SEQUENTIAL), vmin=0, vmax=1)
    labels = [["True negative\ncorrectly skipped", "False positive\nwasted call"],
              ["False negative\nlost deposit", "True positive\nthe ones that matter"]]
    for i in range(2):
        for j in range(2):
            ax2.text(j, i, labels[i][j], ha="center", va="center", fontsize=9.5,
                     color=T.INK)
    ax2.set_xticks([0, 1]); ax2.set_xticklabels(["Predicted no", "Predicted yes"])
    ax2.set_yticks([0, 1]); ax2.set_yticklabels(["Actually no", "Actually yes"])
    ax2.set_title("What the confusion matrix separates", fontsize=11.5)
    ax2.grid(visible=False)
    for s in ax2.spines.values():
        s.set_visible(False)

    fig.suptitle("Bank term-deposit classifier: reading the right metric  ·  schematic",
                 fontsize=12.5)
    fig.tight_layout(); fig.savefig(f"{OUT}/res-bank-classifier.png", dpi=140); plt.close(fig)
    print("bank classifier written")


def holdout_vs_cv():
    """A dumbbell — the gap between two paired values is the whole story."""
    models = ["Linear", "Ridge", "Lasso", "SVR", "Decision Tree", "Random Forest"]
    cv = [0.62, 0.63, 0.62, 0.71, 0.78, 0.83]
    hold = [0.61, 0.62, 0.61, 0.68, 0.59, 0.66]

    order = np.argsort([c - h for c, h in zip(cv, hold)])
    models = [models[i] for i in order]
    cv = [cv[i] for i in order]; hold = [hold[i] for i in order]
    y = np.arange(len(models))

    fig, ax = plt.subplots(figsize=(11.5, 5.2))
    for i, (c, h) in enumerate(zip(cv, hold)):
        wide = (c - h) > 0.08
        ax.plot([h, c], [i, i], color=T.NEGATIVE if wide else "#2b3a3f",
                lw=3 if wide else 2, zorder=1, solid_capstyle="round")
    ax.scatter(hold, y, s=150, color=T.ORANGE, zorder=3,
               edgecolor=T.SURFACE, linewidth=2, label="Hold-out R²")
    ax.scatter(cv, y, s=150, color=T.BLUE, zorder=3,
               edgecolor=T.SURFACE, linewidth=2, label="Cross-validated R²")
    for i, (c, h) in enumerate(zip(cv, hold)):
        if (c - h) > 0.08:
            ax.text((c + h) / 2, i - 0.34, f"−{c-h:.2f}", ha="center",
                    fontsize=9.5, color=T.NEGATIVE)

    ax.set_yticks(y); ax.set_yticklabels(models)
    ax.set_ylim(-0.6, len(models) - 0.25)   # headroom so the top gap label clears the title
    ax.set_xlabel("R²"); ax.set_xlim(0.5, 0.92)
    ax.legend(loc="lower right")
    ax.set_title("Why both scores get reported — schematic, not this project's results\n"
                 "tree models flatter themselves in cross-validation and fall away out of sample")
    T.despine(ax, keep=("bottom",)); ax.grid(axis="y", visible=False)
    fig.tight_layout(); fig.savefig(f"{OUT}/res-holdout-vs-cv.png", dpi=140); plt.close(fig)
    print("holdout vs cv written")


def predictpay():
    """Bars for value by bucket, a dot plot for ranked risk — schematic."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12.5, 5))

    buckets = ["0-30", "31-60", "61-90", "90+"]
    vals = [1_850, 920, 610, 430]
    ax1.bar(buckets, vals, color=T.NEUTRAL, width=0.58,
            edgecolor=T.SURFACE, linewidth=2)
    for i, v in enumerate(vals):
        ax1.text(i, v + 60, f"{v:,}k", ha="center", fontsize=9.5, color=T.INK_MUTED)
    ax1.set_ylim(0, max(vals) * 1.18)
    ax1.set_title("Sorted by how late it is\nthe ageing report", fontsize=11.5)
    ax1.set_xlabel("Days overdue"); ax1.set_ylabel("Value outstanding (000s)")
    T.despine(ax1); ax1.grid(axis="x", visible=False)

    names = ["Customer T", "Customer A", "Customer M", "Customer C", "Customer H"]
    risk = [0.22, 0.41, 0.64, 0.78, 0.91]
    y = np.arange(len(names))
    ax2.hlines(y, 0, risk, color="#2b3a3f", lw=1.6)
    colours = [T.NEGATIVE if r > 0.6 else T.NEUTRAL for r in risk]
    ax2.scatter(risk, y, s=170, color=colours, zorder=3,
                edgecolor=T.SURFACE, linewidth=2)
    for i, r in enumerate(risk):
        ax2.text(r + 0.035, i, f"{r:.0%}", va="center", fontsize=10,
                 color=T.NEGATIVE if r > 0.6 else T.INK_MUTED)
    ax2.set_yticks(y); ax2.set_yticklabels(names)
    ax2.set_xlim(0, 1.12); ax2.set_xlabel("Forecast probability of paying late")
    ax2.set_title("Sorted by who will not pay\nthe worklist", fontsize=11.5)
    T.despine(ax2, keep=("bottom",)); ax2.grid(axis="y", visible=False)

    fig.suptitle("PredictPay: the same ledger, ordered two ways  ·  schematic", fontsize=12.5)
    fig.tight_layout(); fig.savefig(f"{OUT}/res-predictpay.png", dpi=140); plt.close(fig)
    print("predictpay written")


def used_car():
    fig, ax = plt.subplots(figsize=(11.5, 5.2))
    ax.axis("off"); ax.grid(visible=False)

    raw = ['"2.0L 4cyl Turbo 248hp"', '"3.5L V6 295 hp"',
           '"1.6 TDI 115PS"', '"5.0L V8 460-hp"']
    parsed = [248, 295, 115, 460]

    ax.text(0.17, 0.95, "Listing specification (free text)", ha="center",
            fontsize=11, color=T.INK_MUTED, transform=ax.transAxes)
    ax.text(0.80, 0.95, "Parsed feature", ha="center",
            fontsize=11, color=T.INK_MUTED, transform=ax.transAxes)

    for i, (r, p) in enumerate(zip(raw, parsed)):
        y = 0.77 - i * 0.175
        ax.text(0.17, y, r, ha="center", fontsize=10.5, family="monospace",
                color=T.INK, transform=ax.transAxes,
                bbox=dict(boxstyle="round,pad=0.5", fc=T.PANEL, ec="#2b3a3f"))
        ax.annotate("", xy=(0.62, y), xytext=(0.36, y), xycoords="axes fraction",
                    arrowprops=dict(arrowstyle="->", color=T.AQUA, lw=1.8))
        ax.text(0.80, y, f"horsepower = {p}", ha="center", fontsize=11,
                color=T.AQUA, transform=ax.transAxes,
                bbox=dict(boxstyle="round,pad=0.5", fc="#0d2b23", ec=T.AQUA))

    ax.text(0.5, 0.045,
            "Left as a categorical string, almost every listing is unique and carries nothing.\n"
            "Parsed to a number, it becomes one of the strongest predictors of price.",
            ha="center", fontsize=10, color=T.INK_MUTED, transform=ax.transAxes)
    ax.set_title("Used car prices: the step that decides the result", fontsize=12.5)
    fig.tight_layout(); fig.savefig(f"{OUT}/res-used-car.png", dpi=140); plt.close(fig)
    print("used car written")


if __name__ == "__main__":
    eli_lilly()
    jpmorgan()
    bank_classifier()
    holdout_vs_cv()
    predictpay()
    used_car()
