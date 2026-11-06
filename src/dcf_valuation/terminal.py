"""Gordon growth terminal value at the end of the explicit forecast."""

from .validation import number


def terminal_value(last_fcff: float, discount_rate: float, growth: float) -> float:
    number(last_fcff, "last FCFF")
    number(discount_rate, "discount rate")
    number(growth, "terminal growth")
    if growth <= -1 or discount_rate <= growth:
        raise ValueError("terminal growth must be > -100% and below the discount rate")
    # shortcut: grows final FCFF as a block; add a terminal ROIC schedule for investment use.
    return last_fcff * (1 + growth) / (discount_rate - growth)
