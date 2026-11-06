from dataclasses import replace
from decimal import Decimal
from math import nan

import pytest

from dcf_valuation.model import Assumptions, calculate, load_data
from dcf_valuation.revenue import build_revenue
from dcf_valuation.sensitivity import enterprise_value, sensitivity_table
from dcf_valuation.statements import enterprise_to_equity, unlevered_cash_flow
from dcf_valuation.terminal import terminal_value
from dcf_valuation.wacc import cost_of_equity, wacc


def test_capm_and_wacc_by_hand():
    assert cost_of_equity(0.08, 1.2, 0.05) == pytest.approx(0.14)
    assert wacc(0.14, 0.10, 0.34, 0.25) == pytest.approx(0.1215)
    assert wacc(0.14, 0.10, 0.34, 0) == 0.14
    assert wacc(0.14, 0.10, 0.34, 1) == pytest.approx(0.066)


def test_revenue_and_cash_flow_signs():
    assert build_revenue(100, [0.1, -0.2]) == pytest.approx([110, 88])
    assert unlevered_cash_flow(100, 0.30, 10, 20, 5) == 55
    assert unlevered_cash_flow(-100, 0.30, 10, 20, -5) == -105
    assert enterprise_to_equity(100, 20, 30, 5) == 85
    assert enterprise_to_equity(10, 0, 30) == -20


def test_terminal_and_discounting_by_hand():
    assert terminal_value(100, 0.1, 0.02) == 1275
    # Two-year horizon: 90 at t1, 100 at t2 and TV at t2, never t3.
    expected = 90 / 1.1 + (100 + 1275) / 1.1**2
    assert enterprise_value([90, 100], 0.1, 0.02) == pytest.approx(expected)


def test_sensitivity_reprices_each_cash_flow():
    matrix = sensitivity_table(
        [90, 100],
        [0.09, 0.10, 0.11],
        [0.01, 0.02, 0.12],
        cash=20,
        debt=10,
        other_claims=2,
        shares=10,
    )
    assert matrix[1][1] == pytest.approx((90 / 1.1 + (100 + 1275) / 1.1**2 + 8) / 10)
    assert matrix[0][1] > matrix[1][1] > matrix[2][1]
    assert matrix[1][1] > matrix[1][0]
    assert all(row[2] is None for row in matrix)


def test_default_model_against_independent_decimal_calculation():
    d = Decimal
    revenue, old_nwc = d("37986.941"), d("37986.941") * d("0.20")
    flows = []
    for growth in ("0.12", "0.11", "0.10", "0.09", "0.08"):
        revenue *= 1 + d(growth)
        nwc = revenue * d("0.20")
        flow = revenue * (d("0.20") * d("0.66") + d("0.025") - d("0.045"))
        flows.append(flow - (nwc - old_nwc))
        old_nwc = nwc
    rate = d("0.154") * d("0.90") + d("0.12") * d("0.66") * d("0.10")
    ev = sum(flow / (1 + rate) ** year for year, flow in enumerate(flows, 1))
    ev += flows[-1] * d("1.04") / (rate - d("0.04")) / (1 + rate) ** 5
    price = (ev + d("8013.210") - d("3595.237") - 500) / d("4197.317998")
    result = calculate(Assumptions(), load_data("weg_2024.json"))
    assert result["enterprise_value"] == pytest.approx(float(ev))
    assert result["price_per_share"] == pytest.approx(float(price))
    assert result["projections"][0]["fcff"] == pytest.approx(float(flows[0]))
    assert result["projections"][-1]["fcff"] == pytest.approx(float(flows[-1]))


@pytest.mark.parametrize(
    "overrides",
    [
        {"shares": 0},
        {"shares": True},
        {"cash": -1},
        {"debt": nan},
        {"tax_rate": 1.01},
        {"debt_weight": -0.1},
        {"beta": -1},
        {"terminal_growth": 0.20},
        {"terminal_growth": -1},
        {"growth": [0.1]},
        {"growth": [-1] * 5},
        {"growth": ["0.1"] * 5},
        {"ebit_margin": [nan] * 5},
        {"capex_ratio": [-0.1] * 5},
        {"opening_nwc_ratio": 1.1},
    ],
)
def test_reject_invalid_assumptions(overrides):
    with pytest.raises(ValueError):
        Assumptions(**overrides)


def test_zero_growth_and_zero_capex_are_supported():
    result = calculate(replace(Assumptions(), growth=(0,) * 5, capex_ratio=(0,) * 5))
    assert all(period["delta_nwc"] == 0 for period in result["projections"])


def test_empty_flows_and_invalid_terminal_spread():
    with pytest.raises(ValueError):
        enterprise_value([], 0.1, 0.02)
    with pytest.raises(ValueError):
        terminal_value(100, 0.1, 0.1)


def test_source_fixture_units_and_provenance():
    data = load_data("weg_2024.json")
    assert data["historical"][-1]["revenue"] == 37986.941
    assert data["historical"][-1]["ebitda"] - data["historical"][-1]["da"] == pytest.approx(
        7690.528
    )
    assert data["valuation_date"] == "2024-12-31"
    assert data["sources"][0]["url"].startswith("https://api.mziq.com/")
