"""Run the simulated year and produce the summary tables and figures.

Usage:  py -3 report.py
"""

import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from payroll import chart_theme as T
from payroll import expenses, simulate, tax, vouching
from payroll.payslip import reconcile, register_totals, run_month

sys.stdout.reconfigure(encoding="utf-8")
T.apply()

FIG = "figures"


def run_year():
    company = simulate.build_company()
    overrides, raised_employee, new_monthly = company["raises"]
    rows = []
    for month in company["months"]:
        register = run_month(
            company["employees"], company["attendance"][month], overrides.get(month)
        )
        problems = reconcile(register)
        if problems:
            raise AssertionError(f"{month} did not reconcile: {problems[:3]}")
        rows.extend(register)
    return company, pd.DataFrame(rows), raised_employee, new_monthly


def fig_tax_curve():
    """Step plus line — two different jobs, so two different marks."""
    salaries = np.arange(0, 8_000_001, 5_000)
    marginal = np.array([tax.marginal_rate(s) for s in salaries]) * 100
    effective = np.array([tax.effective_rate(s) for s in salaries]) * 100

    fig, ax = plt.subplots(figsize=(11, 5.6))
    for b in (600_000, 1_200_000, 2_200_000, 3_200_000, 4_100_000):
        ax.axvline(b, color="#2b3a3f", lw=0.9)
    ax.step(salaries, marginal, where="post", color=T.BLUE, lw=2.2)
    ax.plot(salaries, effective, color=T.ORANGE, lw=2.2)

    ax.annotate("Marginal — the rate on the next rupee", xy=(5_200_000, 35),
                xytext=(4_300_000, 38), color=T.BLUE, fontsize=10,
                arrowprops=dict(arrowstyle="-", color=T.BLUE, lw=0.9))
    ax.annotate("Effective — the rate on the whole salary", xy=(6_600_000, 24.5),
                xytext=(4_100_000, 20), color=T.ORANGE, fontsize=10,
                arrowprops=dict(arrowstyle="-", color=T.ORANGE, lw=0.9))

    ax.set_xlim(0, 8_000_000); ax.set_ylim(0, 42)
    ax.set_xlabel("Annual taxable salary (PKR)"); ax.set_ylabel("Rate (%)")
    ax.xaxis.set_major_formatter(lambda v, _: f"{v/1_000_000:.0f}m")
    ax.set_title(
        "Pakistan salaried income tax, Tax Year 2025\n"
        "purely marginal — the effective rate never catches the marginal one",
    )
    T.despine(ax)
    fig.tight_layout(); fig.savefig(f"{FIG}/tax_rate_curve.png", dpi=140); plt.close(fig)


def fig_payroll_bridge(df):
    """A waterfall: contractual salary to cash paid."""
    items = [
        ("Contractual\ngross", df["contractual_gross"].sum(), "start"),
        ("Unpaid\nleave", -df["unpaid_leave_deduction"].sum(), "delta"),
        ("Overtime", df["overtime_pay"].sum(), "delta"),
        ("Income\ntax", -df["income_tax"].sum(), "delta"),
        ("EOBI", -df["eobi"].sum(), "delta"),
        ("Net pay", 0, "total"),
    ]
    fig, ax = plt.subplots(figsize=(11, 5.6))
    run = 0.0
    for i, (label, value, kind) in enumerate(items):
        if kind == "start":
            ax.bar(i, value, color=T.NEUTRAL, width=0.6, edgecolor=T.SURFACE, linewidth=2)
            run = value
            top, shown = value, value
        elif kind == "total":
            ax.bar(i, run, color=T.TOTAL, width=0.6, edgecolor=T.SURFACE, linewidth=2)
            top, shown = run, run
        else:
            bottom = run if value >= 0 else run + value
            colour = T.POSITIVE if value >= 0 else T.NEGATIVE
            ax.bar(i, abs(value), bottom=bottom, color=colour, width=0.6,
                   edgecolor=T.SURFACE, linewidth=2)
            run += value
            top, shown = bottom + abs(value), value
        ax.text(i, top + df["contractual_gross"].sum() * 0.018,
                f"{shown/1_000_000:,.1f}m", ha="center", fontsize=10.5,
                color=T.INK if kind in ("start", "total") else
                (T.POSITIVE if shown >= 0 else T.NEGATIVE))

    ax.set_xticks(range(len(items)))
    ax.set_xticklabels([i[0] for i in items])
    ax.set_ylabel("PKR")
    ax.set_ylim(0, df["contractual_gross"].sum() * 1.12)
    ax.yaxis.set_major_formatter(lambda v, _: f"{v/1_000_000:.0f}m")
    ax.set_title("Tax Year 2025 payroll bridge — contractual salary to cash paid")
    T.despine(ax); ax.grid(axis="x", visible=False)
    fig.tight_layout(); fig.savefig(f"{FIG}/payroll_bridge.png", dpi=140); plt.close(fig)


