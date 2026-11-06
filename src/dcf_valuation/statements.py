"""Operating statement helpers, with expenses entered as positive values."""

from .validation import fraction, number


def unlevered_cash_flow(
    ebit: float, tax_rate: float, depreciation: float, capex: float, delta_nwc: float
) -> float:
    number(ebit, "EBIT")
    fraction(tax_rate, "tax rate")
    number(depreciation, "depreciation", 0)
    number(capex, "capex", 0)
    number(delta_nwc, "change in working capital")
    # No immediate tax credit or deferred-tax schedule for operating losses.
    return ebit - max(ebit, 0) * tax_rate + depreciation - capex - delta_nwc


def enterprise_to_equity(
    enterprise_value: float, cash: float, debt: float, other_claims: float = 0
) -> float:
    return (
        number(enterprise_value, "enterprise value")
        + number(cash, "cash", 0)
        - number(debt, "debt", 0)
        - number(other_claims, "other claims", 0)
    )
