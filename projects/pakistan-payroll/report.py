"""Run the simulated year and produce the summary tables and figures.

Usage:  py -3 report.py
"""

import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from payroll import expenses, simulate, tax
from payroll.payslip import reconcile, register_totals, run_month

sys.stdout.reconfigure(encoding="utf-8")

FIG = "figures"
PKR = "PKR"


def run_year():
    company = simulate.build_company()
    overrides, raised_employee, new_monthly = company["raises"]
    rows = []
    for month in company["months"]:
        register = run_month(
            company["employees"],
            company["attendance"][month],
            overrides.get(month),
        )
        problems = reconcile(register)
        if problems:
            raise AssertionError(f"{month} did not reconcile: {problems[:3]}")
        rows.extend(register)
    return company, pd.DataFrame(rows), raised_employee, new_monthly


def fig_tax_curve():
    """Marginal and effective rate across the salary range."""
    salaries = list(range(0, 8_000_001, 10_000))
    marginal = [tax.marginal_rate(s) * 100 for s in salaries]
    effective = [tax.effective_rate(s) * 100 for s in salaries]

    fig, ax = plt.subplots(figsize=(10, 5.5))
    ax.step(salaries, marginal, where="post", label="Marginal rate", lw=2)
    ax.plot(salaries, effective, label="Effective rate", lw=2)
    for b in (600_000, 1_200_000, 2_200_000, 3_200_000, 4_100_000):
        ax.axvline(b, color="0.85", lw=0.8, zorder=0)
    ax.set_title(
        "Pakistan salaried income tax, Tax Year 2025\n"
        "marginal rate steps at each slab; effective rate never catches it",
        fontsize=12,
    )
    ax.set_xlabel(f"Annual taxable salary ({PKR})")
    ax.set_ylabel("Rate (%)")
    ax.set_xlim(0, 8_000_000)
    ax.set_ylim(0, 40)
    ax.xaxis.set_major_formatter(lambda v, _: f"{v/1_000_000:.0f}m")
    ax.legend(frameon=False)
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(f"{FIG}/tax_rate_curve.png", dpi=140)
    plt.close(fig)


def fig_payroll_bridge(df):
    """Where contractual salary goes before it reaches the bank."""
    totals = {
        "Contractual\ngross": df["contractual_gross"].sum(),
        "Unpaid leave": -df["unpaid_leave_deduction"].sum(),
        "Overtime": df["overtime_pay"].sum(),
        "Income tax": -df["income_tax"].sum(),
        "EOBI": -df["eobi"].sum(),
    }
    labels = list(totals) + ["Net pay"]
    values = list(totals.values())
    net = sum(values)

    running, bottoms, heights, colours = 0.0, [], [], []
    for i, v in enumerate(values):
        bottoms.append(running if v >= 0 else running + v)
        heights.append(abs(v))
        colours.append("#2a9d8f" if i == 0 else ("#e76f51" if v < 0 else "#457b9d"))
        running += v
    bottoms.append(0)
    heights.append(net)
    colours.append("#264653")

    fig, ax = plt.subplots(figsize=(10, 5.5))
    ax.bar(labels, heights, bottom=bottoms, color=colours)
    for i, (b, h) in enumerate(zip(bottoms, heights)):
        v = values[i] if i < len(values) else net
        ax.text(i, b + h + net * 0.012, f"{v/1_000_000:,.1f}m",
                ha="center", fontsize=9)
    ax.set_title(
        "Tax Year 2025 payroll bridge, 24 simulated employees\n"
        "contractual salary to cash paid",
        fontsize=12,
    )
    ax.set_ylabel(f"{PKR}")
    ax.yaxis.set_major_formatter(lambda v, _: f"{v/1_000_000:.0f}m")
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(f"{FIG}/payroll_bridge.png", dpi=140)
    plt.close(fig)


