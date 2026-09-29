"""Tests for bank reconciliation and the voucher approval control.

Every control test feeds in the specific way money could escape, and asserts
the control refuses it. A control that is never fed its own failure case has
not been tested.
"""

import unittest
from datetime import date

from payroll import reconciliation as rec_mod
from payroll import vouchers as v_mod
from payroll.reconciliation import Entry, reconcile, statement_of_reconciliation
from payroll.vouchers import ControlBreach, Status, Voucher, approve, disburse, prepare


class TestReconciliationMatching(unittest.TestCase):
    def test_matches_on_reference(self):
        led = [Entry(date(2025, 1, 5), "Supplier A", -50_000, "CHQ001")]
        bank = [Entry(date(2025, 1, 9), "CHEQUE 001", -50_000, "CHQ001")]
        r = reconcile(led, bank)
        self.assertEqual(len(r.matched), 1)
        self.assertEqual(r.unpresented, [])

    def test_reference_match_beats_coincidental_amount(self):
        # Two payments of the same value; references must keep them apart.
        led = [
            Entry(date(2025, 1, 5), "Supplier A", -50_000, "CHQ001"),
            Entry(date(2025, 1, 6), "Supplier B", -50_000, "CHQ002"),
        ]
        bank = [
            Entry(date(2025, 1, 9), "CHEQUE 002", -50_000, "CHQ002"),
            Entry(date(2025, 1, 10), "CHEQUE 001", -50_000, "CHQ001"),
        ]
        r = reconcile(led, bank)
        self.assertEqual(len(r.matched), 2)
        for ledger_entry, bank_entry in r.matched:
            self.assertEqual(ledger_entry.reference, bank_entry.reference)

    def test_matches_on_amount_within_clearing_window(self):
        led = [Entry(date(2025, 1, 28), "Supplier C", -30_000)]
        bank = [Entry(date(2025, 2, 3), "CHEQUE", -30_000)]
        self.assertEqual(len(reconcile(led, bank).matched), 1)

    def test_does_not_match_outside_the_window(self):
        led = [Entry(date(2025, 1, 2), "Supplier C", -30_000)]
        bank = [Entry(date(2025, 3, 20), "CHEQUE", -30_000)]
        r = reconcile(led, bank)
        self.assertEqual(r.matched, [])
        self.assertEqual(len(r.unpresented), 1)

    def test_unpresented_cheque_and_deposit_in_transit(self):
        led = [
            Entry(date(2025, 1, 30), "Cheque to supplier", -40_000),
            Entry(date(2025, 1, 31), "Customer lodgement", 25_000),
        ]
        r = reconcile(led, [])
        self.assertEqual(len(r.unpresented), 1)
        self.assertEqual(len(r.in_transit), 1)

    def test_bank_only_items_are_surfaced(self):
        bank = [Entry(date(2025, 1, 31), "Bank charges", -1_200)]
        r = reconcile([], bank)
        self.assertEqual(len(r.bank_only), 1)
        problems = rec_mod.check(r)
        self.assertTrue(any("not in the cash book" in p for p in problems))


class TestReconciliationTies(unittest.TestCase):
    def test_full_reconciliation_ties(self):
        led = [
            Entry(date(2025, 1, 4), "Sales receipt", 300_000, "RCT01"),
            Entry(date(2025, 1, 12), "Rent", -120_000, "CHQ010"),
            Entry(date(2025, 1, 29), "Cheque not yet cleared", -45_000),
            Entry(date(2025, 1, 31), "Lodgement in transit", 60_000),
        ]
        bank = [
            Entry(date(2025, 1, 5), "CREDIT", 300_000, "RCT01"),
            Entry(date(2025, 1, 14), "CHEQUE 010", -120_000, "CHQ010"),
            Entry(date(2025, 1, 31), "Bank charges", -1_500),
        ]
        r = reconcile(led, bank, opening_ledger=500_000, opening_bank=500_000)
        s = statement_of_reconciliation(r)
        self.assertAlmostEqual(
            s["adjusted_bank_balance"], s["adjusted_book_balance"], places=2
        )
        # The only thing stopping a clean tie is the unrecorded bank charge.
        self.assertEqual(len(r.bank_only), 1)

    def test_stale_items_are_flagged(self):
        led = [Entry(date(2025, 1, 2), "Old cheque", -10_000)]
        r = reconcile(led, [])
        stale = rec_mod.stale_items(r, as_at=date(2025, 3, 1), days=30)
        self.assertEqual(len(stale), 1)


def make_voucher(**kw):
    base = dict(
        voucher_no="V001",
        payee="Office Supplies Ltd",
        category="office",
        amount=25_000,
        raised_on=date(2025, 3, 3),
        prepared_by="shahram",
        narrative="Stationery for Q1",
    )
    base.update(kw)
    return prepare(Voucher(**base))


