"""Nominal BRL CAPM and target-capital-structure WACC."""

from .validation import fraction, number


def cost_of_equity(risk_free: float, beta: float, equity_risk_premium: float) -> float:
    return number(risk_free, "risk free", 0) + number(beta, "beta", 0) * number(
        equity_risk_premium, "equity risk premium", 0
    )


def wacc(equity_cost: float, debt_cost: float, tax_rate: float, debt_weight: float) -> float:
    fraction(tax_rate, "tax rate")
    fraction(debt_weight, "debt weight")
    return (
        number(equity_cost, "equity cost", 0) * (1 - debt_weight)
        + number(debt_cost, "debt cost", 0) * (1 - tax_rate) * debt_weight
    )