def fig_attendance_cost(df):
    """Unpaid absence by department, month by month."""
    pivot = df.pivot_table(
        index="month",
        columns="department",
        values="unpaid_leave_deduction",
        aggfunc="sum",
    ).fillna(0)

    fig, ax = plt.subplots(figsize=(10, 5.5))
    pivot.plot(kind="bar", stacked=True, ax=ax, width=0.78)
    ax.set_title(
        "Cost of unpaid absence by department\n"
        "Operations runs persistently higher than the rest",
        fontsize=12,
    )
    ax.set_xlabel("")
    ax.set_ylabel(f"Pay lost to unpaid leave ({PKR})")
    ax.yaxis.set_major_formatter(lambda v, _: f"{v/1_000:,.0f}k")
    ax.legend(title="", frameon=False, ncol=4, fontsize=9)
    ax.grid(axis="y", alpha=0.25)
    plt.xticks(rotation=45, ha="right")
    fig.tight_layout()
    fig.savefig(f"{FIG}/attendance_cost.png", dpi=140)
    plt.close(fig)


def fig_expenses(approved, rejected):
    """Approved spend by category, and why claims were rejected."""
    by_cat = expenses.spend_by_category(approved)
    reasons = {}
    for r in rejected:
        for reason in r["reasons"]:
            key = (
                "Over category limit" if "exceeds" in reason
                else "No receipt" if "receipt" in reason
                else "Outside 60-day window" if "window" in reason
                else "Dated before expense" if "before" in reason
                else "Other"
            )
            reasons[key] = reasons.get(key, 0) + 1

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    ax1.barh(list(by_cat)[::-1], [v / 1_000 for v in list(by_cat.values())[::-1]],
             color="#457b9d")
    ax1.set_title("Approved expense spend by category", fontsize=11)
    ax1.set_xlabel(f"{PKR} thousands")
    ax1.grid(axis="x", alpha=0.25)

    if reasons:
        ax2.barh(list(reasons)[::-1], list(reasons.values())[::-1], color="#e76f51")
    ax2.set_title("Why claims were rejected", fontsize=11)
    ax2.set_xlabel("Claims")
    ax2.grid(axis="x", alpha=0.25)

    fig.suptitle("Expense claims, Tax Year 2025 (simulated)", fontsize=12)
    fig.tight_layout()
    fig.savefig(f"{FIG}/expense_summary.png", dpi=140)
    plt.close(fig)


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
    print(f"Earned gross              {df['earned_gross'].sum():>18,.0f}")
    print(f"Income tax withheld       {df['income_tax'].sum():>18,.0f}")
    print(f"EOBI withheld             {df['eobi'].sum():>18,.0f}")
    print(f"Net paid                  {df['net_pay'].sum():>18,.0f}")
    print(f"Every month reconciled    yes")

    print("\nUnpaid absence by department")
    dept = df.groupby("department")["unpaid_leave_deduction"].sum().sort_values(ascending=False)
    for d, v in dept.items():
        share = v / df.loc[df.department == d, "contractual_gross"].sum()
        print(f"  {d:<14}{v:>14,.0f}   {share:>6.2%} of that team's payroll")

    print(f"\nMid-year raise: {raised.employee_id} ({raised.department})")
    old_m = df[(df.employee_id == raised.employee_id) & (df.month == "2024-12")]["income_tax"].iloc[0]
    new_m = df[(df.employee_id == raised.employee_id) & (df.month == "2025-01")]["income_tax"].iloc[0]
    print(f"  salary {raised.monthly_gross:,.0f} -> {new_monthly:,.0f} per month")
    print(f"  monthly tax {old_m:,.0f} -> {new_m:,.0f}  (+{(new_m/old_m - 1):.0%})")
    print(f"  marginal rate {tax.marginal_rate(raised.monthly_gross*12):.0%} "
          f"-> {tax.marginal_rate(new_monthly*12):.0%}")

    print(f"\nExpense claims            {len(company['claims'])}")
    print(f"  approved                {len(approved)}  {sum(r['amount'] for r in approved):,.0f}")
    print(f"  rejected                {len(rejected)}  {sum(r['amount'] for r in rejected):,.0f}")

    fig_tax_curve()
    fig_payroll_bridge(df)
    fig_attendance_cost(df)
    fig_expenses(approved, rejected)
    print(f"\nFigures written to {FIG}/")

    df.to_csv("data/payroll_register_ty2025.csv", index=False)
    print("Register written to data/payroll_register_ty2025.csv")


if __name__ == "__main__":
    main()
