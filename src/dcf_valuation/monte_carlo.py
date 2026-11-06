"""Independent triangular assumptions, persistent within each five-year trajectory.

These are subjective uncertainty ranges, not fitted distributions or price forecasts.
All support is validated before sampling; no rejected draws or silent clipping.
"""

from dataclasses import asdict, dataclass, replace

import numpy as np
import pandas as pd
from scipy.stats import triang

from .model import Assumptions, calculate, load_data
from .validation import number


@dataclass(frozen=True)
class SimulationConfig:
    samples: int = 10_000
    seed: int = 42
    growth_spread: float = 0.05
    margin_spread: float = 0.04
    wacc_spread: float = 0.025
    terminal_spread: float = 0.015

    def __post_init__(self) -> None:
        for name in ("samples", "seed"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < (name == "samples"):
                raise ValueError(f"{name} must be a nonnegative integer (samples > 0)")
        for name in ("growth_spread", "margin_spread", "wacc_spread", "terminal_spread"):
            number(getattr(self, name), name, 0)

    def validate_support(self, a: Assumptions) -> None:
        if min(a.growth) - self.growth_spread <= -1:
            raise ValueError("growth support must stay above -100%")
        if (
            min(a.ebit_margin) - self.margin_spread < 0
            or max(a.ebit_margin) + self.margin_spread > 1
        ):
            raise ValueError("margin support must stay in [0, 1]")
        low_rate = a.discount_rate - self.wacc_spread
        if low_rate < 0 or a.terminal_growth - self.terminal_spread <= -1:
            raise ValueError("WACC support must be nonnegative and terminal growth > -100%")
        if low_rate <= a.terminal_growth + self.terminal_spread:
            raise ValueError("entire support must satisfy WACC > terminal growth; narrow spreads")

    def metadata(self) -> dict:
        return {
            **asdict(self),
            "distribution": "independent symmetric triangular; mode=base, bounds=base±spread",
            "persistence": "one growth shift and one margin shift applied to all five years",
            "interpretation": "subjective fair-value uncertainty, not a future-price forecast",
        }


@dataclass
class Simulation:
    samples: pd.DataFrame
    revenue: pd.DataFrame
    config: SimulationConfig
    assumptions: Assumptions
    valuation_date: str
    base_revenue: float

    @property
    def summary(self) -> dict:
        values = self.samples["price_per_share"]
        return {
            "mean": float(values.mean()),
            **{f"p{p:02}": float(values.quantile(p / 100)) for p in (5, 10, 25, 50, 75, 90, 95)},
        }


def _scenario(a: Assumptions, shifts: dict) -> tuple[Assumptions, float]:
    return replace(
        a,
        growth=tuple(g + shifts["growth_shift"] for g in a.growth),
        ebit_margin=tuple(m + shifts["margin_shift"] for m in a.ebit_margin),
        terminal_growth=a.terminal_growth + shifts["terminal_shift"],
    ), a.discount_rate + shifts["wacc_shift"]


def simulate(
    assumptions: Assumptions, config: SimulationConfig | None = None, data: dict | None = None
) -> Simulation:
    config = config or SimulationConfig()
    config.validate_support(assumptions)
    data = data or load_data()
    rng = np.random.default_rng(config.seed)
    shifts = {}
    for name, spread in (
        ("growth_shift", config.growth_spread),
        ("margin_shift", config.margin_spread),
        ("wacc_shift", config.wacc_spread),
        ("terminal_shift", config.terminal_spread),
    ):
        shifts[name] = (
            triang.rvs(0.5, loc=-spread, scale=2 * spread, size=config.samples, random_state=rng)
            if spread
            else np.zeros(config.samples)
        )
    samples = pd.DataFrame(shifts)
    prices, revenues = [], []
    for shift in samples.to_dict("records"):
        scenario, rate = _scenario(assumptions, shift)
        result = calculate(scenario, data, discount_rate=rate)
        prices.append(result["price_per_share"])
        revenues.append([p["revenue"] for p in result["projections"]])
    samples["wacc"] = assumptions.discount_rate + samples["wacc_shift"]
    samples["terminal_growth"] = assumptions.terminal_growth + samples["terminal_shift"]
    samples["price_per_share"] = prices
    return Simulation(
        samples,
        pd.DataFrame(revenues, columns=range(1, 6)),
        config,
        assumptions,
        data["valuation_date"],
        data["historical"][-1]["revenue"],
    )


def tornado(assumptions: Assumptions, config: SimulationConfig, data: dict | None = None):
    """One-at-a-time theoretical P10/P90 shifts; all other inputs stay at their base."""
    config.validate_support(assumptions)
    rows = []
    for driver, spread in (
        ("growth", config.growth_spread),
        ("margin", config.margin_spread),
        ("wacc", config.wacc_spread),
        ("terminal", config.terminal_spread),
    ):
        prices = []
        for quantile in (0.1, 0.9):
            shifts = dict.fromkeys(
                ("growth_shift", "margin_shift", "wacc_shift", "terminal_shift"), 0
            )
            shifts[f"{driver}_shift"] = (
                float(triang.ppf(quantile, 0.5, loc=-spread, scale=2 * spread)) if spread else 0
            )
            scenario, rate = _scenario(assumptions, shifts)
            prices.append(calculate(scenario, data, discount_rate=rate)["price_per_share"])
        rows.append({"driver": driver, "p10_input": prices[0], "p90_input": prices[1]})
    return pd.DataFrame(rows).set_index("driver")
