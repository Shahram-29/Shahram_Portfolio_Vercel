"""Matching the expense register to the receipt file, twelve months of it.

A policy check asks whether a claim was *allowed*. Vouching asks whether a
document actually exists behind the money that left — a different question,
and the one an auditor puts first.

Four things can go wrong, and each is a different problem:

  - a line with no receipt          -> unsupported payment
  - a receipt nobody claimed        -> expense possibly never recorded
  - claim and receipt disagree      -> over- or under-claim
  - one receipt on two lines        -> the same cost paid twice

The last of those is the one worth catching, because it looks clean on every
other report.
"""

from dataclasses import dataclass
from datetime import date

# A claim may round or exclude tax against the receipt; beyond this the two
# genuinely disagree and someone has to say which is right.
AMOUNT_TOLERANCE = 1.00

# Receipts dated outside the claimed month are common and fine at a boundary,
# but a long gap means the receipt is probably for something else.
DATE_TOLERANCE_DAYS = 45


@dataclass(frozen=True)
class Receipt:
    receipt_no: str
    vendor: str
    amount: float
    receipt_date: date


@dataclass(frozen=True)
class ExpenseLine:
    line_id: str
    month: str  # "YYYY-MM"
    vendor: str
    amount: float
    expense_date: date
    receipt_no: str = ""  # the receipt the claimant says supports this line


@dataclass
class VouchingResult:
    matched: list
    unvouched: list  # expense lines with no supporting receipt
    orphan_receipts: list  # receipts never claimed against a line
    amount_mismatches: list  # (line, receipt, difference)
    date_mismatches: list  # (line, receipt, days apart)
    reused_receipts: list  # (receipt_no, [lines]) — same receipt twice


def voucher_match(lines, receipts):
    """Match every expense line to its receipt and classify the failures."""
    by_no = {r.receipt_no: r for r in receipts}
    claimed = {}

    matched, unvouched, amount_mismatches, date_mismatches = [], [], [], []

    for line in lines:
        receipt = by_no.get(line.receipt_no) if line.receipt_no else None
        if receipt is None:
            unvouched.append(line)
            continue

        claimed.setdefault(receipt.receipt_no, []).append(line)
        matched.append((line, receipt))

        diff = line.amount - receipt.amount
        if abs(diff) > AMOUNT_TOLERANCE:
            amount_mismatches.append((line, receipt, diff))

        gap = abs((line.expense_date - receipt.receipt_date).days)
        if gap > DATE_TOLERANCE_DAYS:
            date_mismatches.append((line, receipt, gap))

    orphans = [r for r in receipts if r.receipt_no not in claimed]
    reused = [(no, ls) for no, ls in claimed.items() if len(ls) > 1]

    return VouchingResult(
        matched=matched,
        unvouched=unvouched,
        orphan_receipts=orphans,
        amount_mismatches=amount_mismatches,
        date_mismatches=date_mismatches,
        reused_receipts=reused,
    )


def coverage(lines, result: VouchingResult):
    """Share of expense *value* supported by a receipt.

    Value rather than count, because ten small vouched claims do not offset
    one large unsupported one.
    """
    total = sum(l.amount for l in lines)
    if total == 0:
        return 1.0
    unsupported = sum(l.amount for l in result.unvouched)
    return (total - unsupported) / total


def monthly_coverage(lines, result: VouchingResult):
    """Coverage month by month, so a bad month is visible rather than averaged away."""
    unvouched_ids = {l.line_id for l in result.unvouched}
    months = {}
    for line in lines:
        m = months.setdefault(line.month, {"total": 0.0, "unsupported": 0.0})
        m["total"] += line.amount
        if line.line_id in unvouched_ids:
            m["unsupported"] += line.amount
    return {
        month: (v["total"] - v["unsupported"]) / v["total"] if v["total"] else 1.0
        for month, v in sorted(months.items())
    }


def exceptions_report(result: VouchingResult):
    """Everything that needs a human, in the order it should be looked at."""
    report = []

    for receipt_no, lines in result.reused_receipts:
        ids = ", ".join(l.line_id for l in lines)
        report.append(
            f"DUPLICATE  receipt {receipt_no} claimed on {len(lines)} lines ({ids}) "
            f"— the same cost may have been paid more than once"
        )
    for line, receipt, diff in result.amount_mismatches:
        report.append(
            f"MISMATCH   {line.line_id}: claimed {line.amount:,.2f} against receipt "
            f"{receipt.receipt_no} for {receipt.amount:,.2f} "
            f"({'over' if diff > 0 else 'under'} by {abs(diff):,.2f})"
        )
    for line in result.unvouched:
        report.append(
            f"NO RECEIPT {line.line_id}: {line.vendor} {line.amount:,.2f} "
            f"({line.month}) has no supporting document"
        )
    for receipt in result.orphan_receipts:
        report.append(
            f"UNCLAIMED  receipt {receipt.receipt_no} from {receipt.vendor} for "
            f"{receipt.amount:,.2f} was never claimed — the cost may not be recorded"
        )
    for line, receipt, gap in result.date_mismatches:
        report.append(
            f"DATE       {line.line_id}: receipt {receipt.receipt_no} is {gap} days "
            f"from the expense date"
        )
    return report


def summary(lines, receipts, result: VouchingResult):
    """The headline numbers for a twelve-month vouching exercise."""
    return {
        "expense_lines": len(lines),
        "receipts_on_file": len(receipts),
        "matched": len(result.matched),
        "value_claimed": sum(l.amount for l in lines),
        "value_coverage": coverage(lines, result),
        "unvouched_lines": len(result.unvouched),
        "unvouched_value": sum(l.amount for l in result.unvouched),
        "orphan_receipts": len(result.orphan_receipts),
        "amount_mismatches": len(result.amount_mismatches),
        "reused_receipts": len(result.reused_receipts),
        "exceptions": len(exceptions_report(result)),
    }
