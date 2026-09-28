"""Tests for the Tax Year 2025 salaried tax engine.

The slab boundaries and the internal consistency of the fixed amounts are
tested separately: a typo in a fixed amount would pass a boundary test but
fail the chaining test, and vice versa.
"""

import unittest

from payroll import tax


class TestSlabBoundaries(unittest.TestCase):
    def test_no_tax_at_or_below_exemption(self):
        self.assertEqual(tax.annual_tax(0), 0)
        self.assertEqual(tax.annual_tax(600_000), 0)

    def test_first_taxable_rupee(self):
        # One rupee over the exemption is taxed at 5%, not on the whole amount.
        self.assertAlmostEqual(tax.annual_tax(600_100), 5.0, places=6)

    def test_slab_tops(self):
        # Tax at the top of each slab equals the next slab's fixed amount.
        self.assertAlmostEqual(tax.annual_tax(1_200_000), 30_000, places=6)
        self.assertAlmostEqual(tax.annual_tax(2_200_000), 180_000, places=6)
        self.assertAlmostEqual(tax.annual_tax(3_200_000), 430_000, places=6)
        self.assertAlmostEqual(tax.annual_tax(4_100_000), 700_000, places=6)

    def test_top_slab(self):
        # 700,000 + 35% of 900,000
        self.assertAlmostEqual(tax.annual_tax(5_000_000), 1_015_000, places=6)

    def test_negative_income_is_not_a_refund(self):
        self.assertEqual(tax.annual_tax(-50_000), 0)


class TestFixedAmountsChain(unittest.TestCase):
    """Each fixed amount must equal the tax accumulated by the slabs below it.

    This checks the table against itself, so a mistyped fixed amount is caught
    without hard-coding the expected figures a second time.
    """

    def test_fixed_amounts_are_consistent_with_rates(self):
        slabs = tax.TY2025_SLABS
        accumulated = 0.0
        for lower, upper in zip(slabs, slabs[1:]):
            accumulated += (upper.lower - lower.lower) * lower.rate
            self.assertAlmostEqual(
                upper.fixed,
                accumulated,
                places=6,
                msg=f"fixed amount for the slab above {upper.lower:,.0f} "
                f"should be {accumulated:,.0f}, table says {upper.fixed:,.0f}",
            )


class TestMonotonicity(unittest.TestCase):
    def test_tax_never_decreases_with_income(self):
        previous = -1.0
        for income in range(0, 6_000_001, 25_000):
            current = tax.annual_tax(income)
            self.assertGreaterEqual(current, previous)
            previous = current

    def test_no_cliff_edges(self):
        """Earning one rupee more must never leave you worse off after tax.

        Pakistan's salaried slabs are marginal, so unlike the Irish USC there
        should be no income at which net pay falls.
        """
        for boundary in (600_000, 1_200_000, 2_200_000, 3_200_000, 4_100_000):
            before = boundary - tax.annual_tax(boundary)
            after = (boundary + 1) - tax.annual_tax(boundary + 1)
            self.assertGreaterEqual(
                after, before, msg=f"net pay falls crossing {boundary:,.0f}"
            )


class TestSurcharge(unittest.TestCase):
    def test_no_surcharge_at_threshold(self):
        t = tax.annual_tax(10_000_000)
        self.assertEqual(tax.surcharge(10_000_000, t), 0.0)

    def test_surcharge_above_threshold(self):
        income = 12_000_000
        t = tax.annual_tax(income)
        self.assertAlmostEqual(tax.surcharge(income, t), t * 0.10, places=6)
        self.assertAlmostEqual(
            tax.total_annual_liability(income), t * 1.10, places=6
        )


class TestRates(unittest.TestCase):
    def test_marginal_rate(self):
        self.assertEqual(tax.marginal_rate(500_000), 0.00)
        self.assertEqual(tax.marginal_rate(900_000), 0.05)
        self.assertEqual(tax.marginal_rate(2_000_000), 0.15)
        self.assertEqual(tax.marginal_rate(5_000_000), 0.35)

    def test_effective_rate_below_marginal(self):
        # Progressive tax: the effective rate always trails the marginal rate.
        for income in (700_000, 1_500_000, 3_000_000, 5_000_000):
            self.assertLess(tax.effective_rate(income), tax.marginal_rate(income))

    def test_monthly_withholding_is_one_twelfth(self):
        income = 2_400_000
        self.assertAlmostEqual(
            tax.monthly_withholding(income),
            tax.total_annual_liability(income) / 12,
            places=6,
        )


if __name__ == "__main__":
    unittest.main()
