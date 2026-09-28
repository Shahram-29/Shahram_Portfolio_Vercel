"""Pakistani salaried income tax, Tax Year 2025.

Tax Year 2025 runs 1 July 2024 to 30 June 2025 and is governed by the Finance
Act 2024. Slabs are held as data so another year can be added without touching
the calculation.

Sources for the TY2025 slabs are listed in the project README. The fixed amounts
chain arithmetically from the marginal rates, which `tests/test_tax.py` checks
independently of the table.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Slab:
    """One row of the salaried slab table."""

    lower: float  # taxable income above which this slab applies (PKR)
    fixed: float  # tax on all income up to `lower` (PKR)
    rate: float  # marginal rate on the excess over `lower`


# Finance Act 2024, salaried individuals (salary > 75% of taxable income).
TY2025_SLABS = (
    Slab(lower=0, fixed=0, rate=0.00),
    Slab(lower=600_000, fixed=0, rate=0.05),
    Slab(lower=1_200_000, fixed=30_000, rate=0.15),
    Slab(lower=2_200_000, fixed=180_000, rate=0.25),
    Slab(lower=3_200_000, fixed=430_000, rate=0.30),
    Slab(lower=4_100_000, fixed=700_000, rate=0.35),
)

# Surcharge on the tax charged, for taxable income above this threshold.
TY2025_SURCHARGE_THRESHOLD = 10_000_000
TY2025_SURCHARGE_RATE = 0.10


def annual_tax(taxable_income, slabs=TY2025_SLABS):
    """Income tax before surcharge on an annual taxable salary, in PKR."""
    if taxable_income <= 0:
        return 0.0
    slab = slabs[0]
    for candidate in slabs:
        if taxable_income > candidate.lower:
            slab = candidate
        else:
            break
    return slab.fixed + (taxable_income - slab.lower) * slab.rate


def surcharge(
    taxable_income,
    tax,
    threshold=TY2025_SURCHARGE_THRESHOLD,
    rate=TY2025_SURCHARGE_RATE,
):
    """Surcharge payable on top of `tax`. Zero below the threshold."""
    return tax * rate if taxable_income > threshold else 0.0


def total_annual_liability(taxable_income, slabs=TY2025_SLABS):
    """Income tax plus surcharge for the year."""
    tax = annual_tax(taxable_income, slabs)
    return tax + surcharge(taxable_income, tax)


def monthly_withholding(annual_taxable_income, slabs=TY2025_SLABS):
    """Tax to deduct from one month's salary under section 149.

    The employer spreads the annual liability evenly across twelve months,
    which is why a mid-year raise changes every remaining month's deduction
    and not just the months after it.
    """
    return total_annual_liability(annual_taxable_income, slabs) / 12


def effective_rate(taxable_income, slabs=TY2025_SLABS):
    """Total liability as a share of taxable income."""
    if taxable_income <= 0:
        return 0.0
    return total_annual_liability(taxable_income, slabs) / taxable_income


def marginal_rate(taxable_income, slabs=TY2025_SLABS):
    """The rate applying to the next rupee earned."""
    slab = slabs[0]
    for candidate in slabs:
        if taxable_income > candidate.lower:
            slab = candidate
        else:
            break
    return slab.rate
