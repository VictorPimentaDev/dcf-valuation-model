"""Revenue build from explicit annual growth rates."""

from collections.abc import Iterable

from .validation import number


def build_revenue(base_revenue: float, growth_rates: Iterable[float]) -> list[float]:
    revenue = number(base_revenue, "base revenue", 0)
    result = []
    for growth in growth_rates:
        number(growth, "growth")
        if growth <= -1:
            raise ValueError("growth must be greater than -100%")
        revenue *= 1 + growth
        number(revenue, "projected revenue", 0)
        result.append(revenue)
    return result