def fig_attendance_cost(df):
    """A dot plot. The story is four values on one scale, not twelve stacks."""
    by_dept = df.groupby("department").agg(
        lost=("unpaid_leave_deduction", "sum"), gross=("contractual_gross", "sum")
    )
    by_dept["share"] = by_dept["lost"] / by_dept["gross"] * 100
    by_dept = by_dept.sort_values("share")

    fig, ax = plt.subplots(figsize=(11, 4.6))
    y = np.arange(len(by_dept))
    ax.hlines(y, 0, by_dept["share"], color="#2b3a3f", lw=1.6, zorder=1)
    colours = [T.NEGATIVE if v > 1.5 else T.NEUTRAL for v in by_dept["share"]]
    ax.scatter(by_dept["share"], y, s=190, color=colours, zorder=3,
               edgecolor=T.SURFACE, linewidth=2)
    for i, (share, lost) in enumerate(zip(by_dept["share"], by_dept["lost"])):
        ax.text(share + 0.13, i, f"{share:.2f}%   ({lost/1000:,.0f}k)",
                va="center", fontsize=10,
                color=T.NEGATIVE if share > 1.5 else T.INK_MUTED)

    ax.set_yticks(y); ax.set_yticklabels(by_dept.index)
    ax.set_xlabel("Pay lost to unpaid absence, as % of that team's payroll")
    ax.set_xlim(0, by_dept["share"].max() * 1.55)
    ax.set_title("Operations loses four times the share the other teams do")
    T.despine(ax, keep=("bottom",)); ax.grid(axis="y", visible=False)
    fig.tight_layout(); fig.savefig(f"{FIG}/attendance_cost.png", dpi=140); plt.close(fig)


def fig_expenses(approved, rejected):
    by_cat = expenses.spend_by_category(approved)
    reasons = {}
    for r in rejected:
        for reason in r["reasons"]:
            key = ("Over category limit" if "exceeds" in reason
                   else "No receipt" if "receipt" in reason
                   else "Outside 60-day window" if "window" in reason
                   else "Dated before expense" if "before" in reason else "Other")
            reasons[key] = reasons.get(key, 0) + 1

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12.5, 5))
    cats = list(by_cat)[::-1]
    vals = [v / 1000 for v in list(by_cat.values())[::-1]]
    ax1.barh(cats, vals, color=T.BLUE, height=0.6, edgecolor=T.SURFACE, linewidth=2)
    for i, v in enumerate(vals):
        ax1.text(v + max(vals) * 0.02, i, f"{v:,.0f}k", va="center",
                 fontsize=9.5, color=T.INK_MUTED)
    ax1.set_xlim(0, max(vals) * 1.18)
    ax1.set_title("Approved spend by category", fontsize=11.5)
    T.despine(ax1, keep=("left",)); ax1.grid(axis="y", visible=False)

    ks = list(reasons)[::-1]; vs = list(reasons.values())[::-1]
    ax2.barh(ks, vs, color=T.NEGATIVE, height=0.6, edgecolor=T.SURFACE, linewidth=2)
    for i, v in enumerate(vs):
        ax2.text(v + 0.12, i, str(v), va="center", fontsize=9.5, color=T.INK_MUTED)
    ax2.set_xlim(0, max(vs) * 1.25)
    ax2.set_title("Why claims were rejected", fontsize=11.5)
    T.despine(ax2, keep=("left",)); ax2.grid(axis="y", visible=False)

    fig.suptitle("Expense claims, Tax Year 2025 (simulated)", fontsize=13)
    fig.tight_layout(); fig.savefig(f"{FIG}/expense_summary.png", dpi=140); plt.close(fig)


