"""Tests for attendance, payslips and expense policy checks.

Each validation test feeds in the specific error the check is meant to catch,
so a check that silently stopped working would fail here rather than pass by
never being exercised.
"""

import unittest
from datetime import date

from payroll import expenses
from payroll.attendance import MonthAttendance, attendance_factor, earned_gross
from payroll.expenses import ExpenseClaim
from payroll.payslip import Employee, eobi_employee_contribution, reconcile, run_month


def att(**kw):
    base = dict(
        employee_id="E001",
        month="2025-01",
        working_days=22,
        days_present=22,
        paid_leave_days=0,
        unpaid_leave_days=0,
        overtime_hours=0.0,
    )
    base.update(kw)
    return MonthAttendance(**base)


class TestAttendanceValidation(unittest.TestCase):
    def test_days_must_add_up(self):
        with self.assertRaises(ValueError):
            att(days_present=20)  # 20 + 0 + 0 != 22

    def test_working_days_must_be_positive(self):
        with self.assertRaises(ValueError):
            att(working_days=0, days_present=0)

    def test_full_attendance_is_full_pay(self):
        self.assertEqual(attendance_factor(att()), 1.0)

    def test_paid_leave_does_not_reduce_pay(self):
        a = att(days_present=20, paid_leave_days=2)
        self.assertEqual(attendance_factor(a), 1.0)

    def test_unpaid_leave_reduces_pay_pro_rata(self):
        a = att(days_present=20, unpaid_leave_days=2)
        self.assertAlmostEqual(attendance_factor(a), 20 / 22, places=9)


class TestEarnings(unittest.TestCase):
    def test_unpaid_leave_deduction_is_reported(self):
        a = att(days_present=20, unpaid_leave_days=2)
        e = earned_gross(220_000, a)
        self.assertAlmostEqual(e["unpaid_leave_deduction"], 20_000, places=6)
        self.assertAlmostEqual(e["attendance_adjusted_gross"], 200_000, places=6)

    def test_overtime_at_one_and_a_half(self):
        a = att(overtime_hours=10)
        e = earned_gross(176_000, a)  # 22 days x 8h -> 1,000/hour
        self.assertAlmostEqual(e["overtime_pay"], 10 * 1_000 * 1.5, places=6)

    def test_components_sum_to_earned_gross(self):
        a = att(days_present=19, paid_leave_days=1, unpaid_leave_days=2, overtime_hours=6)
        e = earned_gross(300_000, a)
        self.assertAlmostEqual(
            e["earned_gross"],
            e["attendance_adjusted_gross"] + e["overtime_pay"],
            places=6,
        )


class TestEOBI(unittest.TestCase):
    def test_capped_at_the_notified_wage(self):
        # A high earner pays the same EOBI as someone on the ceiling.
        self.assertAlmostEqual(
            eobi_employee_contribution(500_000), 37_000 * 0.01, places=6
        )

    def test_below_ceiling_uses_actual_wage(self):
        self.assertAlmostEqual(eobi_employee_contribution(30_000), 300.0, places=6)


class TestPayrollRun(unittest.TestCase):
    def setUp(self):
        self.employees = [
            Employee("E001", "Test One", "Finance", 200_000),
            Employee("E002", "Test Two", "Sales", 90_000),
        ]
        self.attendances = [
            att(employee_id="E001", days_present=20, unpaid_leave_days=2),
            att(employee_id="E002"),
        ]

    def test_register_reconciles(self):
        register = run_month(self.employees, self.attendances)
        self.assertEqual(reconcile(register), [])

    def test_missing_attendance_is_an_error(self):
        with self.assertRaises(ValueError):
            run_month(self.employees, self.attendances[:1])

    def test_mismatched_attendance_is_an_error(self):
        with self.assertRaises(ValueError):
            run_month([self.employees[0]], [att(employee_id="E999")])

    def test_raise_changes_withholding(self):
        base = run_month(self.employees, self.attendances)[0]["income_tax"]
        raised = run_month(
            self.employees, self.attendances, {"E001": 200_000 * 12 * 1.5}
        )[0]["income_tax"]
        self.assertGreater(raised, base)


class TestExpensePolicy(unittest.TestCase):
    def claim(self, **kw):
        base = dict(
            claim_id="C1",
            employee_id="E001",
            month="2025-03",
            category="travel",
            amount=10_000,
            incurred_on=date(2025, 3, 1),
            submitted_on=date(2025, 3, 5),
            has_receipt=True,
        )
        base.update(kw)
        return ExpenseClaim(**base)

    def test_clean_claim_passes(self):
        self.assertEqual(expenses.check_claim(self.claim()), [])

    def test_over_category_limit_is_caught(self):
        problems = expenses.check_claim(self.claim(category="meals", amount=18_000))
        self.assertTrue(any("exceeds" in p for p in problems))

    def test_missing_receipt_is_caught(self):
        problems = expenses.check_claim(self.claim(amount=20_000, has_receipt=False))
        self.assertTrue(any("receipt" in p for p in problems))

    def test_small_claim_needs_no_receipt(self):
        self.assertEqual(expenses.check_claim(self.claim(amount=2_000, has_receipt=False)), [])

    def test_stale_claim_is_caught(self):
        problems = expenses.check_claim(
            self.claim(incurred_on=date(2024, 11, 1), submitted_on=date(2025, 3, 5))
        )
        self.assertTrue(any("window" in p for p in problems))

    def test_submitted_before_incurred_is_caught(self):
        problems = expenses.check_claim(
            self.claim(incurred_on=date(2025, 3, 10), submitted_on=date(2025, 3, 1))
        )
        self.assertTrue(any("before" in p for p in problems))

    def test_unknown_category_is_caught(self):
        problems = expenses.check_claim(self.claim(category="bribes"))
        self.assertTrue(any("unknown category" in p for p in problems))

    def test_large_claim_escalates(self):
        self.assertEqual(expenses.approval_level(self.claim(amount=60_000)), "finance_head")
        self.assertEqual(expenses.approval_level(self.claim(amount=10_000)), "line_manager")

    def test_rejected_claims_are_not_reimbursed(self):
        claims = [self.claim(), self.claim(claim_id="C2", category="meals", amount=18_000)]
        approved, rejected = expenses.process(claims)
        self.assertEqual(len(approved), 1)
        self.assertEqual(len(rejected), 1)
        totals = expenses.reimbursements_by_employee(approved, "2025-03")
        self.assertAlmostEqual(totals["E001"], 10_000, places=6)


if __name__ == "__main__":
    unittest.main()
