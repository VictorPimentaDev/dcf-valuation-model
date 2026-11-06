"""Versioned artifacts and prose must stay what the code regenerates today."""

import json
import math
import re
import subprocess
import sys
from pathlib import Path

import pytest
from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parents[1]
RESULT = json.loads((ROOT / "examples/weg-research.json").read_text())
DOCS = {name: (ROOT / name).read_text() for name in ("README.md", "docs/pitch.md")}


def brl(value: float) -> str:
    return f"{value:.2f}".replace(".", ",")


@pytest.fixture(scope="module")
def regenerated(tmp_path_factory):
    folder = tmp_path_factory.mktemp("regenerated")
    subprocess.run(
        [
            sys.executable, "-m", "dcf_valuation",
            "--output", str(folder / "weg-research.xlsx"),
            "--charts-dir", str(folder / "charts"),
            "--samples", "10000",
            "--seed", "42",
        ],
        check=True,
        capture_output=True,
    )
    return folder


def test_versioned_summary_matches_regeneration(regenerated):
    fresh = json.loads((regenerated / "weg-research.json").read_text())
    assert _close(fresh, RESULT)


def _close(left, right) -> bool:
    if isinstance(left, dict):
        return left.keys() == right.keys() and all(_close(left[k], right[k]) for k in left)
    if isinstance(left, list):
        return len(left) == len(right) and all(map(_close, left, right))
    if isinstance(left, float):
        return math.isclose(left, right, rel_tol=1e-9)
    return left == right


def test_versioned_workbook_cells_match_regeneration(regenerated):
    versioned = load_workbook(ROOT / "examples/weg-research.xlsx")
    fresh = load_workbook(regenerated / "weg-research.xlsx")
    assert versioned.sheetnames == fresh.sheetnames
    for sheet in versioned:
        assert sheet.dimensions == fresh[sheet.title].dimensions
        for row in sheet.iter_rows():
            for cell in row:
                assert _close(cell.value, fresh[sheet.title][cell.coordinate].value), (
                    sheet.title,
                    cell.coordinate,
                )


def test_readme_lists_the_real_tabs_in_workbook_order():
    tabs = re.findall(r"^\| (\w+) \| ", DOCS["README.md"], re.M)
    assert tabs[1:] == load_workbook(ROOT / "examples/weg-research.xlsx").sheetnames


@pytest.mark.parametrize("name", DOCS)
def test_headline_numbers_and_quote_times_match_artifacts(name):
    text = DOCS[name]
    summary = RESULT["monte_carlo"]
    for value in (RESULT["valuation"]["price_per_share"], RESULT["quote"]["price"]):
        assert brl(value) in text
    for key in ("p05", "p50", "p95"):
        assert brl(summary[key]) in text
    assert "17:50:34" in text and "18:05:36" in text  # market time and retrieval, −03:00
    assert RESULT["quote"]["timestamp"] == "2026-11-06T17:50:34-03:00"
    assert RESULT["quote"]["fetched_at"].startswith("2026-11-06T21:05:36")


def test_methodology_states_the_simulated_monte_carlo_support():
    text = (ROOT / "docs/methodology.md").read_text()
    config = RESULT["simulation_config"]
    wacc = RESULT["valuation"]["wacc"]
    low, high = wacc - config["wacc_spread"], wacc + config["wacc_spread"]
    assert f"{low:.3%}".replace(".", ",") in text and f"{high:.3%}".replace(".", ",") in text
    assert f"{config['samples']:,}".replace(",", ".") in text and "seed=42" in text
    assert "entre −5 e +5" in text and "entre −4 e +4" in text
    assert "2,5% a 5,5%" in text
