"""Monthly payroll run: attendance and salary in, payslips and a register out."""

from dataclasses import dataclass

from payroll import attendance as att_mod
from payroll import tax as tax_mod

# Employee Old-Age Benefits Institution contribution, employee share.
# Capped on a notified minimum wage rather than on actual salary.
EOBI_EMPLOYEE_RATE = 0.01
EOBI_WAGE_CEILING = 37_000  # PKR per month, the notified minimum wage used for EOBI


@dataclass(frozen=True)
class Employee:
    employee_id: str
    name: str
    department: str
    monthly_gross: float  # contractual monthly salary, PKR


def eobi_employee_contribution(monthly_gross, ceiling=EOBI_WAGE_CEILING):
    """Employee EOBI contribution, charged on the capped wage."""
    return min(monthly_gross, ceiling) * EOBI_EMPLOYEE_RATE


def run_payslip(emp: Employee, att: att_mod.MonthAttendance, annual_taxable_override=None):
    """Produce one payslip.

    Tax is withheld on the *contractual* annual salary rather than on the
    month's earned pay, which is how section 149 withholding works in
    practice: the employer estimates the year and deducts a twelfth. Passing
    `annual_taxable_override` models a mid-year salary revision.
    """
    if att.employee_id != emp.employee_id:
        raise ValueError(
            f"attendance is for {att.employee_id} but employee is {emp.employee_id}"
        )

    earnings = att_mod.earned_gross(emp.monthly_gross, att)
    annual_taxable = (
        annual_taxable_override
        if annual_taxable_override is not None
        else emp.monthly_gross * 12
    )

    income_tax = tax_mod.monthly_withholding(annual_taxable)
    eobi = eobi_employee_contribution(emp.monthly_gross)
    deductions = income_tax + eobi
    net = earnings["earned_gross"] - deductions

    return {
        "employee_id": emp.employee_id,
        "name": emp.name,
        "department": emp.department,
        "month": att.month,
        "working_days": att.working_days,
        "days_present": att.days_present,
        "paid_leave_days": att.paid_leave_days,
        "unpaid_leave_days": att.unpaid_leave_days,
        "overtime_hours": att.overtime_hours,
        **earnings,
        "annual_taxable_income": annual_taxable,
        "income_tax": income_tax,
        "eobi": eobi,
        "total_deductions": deductions,
        "net_pay": net,
    }


def run_month(employees, attendances, annual_taxable_overrides=None):
    """Run payroll for one month and return the register as a list of payslips."""
    overrides = annual_taxable_overrides or {}
    by_id = {a.employee_id: a for a in attendances}
    register = []
    for emp in employees:
        if emp.employee_id not in by_id:
            raise ValueError(f"no attendance recorded for {emp.employee_id}")
        register.append(
            run_payslip(emp, by_id[emp.employee_id], overrides.get(emp.employee_id))
        )
    return register


def register_totals(register):
    """Control totals for a month, the figures that have to tie to the bank run."""
    keys = (
        "contractual_gross",
        "unpaid_leave_deduction",
        "overtime_pay",
        "earned_gross",
        "income_tax",
        "eobi",
        "total_deductions",
        "net_pay",
    )
    totals = {k: sum(row[k] for row in register) for k in keys}
    totals["headcount"] = len(register)
    return totals


def reconcile(register, tolerance=0.01):
    """Check the register ties: earned gross less deductions equals net pay.

    Returns a list of problems. An empty list means the run is safe to pay.
    """
    problems = []
    for row in register:
        expected = row["earned_gross"] - row["total_deductions"]
        if abs(expected - row["net_pay"]) > tolerance:
            problems.append(
                f"{row['employee_id']} {row['month']}: net pay {row['net_pay']:.2f} "
                f"does not equal earned gross less deductions {expected:.2f}"
            )
        if row["net_pay"] < 0:
            problems.append(
                f"{row['employee_id']} {row['month']}: negative net pay "
                f"{row['net_pay']:.2f} — deductions exceed earnings"
            )
    totals = register_totals(register)
    expected_net = totals["earned_gross"] - totals["total_deductions"]
    if abs(expected_net - totals["net_pay"]) > tolerance:
        problems.append(
            f"register total net {totals['net_pay']:.2f} does not tie to "
            f"{expected_net:.2f}"
        )
    return problems
