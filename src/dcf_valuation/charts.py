"""Four static research figures from the same reproducible simulation as Excel."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from .model import calculate, load_data
from .monte_carlo import Simulation, tornado

NAVY, TEAL, RED = "#173b4f", "#008c95", "#bd5b48"


def save_charts(
    simulation: Simulation,
    output_dir: str | Path = "charts",
    *,
    data: dict | None = None,
    quote: dict | None = None,
) -> list[Path]:
    data = data or load_data()
    quote = quote or data.get("quote")
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    prices = simulation.samples["price_per_share"]
    base = calculate(simulation.assumptions, data)["price_per_share"]
    paths = []
    stamp = (
        f"WEGE3 · R$ {quote['price']:.2f} · {quote['timestamp']} · {quote['provider']}"
        if quote
        else "Market quote unavailable"
    )
    footer = (
        f"As of {simulation.valuation_date} · {len(prices):,} scenarios "
        f"· seed {simulation.config.seed}"
        "\nSubjective fair-value scenarios, not a share-price forecast. "
        "Independent triangular inputs."
    )
    with plt.rc_context(
        {
            "font.family": "DejaVu Sans",
            "font.size": 11,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.labelcolor": NAVY,
            "text.color": NAVY,
            "axes.edgecolor": "#aab7bd",
            "figure.facecolor": "#f8fafb",
            "axes.facecolor": "#f8fafb",
            "savefig.facecolor": "#f8fafb",
            "grid.alpha": 0.2,
        }
    ):

        def finish(fig, ax, name, title, subtitle, *, left=0.1):
            fig.suptitle(title, x=0.1, y=0.95, ha="left", fontsize=20, fontweight="bold")
            fig.text(0.1, 0.87, subtitle, fontsize=10, color="#526574")
            fig.text(0.1, 0.045, footer, fontsize=8, color="#526574", linespacing=1.6)
            ax.grid(axis="y")
            ax.set_axisbelow(True)
            fig.subplots_adjust(left=left, right=0.95, top=0.79, bottom=0.22)
            path = output / name
            fig.savefig(path, dpi=160, metadata={"Description": str(quote or {})})
            plt.close(fig)
            paths.append(path)

        fig, ax = plt.subplots(figsize=(11, 6.5))
        ax.hist(prices, bins=65, color=TEAL, edgecolor="#f8fafb", linewidth=0.4)
        ax.axvline(base, color=NAVY, lw=2, label=f"Base DCF R$ {base:.2f}")
        if quote:
            ax.axvline(quote["price"], color=RED, lw=2, label=f"Market R$ {quote['price']:.2f}")
        ax.set(xlabel="Fair value per share (BRL)", ylabel="Scenarios")
        ax.legend(frameon=False)
        finish(fig, ax, "fair_value_histogram.png", "WEG · What the assumptions imply", stamp)

        fig, ax = plt.subplots(figsize=(11, 6.5))
        years = np.arange(1, 6)
        revenue = simulation.revenue / 1000
        for low, high, alpha in ((0.05, 0.95, 0.15), (0.25, 0.75, 0.3)):
            ax.fill_between(
                years,
                revenue.quantile(low),
                revenue.quantile(high),
                color=TEAL,
                alpha=alpha,
                label=f"P{low * 100:.0f}–P{high * 100:.0f}",
            )
        ax.plot(years, revenue.median(), color=TEAL, lw=2.5, label="Median")
        ax.set(
            xticks=years,
            xlabel="Full annual periods after valuation date",
            ylabel="Annual net revenue (BRL billion)",
        )
        ax.legend(frameon=False)
        finish(
            fig,
            ax,
            "revenue_fan.png",
            "WEG · A range of operating outcomes",
            "One persistent growth shift per scenario; bands are model percentiles.",
        )

        fig, ax = plt.subplots(figsize=(11, 6.5))
        impacts = tornado(simulation.assumptions, simulation.config, data)
        impacts["width"] = abs(impacts["p90_input"] - impacts["p10_input"])
        impacts = impacts.sort_values("width")
        for y, (_, row) in enumerate(impacts.iterrows()):
            ax.plot([row.p10_input, row.p90_input], [y, y], color=TEAL, lw=13, alpha=0.6)
            ax.scatter([row.p10_input, row.p90_input], [y, y], c=[NAVY, RED], s=45, zorder=3)
        ax.axvline(base, color=NAVY, linestyle="--", lw=1)
        ax.set(
            yticks=range(4),
            yticklabels=[
                {
                    "growth": "Revenue growth",
                    "margin": "EBIT margin",
                    "wacc": "WACC",
                    "terminal": "Terminal growth",
                }[d]
                for d in impacts.index
            ],
            xlabel="Fair value per share (BRL)",
        )
        ax.scatter([], [], color=NAVY, label="Input P10")
        ax.scatter([], [], color=RED, label="Input P90")
        ax.legend(frameon=False)
        finish(
            fig,
            ax,
            "sensitivity_tornado.png",
            "WEG · Which inputs move value?",
            "One-at-a-time P10/P90 input changes; other inputs fixed. Not a causal estimate.",
            left=0.2,
        )

        fig, ax = plt.subplots(figsize=(11, 6.5))
        quantiles = prices.quantile([0.05, 0.25, 0.5, 0.75, 0.95])
        ax.plot(quantiles.iloc[[0, 4]], [0, 0], lw=3, color=TEAL, label="P05–P95")
        ax.plot(quantiles.iloc[[1, 3]], [0, 0], lw=18, color=TEAL, alpha=0.5, label="P25–P75")
        ax.scatter([quantiles.iloc[2]], [0], color=NAVY, s=100, zorder=3, label="Median")
        for index, label, offset in ((0, "P05", 32), (2, "P50", -42), (4, "P95", 32)):
            x = quantiles.iloc[index]
            ax.annotate(
                f"{label}\nR$ {x:.2f}",
                (x, 0),
                xytext=(0, offset),
                textcoords="offset points",
                ha="center",
                fontsize=9,
                arrowprops={"arrowstyle": "-", "color": "#aab7bd"},
            )
        if quote:
            ax.axvline(quote["price"], color=RED, lw=2, label="Market quote")
        ax.set(ylim=(-0.7, 0.7), yticks=[], xlabel="Fair value per share (BRL)")
        ax.legend(frameon=False, loc="lower left", ncol=4)
        finish(fig, ax, "price_vs_distribution.png", "WEG · Market price and model value", stamp)
    return paths
