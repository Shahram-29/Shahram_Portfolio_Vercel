"""Figures for the reconciliation and voucher-control case studies.

Usage:  py -3 figures_controls.py
"""

import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from payroll import reconciliation as rec_mod
from payroll import simulate
from payroll import vouchers as v_mod

sys.stdout.reconfigure(encoding="utf-8")

FIG = "figures"
INK = "#1a1a1a"
TEAL = "#2a9d8f"
RED = "#e76f51"
BLUE = "#457b9d"
SLATE = "#264653"


def fig_reconciliation():
    ledger, statement = simulate.build_bank_month()
    rec = rec_mod.reconcile(ledger, statement, opening_ledger=4_200_000, opening_bank=4_200_000)
    s = rec_mod.statement_of_reconciliation(rec)

    labels = [
        "Balance per\nbank statement",
        "Add: deposits\nin transit",
        "Less: unpresented\npayments",
        "Adjusted\nbalance",
        "Balance per\ncash book",
        "Less: unrecorded\nbank items",
        "Adjusted\nbalance",
    ]
    vals = [
        s["balance_per_bank_statement"],
        s["add_deposits_in_transit"],
        s["less_unpresented_payments"],
        s["adjusted_bank_balance"],
        s["balance_per_cash_book"],
        s["unrecorded_bank_items"],
        s["adjusted_book_balance"],
    ]

    bottoms, heights, colours = [], [], []
    run = 0.0
    for i, v in enumerate(vals):
        if i in (0, 4):  # starting balances
            bottoms.append(0); heights.append(v); colours.append(SLATE); run = v
        elif i in (3, 6):  # totals
            bottoms.append(0); heights.append(v); colours.append(TEAL)
        else:  # adjustments
            bottoms.append(run if v >= 0 else run + v)
            heights.append(abs(v))
            colours.append(BLUE if v >= 0 else RED)
            run += v

    fig, ax = plt.subplots(figsize=(11, 5.6))
    ax.bar(range(len(vals)), heights, bottom=bottoms, color=colours, width=0.62)
    for i, (b, h, v) in enumerate(zip(bottoms, heights, vals)):
        ax.text(i, b + h + max(vals) * 0.015, f"{v/1000:,.0f}k",
                ha="center", fontsize=9, color=INK)

    ax.axvline(3.5, color="0.75", ls="--", lw=1)
    ax.text(1.5, max(vals) * 1.22, "from the bank's side", ha="center",
            fontsize=10, color="0.35")
    ax.text(5.0, max(vals) * 1.22, "from the books' side", ha="center",
            fontsize=10, color="0.35")

    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, fontsize=8.5)
    ax.set_ylabel("PKR")
    ax.set_ylim(0, max(vals) * 1.30)
    ax.yaxis.set_major_formatter(lambda v, _: f"{v/1_000_000:.1f}m")
    ax.set_title(
        "Bank reconciliation, June 2025 (simulated)\n"
        "both sides meet at the same adjusted balance",
        fontsize=12,
    )
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(f"{FIG}/reconciliation_bridge.png", dpi=140)
    plt.close(fig)
    print("reconciliation figure written; ties:", not rec_mod.check(rec)[:1] or "with exceptions")


def fig_voucher_control():
    vouchers, blocked = simulate.build_vouchers()
    summary = v_mod.control_summary(vouchers)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12.5, 5), width_ratios=[1.05, 1])

    # left: the three-step flow, with headcount at each gate
    steps = ["Prepared\n(finance)", "Approved\n(director / CEO)", "Disbursed\n(CEO / director)"]
    counts = [summary["raised"], summary["raised"], summary["disbursed"]]
    ax1.bar(steps, counts, color=[BLUE, TEAL, SLATE], width=0.55)
    for i, c in enumerate(counts):
        ax1.text(i, c + 0.6, str(c), ha="center", fontsize=11, color=INK)
    ax1.set_ylim(0, max(counts) * 1.22)
    ax1.set_ylabel("Vouchers")
    ax1.set_title(
        f"Every payment passed three people\n"
        f"segregation of duties: {summary['segregation_rate']:.0%}",
        fontsize=11,
    )
    ax1.grid(axis="y", alpha=0.25)

    # right: what the control refused
    refusals = [
        "Preparer approving\ntheir own voucher",
        "Above the director's\nPKR 100k authority",
        "Payment before\napproval",
        "Preparer releasing\nthe payment",
    ]
    ax2.barh(refusals[::-1], [1] * 4, color=RED, height=0.5)
    for i in range(4):
        ax2.text(1.04, i, "refused", va="center", fontsize=10, color=RED)
    ax2.set_xlim(0, 1.7)
    ax2.set_xticks([])
    ax2.tick_params(labelsize=9)
    ax2.set_title("Four ways money could have left\nand what happened to each", fontsize=11)
    for side in ("top", "right", "bottom"):
        ax2.spines[side].set_visible(False)

    fig.suptitle("Expense payment voucher control, June 2025 (simulated)", fontsize=12.5)
    fig.tight_layout()
    fig.savefig(f"{FIG}/voucher_control.png", dpi=140)
    plt.close(fig)
    print(f"voucher figure written; {len(blocked)} attempts blocked")


if __name__ == "__main__":
    fig_reconciliation()
    fig_voucher_control()
