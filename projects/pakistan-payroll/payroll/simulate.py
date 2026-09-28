"""Generate a simulated company for Tax Year 2025.

Every employee, salary, absence and expense claim in here is invented. The
names are common Pakistani names chosen at random and do not refer to anyone.
No data from any real employer is used anywhere in this project.

Deliberate quirks are built in so the reporting has something to find:
  - one employee crosses a tax slab mid-year after a raise
  - one department runs persistent unpaid absence
  - a handful of expense claims breach policy in different ways
"""

import random
from datetime import date, timedelta

from payroll.attendance import MonthAttendance
from payroll.expenses import CATEGORY_LIMITS, ExpenseClaim
from payroll.payslip import Employee

# Tax Year 2025 runs July 2024 to June 2025.
MONTHS = [
    "2024-07", "2024-08", "2024-09", "2024-10", "2024-11", "2024-12",
    "2025-01", "2025-02", "2025-03", "2025-04", "2025-05", "2025-06",
]

# Working days per month, after weekends and public holidays.
WORKING_DAYS = {
    "2024-07": 23, "2024-08": 21, "2024-09": 21, "2024-10": 23,
    "2024-11": 21, "2024-12": 22, "2025-01": 22, "2025-02": 20,
    "2025-03": 20, "2025-04": 21, "2025-05": 21, "2025-06": 20,
}

FIRST_NAMES = [
    "Ahmed", "Fatima", "Bilal", "Ayesha", "Usman", "Zainab", "Hassan", "Maryam",
    "Imran", "Sana", "Tariq", "Hira", "Kamran", "Nadia", "Faisal", "Rabia",
    "Salman", "Amna", "Zeeshan", "Iqra", "Adnan", "Sadia", "Waqas", "Bushra",
]
LAST_NAMES = [
    "Khan", "Ali", "Ahmed", "Malik", "Hussain", "Sheikh", "Butt", "Raza",
    "Siddiqui", "Qureshi", "Farooq", "Javed",
]

DEPARTMENTS = {
    "Engineering": (180_000, 420_000),
    "Finance": (120_000, 300_000),
    "Sales": (100_000, 260_000),
    "Operations": (80_000, 180_000),
}


def build_employees(n=24, seed=42):
    """Create the simulated headcount."""
    rng = random.Random(seed)
    employees = []
    used = set()
    depts = list(DEPARTMENTS)
    for i in range(n):
        while True:
            name = f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}"
            if name not in used:
                used.add(name)
                break
        dept = depts[i % len(depts)]
        low, high = DEPARTMENTS[dept]
        salary = round(rng.uniform(low, high), -3)
        employees.append(
            Employee(
                employee_id=f"E{i + 1:03d}",
                name=name,
                department=dept,
                monthly_gross=salary,
            )
        )
    return employees


def build_attendance(employees, seed=42):
    """Attendance for every employee for every month of the year."""
    rng = random.Random(seed + 1)
    records = {}
    for month in MONTHS:
        wd = WORKING_DAYS[month]
        month_records = []
        for emp in employees:
            # Operations carries persistent unpaid absence; everyone else is
            # mostly present with occasional paid leave.
            if emp.department == "Operations":
                unpaid = rng.choices([0, 1, 2, 3], weights=[55, 25, 13, 7])[0]
            else:
                unpaid = rng.choices([0, 1, 2], weights=[88, 9, 3])[0]
            paid = rng.choices([0, 1, 2], weights=[75, 18, 7])[0]
            paid = min(paid, wd - unpaid)
            present = wd - paid - unpaid
            overtime = (
                round(rng.uniform(0, 18), 1)
                if emp.department in ("Engineering", "Operations") and rng.random() < 0.45
                else 0.0
            )
            month_records.append(
                MonthAttendance(
                    employee_id=emp.employee_id,
                    month=month,
                    working_days=wd,
                    days_present=present,
                    paid_leave_days=paid,
                    unpaid_leave_days=unpaid,
                    overtime_hours=overtime,
                )
            )
        records[month] = month_records
    return records


def build_raises(employees):
    """A mid-year raise that pushes one employee into a higher tax slab.

    Returns {month: {employee_id: new_annual_taxable_income}}, applied from
    January 2025 onward.
    """
    target = next(e for e in employees if e.department == "Finance")
    new_monthly = target.monthly_gross * 1.35
    from_month = "2025-01"
    overrides = {}
    for month in MONTHS[MONTHS.index(from_month):]:
        overrides[month] = {target.employee_id: new_monthly * 12}
    return overrides, target, new_monthly


def build_expense_claims(employees, seed=42):
    """Expense claims across the year, including deliberate policy breaches."""
    rng = random.Random(seed + 2)
    categories = ["travel", "fuel", "meals", "equipment", "internet", "other"]
    claims = []
    cid = 0
    for month in MONTHS:
        year, mm = (int(x) for x in month.split("-"))
        for emp in employees:
            for _ in range(rng.choices([0, 1, 2, 3], weights=[35, 40, 18, 7])[0]):
                cid += 1
                cat = rng.choice(categories)
                # Draw against the category's own limit so most claims are
                # within policy, as they are in a real company. About 6% are
                # drawn deliberately over, which is what the checks catch.
                limit = CATEGORY_LIMITS[cat]
                if rng.random() < 0.06:
                    amount = round(rng.uniform(1.05, 1.6) * limit, -2)
                else:
                    amount = round(rng.uniform(0.05, 0.85) * limit, -2)
                incurred = date(year, mm, rng.randint(1, 28))
                submitted = incurred + timedelta(days=rng.randint(1, 20))
                has_receipt = rng.random() > 0.04
                claims.append(
                    ExpenseClaim(
                        claim_id=f"C{cid:05d}",
                        employee_id=emp.employee_id,
                        month=month,
                        category=cat,
                        amount=amount,
                        incurred_on=incurred,
                        submitted_on=submitted,
                        has_receipt=has_receipt,
                    )
                )

    # Deliberate breaches, one of each kind, so the checks have something to catch.
    e = employees[0].employee_id
    claims += [
        ExpenseClaim("C90001", e, "2025-03", "meals", 18_000,
                     date(2025, 3, 4), date(2025, 3, 9), True),          # over limit
        ExpenseClaim("C90002", e, "2025-03", "travel", 22_000,
                     date(2025, 3, 6), date(2025, 3, 10), False),        # no receipt
        ExpenseClaim("C90003", e, "2025-04", "fuel", 9_000,
                     date(2024, 12, 2), date(2025, 4, 15), True),        # stale
        ExpenseClaim("C90004", e, "2025-05", "equipment", 95_000,
                     date(2025, 5, 3), date(2025, 5, 8), True),          # needs escalation
    ]
    return claims


def build_company(seed=42):
    """Everything the reporting needs, in one call."""
    employees = build_employees(seed=seed)
    return {
        "employees": employees,
        "attendance": build_attendance(employees, seed=seed),
        "raises": build_raises(employees),
        "claims": build_expense_claims(employees, seed=seed),
        "months": MONTHS,
    }
