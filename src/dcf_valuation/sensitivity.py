"""Reprice all forecast cash flows and terminal value for each rate pair."""

from collections.abc import Sequence

from .statements import enterprise_to_equity
from .terminal import terminal_value
from .validation import number


def enterprise_value(cash_flows: Sequence[float], discount_rate: float, growth: float) -> float:
    if not cash_flows:
        raise ValueError("at least one forecast cash flow is required")
    terminal = terminal_value(cash_flows[-1], discount_rate, growth)
    present = sum(
        number(flow, "FCFF") / (1 + discount_rate) ** year
        for year, flow in enumerate(cash_flows, 1)
    )
    return present + terminal / (1 + discount_rate) ** len(cash_flows)


def sensitivity_table(
    cash_flows: Sequence[float],
    discount_rates: Sequence[float],
    growth_rates: Sequence[float],
    *,
    cash: float,
    debt: float,
    other_claims: float,
    shares: float,
) -> list[list[float | None]]:
    number(shares, "shares", 0)
    if shares == 0:
        raise ValueError("shares must be positive")
    for rate in discount_rates:
        number(rate, "discount rate", 0)
    for growth in growth_rates:
        number(growth, "terminal growth")
        if growth <= -1:
            raise ValueError("terminal growth must be > -100%")
    enterprise_to_equity(0, cash, debt, other_claims)
    if not cash_flows:
        raise ValueError("at least one forecast cash flow is required")
    return [
        [
            enterprise_to_equity(
                enterprise_value(cash_flows, rate, growth), cash, debt, other_claims
            )
            / shares
            if rate > growth
            else None
            for growth in growth_rates
        ]
        for rate in discount_rates
    ]
