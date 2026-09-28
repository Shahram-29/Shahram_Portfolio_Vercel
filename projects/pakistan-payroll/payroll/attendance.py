"""Attendance to payable pay.

The rule the payroll actually has to implement: gross salary is contractual,
but what gets paid depends on attendance. Paid leave does not reduce pay;
unpaid leave does, pro-rated on working days rather than calendar days.
Overtime is paid at a multiple of the ordinary hourly rate.
"""

from dataclasses import dataclass

# Hours in a standard working day, used to derive the hourly rate.
STANDARD_DAY_HOURS = 8
OVERTIME_MULTIPLIER = 1.5

# Paid leave entitlement per year under the Shops and Establishments rules
# commonly applied; the company policy value lives here so it is visible.
ANNUAL_PAID_LEAVE_DAYS = 14


@dataclass(frozen=True)
class MonthAttendance:
    """One employee's attendance for one month."""

    employee_id: str
    month: str  # "YYYY-MM"
    working_days: int  # working days in the month, excluding weekends/holidays
    days_present: int
    paid_leave_days: int = 0
    unpaid_leave_days: int = 0
    overtime_hours: float = 0.0

    def __post_init__(self):
        accounted = self.days_present + self.paid_leave_days + self.unpaid_leave_days
        if accounted != self.working_days:
            raise ValueError(
                f"{self.employee_id} {self.month}: days present ({self.days_present}) "
                f"+ paid leave ({self.paid_leave_days}) + unpaid leave "
                f"({self.unpaid_leave_days}) = {accounted}, but the month has "
                f"{self.working_days} working days"
            )
        if self.working_days <= 0:
            raise ValueError(f"{self.employee_id} {self.month}: working_days must be positive")


def payable_days(att: MonthAttendance):
    """Days the employee is paid for: attendance plus paid leave."""
    return att.days_present + att.paid_leave_days


def attendance_factor(att: MonthAttendance):
    """Share of the month's contractual salary that is payable."""
    return payable_days(att) / att.working_days


def hourly_rate(monthly_gross, working_days):
    """Ordinary hourly rate derived from the monthly contractual salary."""
    return monthly_gross / (working_days * STANDARD_DAY_HOURS)


def overtime_pay(monthly_gross, att: MonthAttendance, multiplier=OVERTIME_MULTIPLIER):
    """Overtime payable for the month."""
    if att.overtime_hours <= 0:
        return 0.0
    return hourly_rate(monthly_gross, att.working_days) * att.overtime_hours * multiplier


def earned_gross(monthly_gross, att: MonthAttendance):
    """Gross actually earned: salary scaled by attendance, plus overtime.

    Returned split out so a payslip can show the deduction rather than only
    the net figure — an employee who lost a day's pay should be able to see
    which day and how much.
    """
    base = monthly_gross * attendance_factor(att)
    ot = overtime_pay(monthly_gross, att)
    return {
        "contractual_gross": monthly_gross,
        "unpaid_leave_deduction": monthly_gross - base,
        "attendance_adjusted_gross": base,
        "overtime_pay": ot,
        "earned_gross": base + ot,
    }
