"""CLI: one workbook and a matching numerical summary, without network calls."""

import argparse
import json
from pathlib import Path

from .model import Assumptions, calculate
from .workbook import build_workbook


def main() -> None:
    parser = argparse.ArgumentParser(description="DCF retrospectivo ilustrativo da WEG (base 2024)")
    parser.add_argument("--output", type=Path, default=Path("outputs/weg-dcf.xlsx"))
    parser.add_argument(
        "--assumptions", type=Path, help="JSON com campos de Assumptions para substituir"
    )
    args = parser.parse_args()
    try:
        overrides = json.loads(args.assumptions.read_text()) if args.assumptions else {}
        if not isinstance(overrides, dict):
            raise ValueError("assumptions must be a JSON object")
        assumptions = Assumptions(**overrides)
        result = calculate(assumptions)
        destination = build_workbook(args.output, assumptions)
    except (ValueError, TypeError, OSError) as error:
        parser.error(str(error))
    print(f"Arquivo: {destination}")
    print("Base 31/12/2024; premissas ilustrativas, sem cotação atual.")
    print(f"WACC: {result['wacc']:.2%}")
    print(f"Enterprise value: R$ {result['enterprise_value']:,.2f} milhões")
    print(f"Equity value: R$ {result['equity_value']:,.2f} milhões")
    print(f"Valor ilustrativo por ação: R$ {result['price_per_share']:.2f}")
    print("Excel: fórmulas recalculadas ao abrir em Excel/LibreOffice; sem cache no arquivo.")


if __name__ == "__main__":
    main()
