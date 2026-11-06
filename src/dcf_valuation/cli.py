"""Build the complete research artifacts offline; live quotes require --live."""

import argparse
import json
from pathlib import Path

from .charts import save_charts
from .market import get_quote
from .model import Assumptions, calculate, load_data
from .monte_carlo import SimulationConfig, simulate
from .workbook import build_workbook


def main() -> None:
    parser = argparse.ArgumentParser(description="WEG: DCF, Monte Carlo, Excel e quatro gráficos")
    parser.add_argument("--output", type=Path, default=Path("outputs/weg-dcf.xlsx"))
    parser.add_argument("--charts-dir", type=Path, default=Path("charts"))
    parser.add_argument("--samples", type=int, default=10_000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--live", action="store_true", help="Buscar cotação live; erros são explícitos"
    )
    parser.add_argument(
        "--assumptions", type=Path, help="JSON com campos de Assumptions para substituir"
    )
    args = parser.parse_args()
    try:
        data = load_data()
        overrides = json.loads(args.assumptions.read_text()) if args.assumptions else {}
        if not isinstance(overrides, dict):
            raise ValueError("assumptions must be a JSON object")
        assumptions = Assumptions(**(data.get("assumptions", {}) | overrides))
        config = SimulationConfig(samples=args.samples, seed=args.seed)
        config.validate_support(assumptions)
        quote = get_quote(live=args.live)
        result = calculate(assumptions, data)
        simulation = simulate(assumptions, config, data)
        destination = build_workbook(
            args.output, assumptions, data=data, simulation=simulation, quote=quote
        )
        charts = save_charts(simulation, args.charts_dir, data=data, quote=quote)
        summary = {
            "valuation": result,
            "monte_carlo": simulation.summary,
            "simulation_config": config.metadata(),
            "quote": quote,
        }
        destination.with_suffix(".json").write_text(json.dumps(summary, indent=2) + "\n")
    except (ValueError, TypeError, OSError, RuntimeError) as error:
        parser.error(str(error))
    print(f"Arquivo: {destination}; gráficos: {len(charts)} em {args.charts_dir}")
    print(f"Data de valuation: {data['valuation_date']}; cinco períodos anuais completos.")
    print(f"WACC: {result['wacc']:.2%}")
    print(f"Enterprise value: R$ {result['enterprise_value']:,.2f} milhões")
    print(f"Fair value base por ação: R$ {result['price_per_share']:.2f}")
    print(
        f"Monte Carlo P05/P50/P95: {simulation.summary['p05']:.2f} / "
        f"{simulation.summary['p50']:.2f} / {simulation.summary['p95']:.2f}"
    )
    print(f"Cotação: R$ {quote['price']:.2f} em {quote['timestamp']} ({quote['provider']})")
    print("Premissas ilustrativas; não é previsão de preço nem recomendação.")
    print("DCF recalcula no Excel; MonteCarlo é snapshot e exige reexecutar Python após editar.")


if __name__ == "__main__":
    main()
