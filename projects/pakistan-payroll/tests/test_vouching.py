"""Tests for matching the expense register to the receipt file.

Each test feeds in one specific way the match can fail, so a check that
stopped working fails here rather than passing by never being exercised.
"""

import unittest
from datetime import date

from payroll.vouching import (
    ExpenseLine,
    Receipt,
    coverage,
    exceptions_report,
    monthly_coverage,
    summary,
    voucher_match,
)


def line(**kw):
    base = dict(
        line_id="L001",
        month="2025-03",
        vendor="Office Supplies Ltd",
        amount=12_000.0,
        expense_date=date(2025, 3, 10),
        receipt_no="R001",
    )
    base.update(kw)
    return ExpenseLine(**base)


def receipt(**kw):
    base = dict(
        receipt_no="R001",
        vendor="Office Supplies Ltd",
        amount=12_000.0,
        receipt_date=date(2025, 3, 10),
    )
    base.update(kw)
    return Receipt(**base)


class TestCleanMatch(unittest.TestCase):
    def test_matching_line_and_receipt(self):
        r = voucher_match([line()], [receipt()])
        self.assertEqual(len(r.matched), 1)
        self.assertEqual(r.unvouched, [])
        self.assertEqual(r.orphan_receipts, [])
        self.assertEqual(exceptions_report(r), [])

    def test_small_rounding_is_tolerated(self):
        r = voucher_match([line(amount=12_000.50)], [receipt()])
        self.assertEqual(r.amount_mismatches, [])


class TestUnvouched(unittest.TestCase):
    def test_line_with_no_receipt_number(self):
        r = voucher_match([line(receipt_no="")], [])
        self.assertEqual(len(r.unvouched), 1)

    def test_line_referencing_a_receipt_that_is_not_on_file(self):
        r = voucher_match([line(receipt_no="R999")], [receipt()])
        self.assertEqual(len(r.unvouched), 1)
        self.assertEqual(len(r.orphan_receipts), 1)

    def test_unvouched_appears_in_exceptions(self):
        r = voucher_match([line(receipt_no="")], [])
        self.assertTrue(any("NO RECEIPT" in e for e in exceptions_report(r)))


class TestOrphanReceipts(unittest.TestCase):
    def test_receipt_nobody_claimed(self):
        r = voucher_match([], [receipt()])
        self.assertEqual(len(r.orphan_receipts), 1)
        self.assertTrue(any("UNCLAIMED" in e for e in exceptions_report(r)))


class TestAmountMismatch(unittest.TestCase):
    def test_over_claim_is_caught(self):
        r = voucher_match([line(amount=15_000)], [receipt(amount=12_000)])
        self.assertEqual(len(r.amount_mismatches), 1)
        _, _, diff = r.amount_mismatches[0]
        self.assertAlmostEqual(diff, 3_000, places=2)
        self.assertTrue(any("over by" in e for e in exceptions_report(r)))

    def test_under_claim_is_caught(self):
        r = voucher_match([line(amount=9_000)], [receipt(amount=12_000)])
        self.assertTrue(any("under by" in e for e in exceptions_report(r)))


class TestReusedReceipt(unittest.TestCase):
    """The same receipt supporting two claims — the one that looks clean elsewhere."""

    def test_same_receipt_on_two_lines_is_flagged(self):
        lines = [line(line_id="L001"), line(line_id="L002")]
        r = voucher_match(lines, [receipt()])
        self.assertEqual(len(r.reused_receipts), 1)
        no, claimed = r.reused_receipts[0]
        self.assertEqual(no, "R001")
        self.assertEqual(len(claimed), 2)

    def test_duplicate_is_first_in_the_exceptions_report(self):
        lines = [line(line_id="L001"), line(line_id="L002", receipt_no="R001")]
        r = voucher_match(lines, [receipt()])
        self.assertTrue(exceptions_report(r)[0].startswith("DUPLICATE"))

    def test_distinct_receipts_are_not_flagged(self):
        lines = [line(line_id="L001"), line(line_id="L002", receipt_no="R002")]
        receipts = [receipt(), receipt(receipt_no="R002")]
        self.assertEqual(voucher_match(lines, receipts).reused_receipts, [])


class TestDateMismatch(unittest.TestCase):
    def test_receipt_far_from_the_expense_date(self):
        r = voucher_match(
            [line(expense_date=date(2025, 3, 10))],
            [receipt(receipt_date=date(2024, 11, 1))],
        )
        self.assertEqual(len(r.date_mismatches), 1)

    def test_month_boundary_is_tolerated(self):
        r = voucher_match(
            [line(month="2025-03", expense_date=date(2025, 3, 2))],
            [receipt(receipt_date=date(2025, 2, 26))],
        )
        self.assertEqual(r.date_mismatches, [])


class TestCoverage(unittest.TestCase):
    def test_coverage_is_by_value_not_count(self):
        # Nine small vouched claims must not hide one large unsupported one.
        lines = [
            line(line_id=f"L{i}", amount=1_000, receipt_no=f"R{i}") for i in range(9)
        ] + [line(line_id="BIG", amount=91_000, receipt_no="")]
        receipts = [receipt(receipt_no=f"R{i}", amount=1_000) for i in range(9)]
        r = voucher_match(lines, receipts)
        self.assertAlmostEqual(coverage(lines, r), 0.09, places=4)

    def test_full_coverage(self):
        lines = [line()]
        r = voucher_match(lines, [receipt()])
        self.assertEqual(coverage(lines, r), 1.0)

    def test_monthly_coverage_isolates_a_bad_month(self):
        lines = [
            line(line_id="A", month="2025-01", receipt_no="R001"),
            line(line_id="B", month="2025-02", receipt_no=""),
        ]
        r = voucher_match(lines, [receipt()])
        m = monthly_coverage(lines, r)
        self.assertEqual(m["2025-01"], 1.0)
        self.assertEqual(m["2025-02"], 0.0)

    def test_empty_register_is_fully_covered(self):
        r = voucher_match([], [])
        self.assertEqual(coverage([], r), 1.0)


class TestSummary(unittest.TestCase):
    def test_summary_counts_every_exception_type(self):
        lines = [
            line(line_id="L1", receipt_no="R001"),
            line(line_id="L2", receipt_no="R001"),  # reused
            line(line_id="L3", receipt_no=""),  # unvouched
            line(line_id="L4", receipt_no="R002", amount=20_000),  # mismatch
        ]
        receipts = [receipt(), receipt(receipt_no="R002", amount=12_000),
                    receipt(receipt_no="R003")]  # orphan
        r = voucher_match(lines, receipts)
        s = summary(lines, receipts, r)
        self.assertEqual(s["unvouched_lines"], 1)
        self.assertEqual(s["orphan_receipts"], 1)
        self.assertEqual(s["amount_mismatches"], 1)
        self.assertEqual(s["reused_receipts"], 1)
        self.assertEqual(s["exceptions"], 4)


if __name__ == "__main__":
    unittest.main()
