"""Render the repository card from the versioned research simulation."""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from dcf_valuation.model import load_assumptions, load_data
from dcf_valuation.monte_carlo import simulate

root = Path(__file__).resolve().parents[1]
data = load_data()
values = simulate(load_assumptions(data), data=data).samples.price_per_share
fig = plt.figure(figsize=(12.8, 6.4), dpi=100, facecolor="#102832")
fig.text(.06, .86, "PYTHON / B3 / OPEN RESEARCH", color="#6cd5c7", fontsize=15,
         fontfamily="DejaVu Sans Mono")
fig.text(.06, .63, "B3 equity\nresearch toolkit", color="white", fontsize=43,
         fontweight="bold", linespacing=1.15)
fig.text(.06, .27, "Stock pitch · DCF · Monte Carlo\nJupyter notebooks + editable Excel",
         color="#bed0d5", fontsize=18, linespacing=1.6)
ax = fig.add_axes((.64, .30, .30, .49), facecolor="#102832")
ax.hist(values, bins=45, color="#6cd5c7", alpha=.9)
ax.axvline(values.median(), color="white", linewidth=2)
ax.set(xticks=[], yticks=[])
for spine in ax.spines.values():
    spine.set_visible(False)
fig.text(.65, .24, "WEG · 10,000 model scenarios", color="#bed0d5", fontsize=12)
fig.text(.06, .08, "VictorPimentaDev / dcf-valuation-model", color="#6cd5c7", fontsize=13)
fig.text(.65, .08, "Illustrative assumptions, not advice", color="#bed0d5", fontsize=11)
(root / "assets").mkdir(exist_ok=True)
fig.savefig(root / "assets/social-preview.png", dpi=100, facecolor=fig.get_facecolor())
plt.close(fig)
