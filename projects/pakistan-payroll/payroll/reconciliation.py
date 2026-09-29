"""Bank reconciliation: the cash book against the bank statement.

The reconciliation is not "do the balances match" — they almost never do, and
that is not an error. It is: can every difference between the two be named?
Anything left unnamed is the thing worth looking at.

Items are matched on reference first, then on amount within a date window,
because a cheque written on the 28th may not clear until the 3rd.
"""

from dataclasses import dataclass, field
from datetime import date, timedelta

# How far apart a ledger entry and a bank line can be and still be the same
# transaction. Cheques in particular clear slowly.
CLEARING_WINDOW_DAYS = 10


@dataclass(frozen=True)
class Entry:
    """A line in either the cash book or the bank statement.

    `amount` is signed: positive is money in, negative is money out.
    """

    entry_date: date
    description: str
    amount: float
    reference: str = ""


@dataclass
class Reconciliation:
    opening_ledger: float
    opening_bank: float
    matched: list = field(default_factory=list)
    unpresented: list = field(default_factory=list)  # in books, not yet at bank
    in_transit: list = field(default_factory=list)  # deposits not yet credited
    bank_only: list = field(default_factory=list)  # charges, interest, direct debits

    @property
    def ledger_closing(self):
        return self.opening_ledger + sum(e.amount for e in self._ledger_side())

    def _ledger_side(self):
        return [m[0] for m in self.matched] + self.unpresented + self.in_transit

    @property
    def bank_closing(self):
        return (
            self.opening_bank
            + sum(m[1].amount for m in self.matched)
            + sum(e.amount for e in self.bank_only)
        )


def _same_transaction(ledger_entry, bank_entry):
    """Could these two lines be the same transaction?"""
    if abs(ledger_entry.amount - bank_entry.amount) > 0.01:
        return False
    gap = abs((bank_entry.entry_date - ledger_entry.entry_date).days)
    return gap <= CLEARING_WINDOW_DAYS


def reconcile(ledger, statement, opening_ledger=0.0, opening_bank=0.0):
    """Match the cash book to the bank statement and classify what is left.

    Returns a Reconciliation. Matching is greedy: exact reference matches are
    taken first so a reference can't be stolen by a coincidental amount match.
    """
    remaining_bank = list(statement)
    rec = Reconciliation(opening_ledger=opening_ledger, opening_bank=opening_bank)
    unmatched_ledger = []

    # Pass 1 — reference match.
    for led in ledger:
        hit = None
        if led.reference:
            for bank in remaining_bank:
                if bank.reference and bank.reference == led.reference:
                    hit = bank
                    break
        if hit is not None:
            remaining_bank.remove(hit)
            rec.matched.append((led, hit))
        else:
            unmatched_ledger.append(led)

    # Pass 2 — amount and date match for anything without a usable reference.
    still_unmatched = []
    for led in unmatched_ledger:
        hit = next((b for b in remaining_bank if _same_transaction(led, b)), None)
        if hit is not None:
            remaining_bank.remove(hit)
            rec.matched.append((led, hit))
        else:
            still_unmatched.append(led)

    # Whatever is left in the books has not reached the bank yet.
    for led in still_unmatched:
        if led.amount < 0:
            rec.unpresented.append(led)  # cheque written, not yet cleared
        else:
            rec.in_transit.append(led)  # lodgement not yet credited

    # Whatever is left on the statement never reached the books.
    rec.bank_only = remaining_bank
    return rec


def statement_of_reconciliation(rec: Reconciliation):
    """The working that goes in the file, starting from the bank balance."""
    unpresented = sum(e.amount for e in rec.unpresented)
    in_transit = sum(e.amount for e in rec.in_transit)
    bank_only = sum(e.amount for e in rec.bank_only)
    return {
        "balance_per_bank_statement": rec.bank_closing,
        "add_deposits_in_transit": in_transit,
        "less_unpresented_payments": unpresented,
        "adjusted_bank_balance": rec.bank_closing + in_transit + unpresented,
        "balance_per_cash_book": rec.ledger_closing,
        "unrecorded_bank_items": bank_only,
        "adjusted_book_balance": rec.ledger_closing + bank_only,
    }


def check(rec: Reconciliation, tolerance=0.01):
    """Does the reconciliation actually reconcile?

    Returns a list of problems; empty means the two sides agree once every
    difference has been accounted for.
    """
    s = statement_of_reconciliation(rec)
    problems = []
    gap = s["adjusted_bank_balance"] - s["adjusted_book_balance"]
    if abs(gap) > tolerance:
        problems.append(
            f"reconciliation does not tie: adjusted bank "
            f"{s['adjusted_bank_balance']:,.2f} vs adjusted book "
            f"{s['adjusted_book_balance']:,.2f}, difference {gap:,.2f}"
        )
    for entry in rec.bank_only:
        problems.append(
            f"on the statement but not in the cash book: "
            f"{entry.entry_date} {entry.description} {entry.amount:,.2f}"
        )
    return problems


def stale_items(rec: Reconciliation, as_at: date, days=30):
    """Reconciling items old enough to be worth chasing.

    An unpresented cheque still outstanding after a month is usually either
    lost, never sent, or was already replaced — all of which need action.
    """
    cutoff = as_at - timedelta(days=days)
    return [
        e for e in (rec.unpresented + rec.in_transit) if e.entry_date < cutoff
    ]
