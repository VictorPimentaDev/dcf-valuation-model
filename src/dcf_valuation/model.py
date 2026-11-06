"""Fixed five-year educational model and versioned source fixture."""

import json
from dataclasses import asdict, dataclass
from importlib.resources import files

from .revenue import build_revenue
from .sensitivity import enterprise_value
from .statements import enterprise_to_equity, unlevered_cash_flow
from .validation import fraction, number
from .wacc import cost_of_equity, wacc


def load_data() -> dict:
    return json.loads(files("dcf_valuation").joinpath("data/weg_2024.json").read_text())


@dataclass(frozen=True)
class Assumptions:
    growth: tuple[float, ...] = (0.12, 0.11, 0.10, 0.09, 0.08)
    ebit_margin: tuple[float, ...] = (0.20,) * 5
    da_ratio: tuple[float, ...] = (0.025,) * 5
    capex_ratio: tuple[float, ...] = (0.045,) * 5
    nwc_ratio: tuple[float, ...] = (0.20,) * 5
    risk_free: float = 0.10
    beta: float = 0.9
    equity_risk_premium: float = 0.06
    debt_cost: float = 0.12
    debt_weight: float = 0.10
    tax_rate: float = 0.34
    terminal_growth: float = 0.04
    cash: float = 8013.210
    debt: float = 3595.237
    other_claims: float = 500.0
    shares: float = 4197.317998
    opening_nwc_ratio: float = 0.20

    def __post_init__(self) -> None:
        for name in ("growth", "ebit_margin", "da_ratio", "capex_ratio", "nwc_ratio"):
            values = getattr(self, name)
            if not isinstance(values, (list, tuple)) or len(values) != 5:
                raise ValueError(f"{name}: expected exactly five annual values")
            for value in values:
                if name == "growth":
                    build_revenue(1, [value])
                else:
                    fraction(value, name)
        fraction(self.opening_nwc_ratio, "opening working capital ratio")
        enterprise_to_equity(0, self.cash, self.debt, self.other_claims)
        if number(self.shares, "shares", 0) == 0:
            raise ValueError("shares must be positive")
        enterprise_value([1], self.discount_rate, self.terminal_growth)

    @property
    def discount_rate(self) -> float:
        return wacc(
            cost_of_equity(self.risk_free, self.beta, self.equity_risk_premium),
            self.debt_cost,
            self.tax_rate,
            self.debt_weight,
        )


def calculate(assumptions: Assumptions) -> dict:
    historical = load_data()["historical"][-1]
    revenues = build_revenue(historical["revenue"], assumptions.growth)
    previous_nwc = historical["revenue"] * assumptions.opening_nwc_ratio
    projections = []
    for index, revenue in enumerate(revenues):
        ebit = revenue * assumptions.ebit_margin[index]
        da = revenue * assumptions.da_ratio[index]
        capex = revenue * assumptions.capex_ratio[index]
        nwc = revenue * assumptions.nwc_ratio[index]
        delta_nwc = nwc - previous_nwc
        fcff = unlevered_cash_flow(ebit, assumptions.tax_rate, da, capex, delta_nwc)
        projections.append(
            {
                "year": historical["year"] + index + 1,
                "revenue": revenue,
                "ebit": ebit,
                "da": da,
                "capex": capex,
                "nwc": nwc,
                "delta_nwc": delta_nwc,
                "fcff": fcff,
            }
        )
        previous_nwc = nwc
    flows = [period["fcff"] for period in projections]
    ev = enterprise_value(flows, assumptions.discount_rate, assumptions.terminal_growth)
    equity = enterprise_to_equity(ev, assumptions.cash, assumptions.debt, assumptions.other_claims)
    return {
        "assumptions": asdict(assumptions),
        "projections": projections,
        "wacc": assumptions.discount_rate,
        "enterprise_value": ev,
        "equity_value": equity,
        "price_per_share": equity / assumptions.shares,
    }