def fig_vouching(lines, result):
    """Coverage as a line against its target, not twelve near-identical bars."""
    monthly = vouching.monthly_coverage(lines, result)
    months = list(monthly)
    values = [monthly[m] * 100 for m in months]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5, ), width_ratios=[1.8, 1])
    x = np.arange(len(months))
    ax1.axhspan(95, 100.6, color=T.AQUA, alpha=0.10, lw=0)
    ax1.axhline(95, color=T.AQUA, ls="--", lw=1.2)
    ax1.text(len(months) - 0.5, 95.4, "95% target", ha="right", fontsize=9.5, color=T.AQUA)
    ax1.plot(x, values, color=T.BLUE, lw=2.2, zorder=2)
    below = [i for i, v in enumerate(values) if v < 95]
    ax1.scatter(x, values, s=52, color=T.BLUE, zorder=3,
                edgecolor=T.SURFACE, linewidth=2)
    if below:
        ax1.scatter([x[i] for i in below], [values[i] for i in below], s=90,
                    color=T.NEGATIVE, zorder=4, edgecolor=T.SURFACE, linewidth=2)
    ax1.set_xticks(x); ax1.set_xticklabels(months, rotation=45, ha="right", fontsize=9)
    ax1.set_ylim(min(88, min(values) - 3), 100.8)
    ax1.set_ylabel("Expense value supported by a receipt (%)")
    ax1.set_title("Receipt coverage by month", fontsize=11.5)
    T.despine(ax1); ax1.grid(axis="x", visible=False)

    counts = {
        "No receipt": len(result.unvouched),
        "Unclaimed receipt": len(result.orphan_receipts),
        "Amount mismatch": len(result.amount_mismatches),
        "Receipt reused": len(result.reused_receipts),
    }
    ks = list(counts)[::-1]; vs = list(counts.values())[::-1]
    colours = [T.NEGATIVE if k == "Receipt reused" else T.NEUTRAL for k in ks]
    ax2.barh(ks, vs, color=colours, height=0.58, edgecolor=T.SURFACE, linewidth=2)
    for i, v in enumerate(vs):
        ax2.text(v + 0.18, i, str(v), va="center", fontsize=10, color=T.INK_MUTED)
    ax2.set_xlim(0, max(vs) * 1.3)
    ax2.set_title("Exceptions found", fontsize=11.5)
    T.despine(ax2, keep=("left",)); ax2.grid(axis="y", visible=False)

    fig.suptitle("Twelve-month expense vouching (simulated)", fontsize=13)
    fig.tight_layout(); fig.savefig(f"{FIG}/vouching_coverage.png", dpi=140); plt.close(fig)


def main():
    company, df, raised, new_monthly = run_year()
    approved, rejected = expenses.process(company["claims"])

    print("=" * 72)
    print("TAX YEAR 2025 PAYROLL — SIMULATED COMPANY")
    print("=" * 72)
    print(f"Headcount                 {df['employee_id'].nunique()}")
    print(f"Payslips produced         {len(df)}")
    print(f"Contractual gross         {df['contractual_gross'].sum():>18,.0f}")
    print(f"Lost to unpaid leave      {df['unpaid_leave_deduction'].sum():>18,.0f}")
    print(f"Overtime paid             {df['overtime_pay'].sum():>18,.0f}")
    print(f"Income tax withheld       {df['income_tax'].sum():>18,.0f}")
    print(f"Net paid                  {df['net_pay'].sum():>18,.0f}")
    print("Every month reconciled    yes")

    old_m = df[(df.employee_id == raised.employee_id) & (df.month == "2024-12")]["income_tax"].iloc[0]
    new_m = df[(df.employee_id == raised.employee_id) & (df.month == "2025-01")]["income_tax"].iloc[0]
    print(f"\nMid-year raise: {raised.employee_id} monthly tax "
          f"{old_m:,.0f} -> {new_m:,.0f}  (+{(new_m/old_m - 1):.0%})")

    lines, receipts = simulate.build_receipt_file(approved)
    vres = vouching.voucher_match(lines, receipts)
    vsum = vouching.summary(lines, receipts, vres)
    print(f"\nVouching: {vsum['expense_lines']} lines, {vsum['receipts_on_file']} receipts, "
          f"{vsum['value_coverage']:.1%} coverage, {vsum['exceptions']} exceptions")

    fig_tax_curve()
    fig_payroll_bridge(df)
    fig_attendance_cost(df)
    fig_expenses(approved, rejected)
    fig_vouching(lines, vres)
    print(f"\nFigures written to {FIG}/")

    df.to_csv("data/payroll_register_ty2025.csv", index=False)


if __name__ == "__main__":
    main()
