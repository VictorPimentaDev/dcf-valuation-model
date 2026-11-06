import math
import subprocess
import sys

import pytest
from openpyxl import load_workbook
from openpyxl.formula import Tokenizer
from openpyxl.utils.cell import range_boundaries

from dcf_valuation.model import Assumptions, load_data
from dcf_valuation.monte_carlo import SimulationConfig, simulate
from dcf_valuation.workbook import build_workbook


def value(book, sheet, address):
    """Evaluate this workbook's small formula subset; not an Excel compatibility test."""
    cell = book[sheet][address]
    if cell.data_type != "f":
        return cell.value

    def reference(text):
        location, target = text.rsplit("!", 1) if "!" in text else (sheet, text)
        location, target = location.strip("'"), target.replace("$", "")
        if ":" not in target:
            return value(book, location, target)
        left, top, right, bottom = range_boundaries(target)
        return [
            value(book, location, book[location].cell(row, column).coordinate)
            for row in range(top, bottom + 1)
            for column in range(left, right + 1)
        ]

    def flatten(items):
        return [number for item in items for number in (item if isinstance(item, list) else [item])]

    environment = {
        "SUM": lambda *items: sum(flatten(items)),
        "MIN": lambda *items: min(flatten(items)),
        "MAX": lambda *items: max(flatten(items)),
        "COUNT": lambda items: sum(isinstance(item, (int, float)) for item in items),
        "AND": lambda *items: all(items),
        "IF": lambda condition, yes, no: yes if condition else no,
        "NA": lambda: math.nan,
        "NPV": lambda rate, flows: sum(x / (1 + rate) ** t for t, x in enumerate(flows, 1)),
    }
    expression = ""
    for token in Tokenizer(cell.value).items:
        if token.type == "OPERAND" and token.subtype == "RANGE":
            expression += repr(reference(token.value))
        else:
            expression += {"^": "**", "=": "==", "<>": "!="}.get(token.value, token.value)
    # Only trusted formulas created by our own builder are evaluated in this test.
    return eval(expression, {"__builtins__": {}}, environment)


@pytest.fixture
def workbook(tmp_path):
    data = load_data("weg_2024.json")
    a = Assumptions()
    simulation = simulate(a, SimulationConfig(samples=8), data)
    return load_workbook(build_workbook(tmp_path / "weg.xlsx", a, data=data, simulation=simulation))


def test_workbook_structure_and_base_math(workbook):
    assert workbook.sheetnames == [
        "Assumptions",
        "Historical",
        "Projections",
        "DCF",
        "WACC",
        "Sensitivity",
        "MonteCarlo",
        "Sources",
    ]
    assert value(workbook, "WACC", "D17") == pytest.approx(0.14652)
    assert value(workbook, "DCF", "D18") == pytest.approx(45324.88761380048)
    assert value(workbook, "DCF", "D24") == pytest.approx(11.73198233664079)
    assert value(workbook, "Sensitivity", "F9") == pytest.approx(value(workbook, "DCF", "D24"))
    assert value(workbook, "Sensitivity", "F7") > value(workbook, "Sensitivity", "F11")
    assert value(workbook, "Sensitivity", "H9") > value(workbook, "Sensitivity", "D9")
    assert workbook.calculation.fullCalcOnLoad
    assert workbook["Assumptions"]["D7"].font.color.rgb == "000000FF"
    assert workbook["Sources"]["E7"].value.startswith("https://")
    assert all(sheet.freeze_panes == "D7" for sheet in workbook if sheet.title != "MonteCarlo")
    assert all(not sheet.sheet_view.showGridLines for sheet in workbook)
    assert len(workbook["Assumptions"].data_validations.dataValidation) == 8


@pytest.mark.parametrize(
    "cell,change", [("H7", 0.20), ("H8", 0.25), ("H9", 0.04), ("H10", 0.07), ("H11", 0.25)]
)
def test_later_year_inputs_flow_to_valuation_without_changing_prior_years(workbook, cell, change):
    original = value(workbook, "DCF", "D24")
    first = value(workbook, "Projections", "D17")
    workbook["Assumptions"][cell] = change
    assert value(workbook, "Projections", "D17") == first
    assert value(workbook, "DCF", "D24") != original
    assert value(workbook, "Sensitivity", "F9") == pytest.approx(value(workbook, "DCF", "D24"))


@pytest.mark.parametrize("cell,change", [("D27", 0), ("D22", 2), ("D7", -1), ("D24", -10)])
def test_excel_check_catches_pasted_invalid_inputs(workbook, cell, change):
    workbook["Assumptions"][cell] = change
    assert value(workbook, "Assumptions", "D30") is False
    assert value(workbook, "DCF", "D12") is False


def test_cli_builds_real_file_and_rejects_bad_json(tmp_path):
    path = tmp_path / "cli.xlsx"
    success = subprocess.run(
        [
            sys.executable,
            "-m",
            "dcf_valuation",
            "--output",
            str(path),
            "--samples",
            "16",
            "--charts-dir",
            str(tmp_path / "charts"),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    assert "Monte Carlo P05/P50/P95" in success.stdout
    assert len(list((tmp_path / "charts").glob("*.png"))) == 4
    assert path.with_suffix(".json").exists()
    assert load_workbook(path)["DCF"]["D24"].value == "=D22/D23"
    invalid = tmp_path / "invalid.json"
    invalid.write_text('{"shares": 0}')
    failure = subprocess.run(
        [sys.executable, "-m", "dcf_valuation", "--assumptions", str(invalid)],
        capture_output=True,
        text=True,
    )
    assert failure.returncode == 2
    assert "shares must be positive" in failure.stderr


def test_monte_carlo_snapshot_marks_changed_inputs_stale(workbook):
    assert value(workbook, "MonteCarlo", "D22") == "CURRENT"
    workbook["Assumptions"]["D7"] = 0.25
    assert value(workbook, "MonteCarlo", "D22") == "STALE — rerun Python"


def test_current_fixture_excel_matches_python(tmp_path):
    from dcf_valuation.model import calculate, load_assumptions

    data = load_data()
    assumptions = load_assumptions(data)
    simulation = simulate(assumptions, SimulationConfig(samples=2), data)
    workbook = load_workbook(
        build_workbook(tmp_path / "current.xlsx", assumptions, data=data, simulation=simulation)
    )
    assert value(workbook, "DCF", "D24") == pytest.approx(
        calculate(assumptions, data)["price_per_share"]
    )
    assert workbook["Assumptions"]["D6"].value == "2027-11-06"
