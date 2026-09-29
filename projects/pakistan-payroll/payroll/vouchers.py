"""Expense payment vouchers, with the internal control enforced in code.

The control is a three-way split of duties:

    prepare  ->  approve  ->  disburse
    (finance)    (director)   (CEO)

No one person can move money on their own. That is the whole point: the
person who writes the voucher cannot approve it, and the person who approves
it cannot release the cash.

Most of what follows is refusals. A control that cannot say no is not a
control, so each rule here blocks a specific way money could leave without
three people having touched it.
"""

from dataclasses import dataclass, field
from datetime import date
from enum import Enum


class Status(Enum):
    DRAFT = "draft"
    APPROVED = "approved"
    DISBURSED = "disbursed"
    REJECTED = "rejected"


class ControlBreach(Exception):
    """Raised when an action would break segregation of duties."""


# Approval authority. A director signs routine spend; anything larger needs
# the CEO's approval as well as their disbursement.
DIRECTOR_APPROVAL_LIMIT = 100_000  # PKR


@dataclass
class Voucher:
    voucher_no: str
    payee: str
    category: str
    amount: float
    raised_on: date
    prepared_by: str
    narrative: str = ""
    status: Status = Status.DRAFT
    approved_by: str | None = None
    approved_on: date | None = None
    approved_amount: float | None = None
    disbursed_by: str | None = None
    disbursed_on: date | None = None
    audit_trail: list = field(default_factory=list)

    def _log(self, action, who, when):
        self.audit_trail.append(
            {"action": action, "by": who, "on": when, "amount": self.amount}
        )


def prepare(voucher: Voucher):
    """Record the voucher as raised."""
    if voucher.amount <= 0:
        raise ControlBreach(
            f"{voucher.voucher_no}: amount must be positive, got {voucher.amount:,.2f}"
        )
    if not voucher.narrative.strip():
        raise ControlBreach(
            f"{voucher.voucher_no}: a voucher with no narrative cannot be approved "
            f"on its face — say what the payment is for"
        )
    voucher._log("prepared", voucher.prepared_by, voucher.raised_on)
    return voucher


def approve(voucher: Voucher, approver: str, on: date, is_ceo=False):
    """Director (or CEO) approves the voucher.

    Refuses self-approval, re-approval, and amounts above the director's
    authority unless the approver is the CEO.
    """
    if voucher.status is not Status.DRAFT:
        raise ControlBreach(
            f"{voucher.voucher_no}: cannot approve a voucher that is already "
            f"{voucher.status.value}"
        )
    if approver == voucher.prepared_by:
        raise ControlBreach(
            f"{voucher.voucher_no}: {approver} prepared this voucher and cannot "
            f"also approve it"
        )
    if voucher.amount > DIRECTOR_APPROVAL_LIMIT and not is_ceo:
        raise ControlBreach(
            f"{voucher.voucher_no}: PKR {voucher.amount:,.0f} is above the "
            f"director's limit of PKR {DIRECTOR_APPROVAL_LIMIT:,.0f} and needs "
            f"CEO approval"
        )
    if on < voucher.raised_on:
        raise ControlBreach(
            f"{voucher.voucher_no}: approved {on} but raised {voucher.raised_on} "
            f"— a voucher cannot be approved before it exists"
        )

    voucher.status = Status.APPROVED
    voucher.approved_by = approver
    voucher.approved_on = on
    voucher.approved_amount = voucher.amount  # freeze what was approved
    voucher._log("approved", approver, on)
    return voucher


def reject(voucher: Voucher, approver: str, on: date, reason: str):
    """Approver declines the voucher."""
    if voucher.status is not Status.DRAFT:
        raise ControlBreach(
            f"{voucher.voucher_no}: cannot reject a voucher that is "
            f"{voucher.status.value}"
        )
    voucher.status = Status.REJECTED
    voucher.audit_trail.append(
        {"action": "rejected", "by": approver, "on": on, "reason": reason}
    )
    return voucher


def disburse(voucher: Voucher, payer: str, on: date):
    """CEO releases the payment.

    This is the last gate, so it re-checks everything rather than trusting
    that the earlier steps were done properly.
    """
    if voucher.status is not Status.APPROVED:
        raise ControlBreach(
            f"{voucher.voucher_no}: cannot disburse a voucher that is "
            f"{voucher.status.value} — approval must come first"
        )
    if payer == voucher.prepared_by:
        raise ControlBreach(
            f"{voucher.voucher_no}: {payer} prepared this voucher and cannot "
            f"also release the payment"
        )
    if payer == voucher.approved_by:
        raise ControlBreach(
            f"{voucher.voucher_no}: {payer} approved this voucher and cannot "
            f"also release the payment"
        )
    if voucher.approved_amount is not None and (
        abs(voucher.amount - voucher.approved_amount) > 0.01
    ):
        raise ControlBreach(
            f"{voucher.voucher_no}: amount changed from "
            f"PKR {voucher.approved_amount:,.2f} to PKR {voucher.amount:,.2f} "
            f"after approval — must be re-approved"
        )
    if voucher.approved_on is not None and on < voucher.approved_on:
        raise ControlBreach(
            f"{voucher.voucher_no}: disbursed {on} but approved "
            f"{voucher.approved_on}"
        )

    voucher.status = Status.DISBURSED
    voucher.disbursed_by = payer
    voucher.disbursed_on = on
    voucher._log("disbursed", payer, on)
    return voucher


def find_duplicate_payments(vouchers, days=30):
    """Same payee, same amount, close together — the classic double payment."""
    paid = sorted(
        (v for v in vouchers if v.status is Status.DISBURSED),
        key=lambda v: (v.payee, v.amount, v.disbursed_on),
    )
    flagged = []
    for a, b in zip(paid, paid[1:]):
        if (
            a.payee == b.payee
            and abs(a.amount - b.amount) < 0.01
            and (b.disbursed_on - a.disbursed_on).days <= days
        ):
            flagged.append((a, b))
    return flagged


def control_summary(vouchers):
    """Evidence that the control operated, which is what an auditor asks for."""
    disbursed = [v for v in vouchers if v.status is Status.DISBURSED]
    three_party = [
        v
        for v in disbursed
        if len({v.prepared_by, v.approved_by, v.disbursed_by}) == 3
    ]
    return {
        "raised": len(vouchers),
        "approved": sum(1 for v in vouchers if v.status is Status.APPROVED),
        "disbursed": len(disbursed),
        "rejected": sum(1 for v in vouchers if v.status is Status.REJECTED),
        "value_disbursed": sum(v.amount for v in disbursed),
        "three_party_segregation": len(three_party),
        "segregation_rate": (len(three_party) / len(disbursed)) if disbursed else 0.0,
        "duplicates_flagged": len(find_duplicate_payments(vouchers)),
    }