class TestVoucherPreparation(unittest.TestCase):
    def test_narrative_is_required(self):
        with self.assertRaises(ControlBreach):
            make_voucher(narrative="   ")

    def test_amount_must_be_positive(self):
        with self.assertRaises(ControlBreach):
            make_voucher(amount=0)


class TestSegregationOfDuties(unittest.TestCase):
    """The three refusals that make the control worth having."""

    def test_preparer_cannot_approve_own_voucher(self):
        v = make_voucher()
        with self.assertRaises(ControlBreach) as ctx:
            approve(v, approver="shahram", on=date(2025, 3, 4))
        self.assertIn("cannot", str(ctx.exception))

    def test_preparer_cannot_disburse(self):
        v = make_voucher()
        approve(v, approver="director", on=date(2025, 3, 4))
        with self.assertRaises(ControlBreach):
            disburse(v, payer="shahram", on=date(2025, 3, 5))

    def test_approver_cannot_disburse(self):
        v = make_voucher()
        approve(v, approver="director", on=date(2025, 3, 4))
        with self.assertRaises(ControlBreach):
            disburse(v, payer="director", on=date(2025, 3, 5))

    def test_clean_three_party_flow_succeeds(self):
        v = make_voucher()
        approve(v, approver="director", on=date(2025, 3, 4))
        disburse(v, payer="ceo", on=date(2025, 3, 5))
        self.assertIs(v.status, Status.DISBURSED)
        self.assertEqual(len(v.audit_trail), 3)


class TestApprovalAuthority(unittest.TestCase):
    def test_director_limit_is_enforced(self):
        v = make_voucher(amount=250_000)
        with self.assertRaises(ControlBreach) as ctx:
            approve(v, approver="director", on=date(2025, 3, 4))
        self.assertIn("CEO approval", str(ctx.exception))

    def test_ceo_can_approve_above_the_limit(self):
        v = make_voucher(amount=250_000)
        approve(v, approver="ceo", on=date(2025, 3, 4), is_ceo=True)
        self.assertIs(v.status, Status.APPROVED)


class TestPaymentGates(unittest.TestCase):
    def test_cannot_disburse_without_approval(self):
        v = make_voucher()
        with self.assertRaises(ControlBreach) as ctx:
            disburse(v, payer="ceo", on=date(2025, 3, 5))
        self.assertIn("approval must come first", str(ctx.exception))

    def test_amount_cannot_change_after_approval(self):
        v = make_voucher(amount=25_000)
        approve(v, approver="director", on=date(2025, 3, 4))
        v.amount = 250_000  # tampering after sign-off
        with self.assertRaises(ControlBreach) as ctx:
            disburse(v, payer="ceo", on=date(2025, 3, 5))
        self.assertIn("after approval", str(ctx.exception))

    def test_cannot_approve_twice(self):
        v = make_voucher()
        approve(v, approver="director", on=date(2025, 3, 4))
        with self.assertRaises(ControlBreach):
            approve(v, approver="ceo", on=date(2025, 3, 5), is_ceo=True)

    def test_cannot_approve_before_raised(self):
        v = make_voucher(raised_on=date(2025, 3, 10))
        with self.assertRaises(ControlBreach):
            approve(v, approver="director", on=date(2025, 3, 1))

    def test_rejected_voucher_cannot_be_paid(self):
        v = make_voucher()
        v_mod.reject(v, approver="director", on=date(2025, 3, 4), reason="no budget")
        with self.assertRaises(ControlBreach):
            disburse(v, payer="ceo", on=date(2025, 3, 5))


class TestDuplicateDetection(unittest.TestCase):
    def paid(self, no, amount, day):
        v = make_voucher(voucher_no=no, amount=amount, raised_on=date(2025, 3, 1))
        approve(v, approver="director", on=date(2025, 3, 2))
        disburse(v, payer="ceo", on=date(2025, 3, day))
        return v

    def test_same_payee_same_amount_is_flagged(self):
        vs = [self.paid("V1", 40_000, 5), self.paid("V2", 40_000, 12)]
        self.assertEqual(len(v_mod.find_duplicate_payments(vs)), 1)

    def test_different_amounts_are_not_flagged(self):
        vs = [self.paid("V1", 40_000, 5), self.paid("V2", 41_000, 12)]
        self.assertEqual(v_mod.find_duplicate_payments(vs), [])

    def test_control_summary_counts_segregation(self):
        vs = [self.paid("V1", 40_000, 5)]
        s = v_mod.control_summary(vs)
        self.assertEqual(s["three_party_segregation"], 1)
        self.assertEqual(s["segregation_rate"], 1.0)


if __name__ == "__main__":
    unittest.main()
