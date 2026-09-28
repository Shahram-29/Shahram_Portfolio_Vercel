"""Expense claims: policy checks, approval routing and reimbursement.

The point of the checks is that they run before payment, not after. Each rule
returns a reason string so a rejected claim can be explained to the claimant.
"""

from dataclasses import dataclass
from datetime import date

# Company policy. Kept here so the limits are visible rather than buried
# in the checking code.
CATEGORY_LIMITS = {
    "travel": 50_000,
    "fuel": 25_000,
    "meals": 10_000,
    "equipment": 100_000,
    "internet": 8_000,
    "other": 15_000,
}
RECEIPT_REQUIRED_ABOVE = 5_000
CLAIM_WINDOW_DAYS = 60  # claims must be submitted within this many days
APPROVAL_ESCALATION_ABOVE = 50_000  # above this, needs finance-head sign-off


@dataclass(frozen=True)
class ExpenseClaim:
    claim_id: str
    employee_id: str
    month: str  # "YYYY-MM", the payroll month it would be reimbursed in
    category: str
    amount: float
    incurred_on: date
    submitted_on: date
    has_receipt: bool


def check_claim(claim: ExpenseClaim):
    """Return a list of policy breaches. Empty means the claim passes."""
    problems = []

    if claim.category not in CATEGORY_LIMITS:
        problems.append(f"unknown category '{claim.category}'")
    else:
        limit = CATEGORY_LIMITS[claim.category]
        if claim.amount > limit:
            problems.append(
                f"{claim.category} claim of PKR {claim.amount:,.0f} exceeds the "
                f"PKR {limit:,.0f} limit"
            )

    if claim.amount <= 0:
        problems.append("claim amount must be positive")

    if claim.amount > RECEIPT_REQUIRED_ABOVE and not claim.has_receipt:
        problems.append(
            f"no receipt, required above PKR {RECEIPT_REQUIRED_ABOVE:,.0f}"
        )

    if claim.submitted_on < claim.incurred_on:
        problems.append("submitted before the expense was incurred")
    else:
        age = (claim.submitted_on - claim.incurred_on).days
        if age > CLAIM_WINDOW_DAYS:
            problems.append(
                f"submitted {age} days after the expense, window is "
                f"{CLAIM_WINDOW_DAYS} days"
            )

    return problems


def approval_level(claim: ExpenseClaim):
    """Who has to sign the claim off."""
    return "finance_head" if claim.amount > APPROVAL_ESCALATION_ABOVE else "line_manager"


def process(claims):
    """Split claims into approved and rejected, with reasons."""
    approved, rejected = [], []
    for claim in claims:
        problems = check_claim(claim)
        record = {
            "claim_id": claim.claim_id,
            "employee_id": claim.employee_id,
            "month": claim.month,
            "category": claim.category,
            "amount": claim.amount,
            "approval_level": approval_level(claim),
        }
        if problems:
            rejected.append({**record, "reasons": problems})
        else:
            approved.append(record)
    return approved, rejected


def reimbursements_by_employee(approved, month):
    """Total approved reimbursement per employee for one payroll month."""
    totals = {}
    for row in approved:
        if row["month"] == month:
            totals[row["employee_id"]] = totals.get(row["employee_id"], 0.0) + row["amount"]
    return totals


def spend_by_category(approved, month=None):
    """Approved spend grouped by category, optionally for a single month.

    This is the summary the pivot table produced in the original workbook.
    """
    totals = {}
    for row in approved:
        if month is None or row["month"] == month:
            totals[row["category"]] = totals.get(row["category"], 0.0) + row["amount"]
    return dict(sorted(totals.items(), key=lambda kv: -kv[1]))
