"""Figures for the reconciliation and voucher-control case studies.

Usage:  py -3 figures_controls.py
"""

import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from payroll import chart_theme as T
from payroll import reconciliation as rec_mod
from payroll import simulate
from payroll import vouchers as v_mod

sys.stdout.reconfigure(encoding="utf-8")
T.apply()

FIG = "figures"


def fig_reconciliation():
    """A waterfall that starts at the opening balance, not at zero.

    Drawing 3,892k and 265k from a common zero makes the adjustments — the
    entire content of a reconciliation — invisible. The axis starts just below
    the smaller of the two balances so the steps are legible.
    """
    ledger, statement = simulate.build_bank_month()
    rec = rec_mod.reconcile(ledger, statement, opening_ledger=4_200_000, opening_bank=4_200_000)
    s = rec_mod.statement_of_reconciliation(rec)

    steps = [
        ("Balance per\nbank statement", s["balance_per_bank_statement"], "start"),
        ("Add: deposits\nin transit", s["add_deposits_in_transit"], "delta"),
        ("Less: unpresented\npayments", s["less_unpresented_payments"], "delta"),
        ("Adjusted", s["adjusted_bank_balance"], "total"),
        ("Balance per\ncash book", s["balance_per_cash_book"], "start"),
        ("Less: unrecorded\nbank items", s["unrecorded_bank_items"], "delta"),
        ("Adjusted", s["adjusted_book_balance"], "total"),
    ]

    # Work out the true extent of every bar, including the running total
    # during the adjustment steps, so nothing clips.
    tops, bottoms_seen, run = [], [], 0.0
    for _, value, kind in steps:
        if kind in ("start", "total"):
            run = value
            tops.append(value); bottoms_seen.append(value)
        else:
            lo, hi = sorted((run, run + value))
            tops.append(hi); bottoms_seen.append(lo)
            run += value
    hi_all, lo_all = max(tops), min(bottoms_seen)
    span = hi_all - lo_all
    floor = lo_all - span * 1.6
    ceiling = hi_all + span * 0.42
    lows = [v for _, v, kind in steps if kind != "delta"]

    fig, ax = plt.subplots(figsize=(11.5, 5.8))
    run = 0.0
    for i, (label, value, kind) in enumerate(steps):
        if kind in ("start", "total"):
            colour = T.NEUTRAL if kind == "start" else T.TOTAL
            ax.bar(i, value - floor, bottom=floor, color=colour, width=0.6,
                   edgecolor=T.SURFACE, linewidth=2)
            run = value
            ax.text(i, value + (ceiling - floor) * 0.02, f"{value/1000:,.0f}k",
                    ha="center", fontsize=10, color=T.INK)
        else:
            bottom = run if value >= 0 else run + value
            colour = T.POSITIVE if value >= 0 else T.NEGATIVE
            ax.bar(i, abs(value), bottom=bottom, color=colour, width=0.6,
                   edgecolor=T.SURFACE, linewidth=2)
            ax.text(i, bottom + abs(value) + (ceiling - floor) * 0.02,
                    f"{value/1000:+,.0f}k", ha="center", fontsize=10, color=colour)
            run += value

    ax.axhline(s["adjusted_bank_balance"], color=T.TOTAL, ls="--", lw=1, alpha=0.5)
    ax.axvline(3.5, color="#2b3a3f", lw=1)
    ax.text(1.5, 0.955, "from the bank's side", transform=ax.get_xaxis_transform(),
            ha="center", fontsize=10, color=T.INK_MUTED)
    ax.text(5.0, 0.955, "from the books' side", transform=ax.get_xaxis_transform(),
            ha="center", fontsize=10, color=T.INK_MUTED)

    ax.set_xticks(range(len(steps)))
    ax.set_xticklabels([s_[0] for s_ in steps], fontsize=9)
    ax.set_ylim(floor, ceiling)
    ax.set_ylabel("PKR")
    ax.yaxis.set_major_formatter(lambda v, _: f"{v/1_000_000:.2f}m")
    ax.set_title(
        "Bank reconciliation, June 2025 — both sides meet at 3.77m\n"
        "axis starts below the balances so the adjustments are visible",
        fontsize=12,
    )
    T.despine(ax)
    ax.grid(axis="x", visible=False)
    fig.tight_layout()
    fig.savefig(f"{FIG}/reconciliation_bridge.png", dpi=140)
    plt.close(fig)
    print("reconciliation figure written")


def fig_voucher_control():
    """A stat tile plus the refusals — not three identical bars.

    The left panel used to be three bars all reading 34, which is a stat tile
    that has not noticed. When the story is one number, the number is the chart.
    """
    vouchers, blocked = simulate.build_vouchers()
    summary = v_mod.control_summary(vouchers)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12.5, 5), width_ratios=[0.85, 1.15])

    T.hero(
        ax1,
        f"{summary['segregation_rate']:.0%}",
        "segregation of duties",
        f"all {summary['disbursed']} payments passed three\n"
        f"different people: prepare, approve, disburse",
    )

    refusals = [
        "Preparer approving\ntheir own voucher",
        "Above the director's\nPKR 100k authority",
        "Payment before\napproval",
        "Preparer releasing\nthe payment",
    ]
    y = range(len(refusals))
    ax2.barh(list(y), [1] * 4, color=T.NEGATIVE, height=0.42,
             edgecolor=T.SURFACE, linewidth=2)
    for i in y:
        ax2.text(1.05, i, "refused", va="center", fontsize=10.5, color=T.NEGATIVE)
    ax2.set_yticks(list(y))
    ax2.set_yticklabels(refusals[::-1] if False else refusals, fontsize=9.5)
    ax2.invert_yaxis()
    ax2.set_xlim(0, 1.75)
    ax2.set_xticks([])
    ax2.set_title("Four ways money could have left", fontsize=11.5)
    T.despine(ax2, keep=("left",))
    ax2.grid(visible=False)

    fig.suptitle("Expense payment voucher control, June 2025 (simulated)", fontsize=13)
    fig.tight_layout()
    fig.savefig(f"{FIG}/voucher_control.png", dpi=140)
    plt.close(fig)
    print(f"voucher figure written; {len(blocked)} attempts blocked")


if __name__ == "__main__":
    fig_reconciliation()
    fig_voucher_control()
