from dataclasses import replace

import numpy as np
import pandas as pd
import pytest
from matplotlib.image import imread
from openpyxl import load_workbook

from dcf_valuation.charts import save_charts
from dcf_valuation.model import Assumptions, calculate, load_data
from dcf_valuation.monte_carlo import SimulationConfig, simulate, tornado
from dcf_valuation.workbook import build_workbook


@pytest.fixture
def data():
    return load_data("weg_2024.json")


@pytest.fixture
def simulation(data):
    return simulate(Assumptions(), SimulationConfig(samples=64), data)


def test_seed_reproduces_full_paths_and_different_seed_changes_them(data, simulation):
    same = simulate(Assumptions(), SimulationConfig(samples=64), data)
    pd.testing.assert_frame_equal(simulation.samples, same.samples)
    pd.testing.assert_frame_equal(simulation.revenue, same.revenue)
    other = simulate(Assumptions(), SimulationConfig(samples=64, seed=43), data)
    assert not simulation.samples.equals(other.samples)
    assert (simulation.samples.wacc > simulation.samples.terminal_growth).all()
    assert simulation.summary["p05"] < simulation.summary["p50"] < simulation.summary["p95"]


def test_one_draw_matches_independent_cash_flow_discounting(data, simulation):
    draw = simulation.samples.iloc[0]
    a = Assumptions()
    revenue = data["historical"][-1]["revenue"]
    previous_nwc = revenue * a.opening_nwc_ratio
    flows = []
    for i in range(5):
        revenue *= 1 + a.growth[i] + draw.growth_shift
        ebit = revenue * (a.ebit_margin[i] + draw.margin_shift)
        nwc = revenue * a.nwc_ratio[i]
        flows.append(
            ebit * (1 - a.tax_rate)
            + revenue * (a.da_ratio[i] - a.capex_ratio[i])
            - nwc
            + previous_nwc
        )
        previous_nwc = nwc
        assert simulation.revenue.iloc[0, i] == pytest.approx(revenue)
    terminal = flows[-1] * (1 + draw.terminal_growth) / (draw.wacc - draw.terminal_growth)
    ev = sum(flow / (1 + draw.wacc) ** t for t, flow in enumerate(flows, 1))
    ev += terminal / (1 + draw.wacc) ** 5
    assert draw.price_per_share == pytest.approx((ev + a.cash - a.debt - a.other_claims) / a.shares)


def test_zero_spreads_reduce_to_dcf_and_tornado(data):
    config = SimulationConfig(
        samples=3, growth_spread=0, margin_spread=0, wacc_spread=0, terminal_spread=0
    )
    result = simulate(Assumptions(), config, data)
    expected = calculate(Assumptions(), data)["price_per_share"]
    np.testing.assert_allclose(result.samples.price_per_share, expected)
    np.testing.assert_allclose(tornado(Assumptions(), config, data), expected)


@pytest.mark.parametrize(
    "overrides",
    [
        {"samples": 0},
        {"samples": True},
        {"seed": -1},
        {"seed": 2.5},
        {"growth_spread": -0.1},
        {"margin_spread": float("nan")},
    ],
)
def test_invalid_configuration(overrides):
    with pytest.raises(ValueError):
        SimulationConfig(**overrides)


@pytest.mark.parametrize(
    "overrides",
    [
        {"growth_spread": 2},
        {"margin_spread": 0.3},
        {"wacc_spread": 0.2},
        {"terminal_spread": 0.2},
    ],
)
def test_invalid_entire_support_rejected_before_sampling(data, overrides):
    with pytest.raises(ValueError):
        simulate(Assumptions(), SimulationConfig(samples=1, **overrides), data)


def test_four_real_pngs_and_eight_sheet_snapshot(tmp_path, data, simulation):
    paths = save_charts(simulation, tmp_path, data=data)
    assert len(paths) == 4
    for path in paths:
        assert path.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
        pixels = imread(path)
        assert pixels.shape[0] >= 700 and pixels.std() > 0.05
    path = build_workbook(tmp_path / "model.xlsx", Assumptions(), data=data, simulation=simulation)
    book = load_workbook(path)
    assert len(book.sheetnames) == 8
    sheet = book["MonteCarlo"]
    assert sheet["D7"].value == 42
    assert sheet["D8"].value == 64
    assert "STALE" in sheet["D22"].value
    assert sheet["I27"].value == pytest.approx(simulation.samples.iloc[0].price_per_share)
    assert sheet.max_row == 90
    with pytest.raises(ValueError, match="match"):
        build_workbook(
            tmp_path / "bad.xlsx", replace(Assumptions(), cash=0), data=data, simulation=simulation
        )


def test_projection_dates_start_at_valuation_not_last_reporting_period(data):
    data = {**data, "valuation_date": "2026-11-06"}
    result = calculate(Assumptions(), data)
    assert result["projections"][0]["period_end"] == "2027-11-06"
    assert result["projections"][-1]["period_end"] == "2031-11-06"
