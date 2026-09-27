"""Figures for the README and notebooks (matplotlib only; navy = structure, teal = secondary, coral = breach)."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

NAVY, TEAL, CORAL = "#123B5D", "#00A6A6", "#E45756"
GREY, GRID, BG = "#6B7785", "#D9E1E8", "#FFFFFF"


def apply_theme() -> None:
    plt.rcParams.update({
        "figure.facecolor": BG, "axes.facecolor": BG, "axes.edgecolor": GRID, "axes.grid": True,
        "grid.color": GRID, "grid.linewidth": 0.7, "axes.axisbelow": True, "axes.spines.top": False,
        "axes.spines.right": False, "font.size": 10, "axes.titlesize": 12, "axes.titleweight": "bold",
        "axes.titlelocation": "left", "legend.frameon": False, "savefig.dpi": 150, "savefig.bbox": "tight",
    })


def _save(fig, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path)
    plt.close(fig)
    return path


def step_plot(table: pd.DataFrame, xlabel: str, cut: float, title: str, path: Path, note: str = "") -> Path:
    apply_theme()
    fig, ax = plt.subplots(figsize=(8.5, 4.2))
    ax.errorbar(table["value"], 100 * table["breach_rate"],
                yerr=[100 * (table["breach_rate"] - table["ci_low"]), 100 * (table["ci_high"] - table["breach_rate"])],
                fmt="o", color=NAVY, ecolor=GRID, capsize=2, ms=5)
    ax.axvline(cut - (0.05 if cut % 1 else 0.5), color=CORAL, ls="--", lw=1.4)
    ax.text(cut - (0.05 if cut % 1 else 0.5), 3, f"  step at {cut:g}", color=CORAL, fontsize=9)
    ax.set_xlabel(xlabel)
    ax.set_ylabel("SLA breach rate (%)")
    ax.set_ylim(0, 100)
    ax.set_title(title)
    if note:
        ax.text(0, -0.24, note, transform=ax.transAxes, fontsize=8.5, color=GREY, style="italic")
    return _save(fig, path)


def hour_profile_plot(hp: pd.DataFrame, path: Path) -> Path:
    apply_theme()
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(9, 6), sharex=True, gridspec_kw={"height_ratios": [1, 1.2]})
    a1.bar(hp["order_hour"], hp["n"], color=NAVY)
    a1.set_ylabel("Deliveries")
    a1.set_title("When are deliveries placed, and when do they breach?")
    a2.errorbar(hp["order_hour"], 100 * hp["breach_rate"],
                yerr=[100 * (hp["breach_rate"] - hp["ci_low"]), 100 * (hp["ci_high"] - hp["breach_rate"])],
                fmt="o-", color=CORAL, ecolor=GRID, capsize=2)
    a2.set_ylabel("SLA breach rate (%)")
    a2.set_xlabel("Order hour")
    a2.set_xticks(range(0, 24, 2))
    return _save(fig, path)


def traffic_hour_heatmap(df: pd.DataFrame, path: Path) -> Path:
    apply_theme()
    order = ["Low", "Medium", "High", "Jam"]
    n = df.pivot_table(index="order_hour", columns="traffic", values="breach_flag", aggfunc="size").reindex(columns=order)
    r = 100 * df.pivot_table(index="order_hour", columns="traffic", values="breach_flag", aggfunc="mean").reindex(columns=order)
    r = r.where(n >= 100)
    fig, ax = plt.subplots(figsize=(6.2, 6.2))
    im = ax.imshow(r.to_numpy(), cmap="Reds", vmin=0, vmax=60, aspect="auto")
    ax.set_xticks(range(len(order)), order)
    ax.set_yticks(range(len(r)), r.index)
    for i in range(r.shape[0]):
        for j in range(r.shape[1]):
            v = r.iat[i, j]
            if not np.isnan(v):
                ax.text(j, i, f"{v:.0f}%", ha="center", va="center", fontsize=8,
                        color="white" if v > 35 else "black")
    ax.grid(False)
    ax.set_title("Breach rate by hour and traffic\n(blank = fewer than 100 deliveries)", loc="left")
    fig.colorbar(im, ax=ax, label="Breach rate (%)", shrink=0.8)
    return _save(fig, path)


def traffic_weather_heatmap(df: pd.DataFrame, path: Path) -> Path:
    apply_theme()
    t_order = ["Low", "Medium", "High", "Jam"]
    w_order = ["Sunny", "Windy", "Sandstorms", "Stormy", "Cloudy", "Fog"]
    r = 100 * df.pivot_table(index="weather", columns="traffic", values="breach_flag", aggfunc="mean").reindex(index=w_order, columns=t_order)
    n = df.pivot_table(index="weather", columns="traffic", values="breach_flag", aggfunc="size").reindex(index=w_order, columns=t_order)
    fig, ax = plt.subplots(figsize=(6.6, 4.4))
    im = ax.imshow(r.to_numpy(), cmap="Reds", vmin=0, vmax=70, aspect="auto")
    ax.set_xticks(range(4), t_order)
    ax.set_yticks(range(6), w_order)
    for i in range(6):
        for j in range(4):
            ax.text(j, i, f"{r.iat[i, j]:.0f}%\nn={int(n.iat[i, j]):,}", ha="center", va="center", fontsize=8,
                    color="white" if r.iat[i, j] > 38 else "black")
    ax.grid(False)
    ax.set_title("The traffic effect depends on the weather", loc="left")
    fig.colorbar(im, ax=ax, label="Breach rate (%)", shrink=0.85)
    return _save(fig, path)


def risk_ratio_plot(rows: pd.DataFrame, path: Path,
                    title: str = "Breach risk ratio by factor (each vs. its reference level)") -> Path:
    """Dot-and-whisker plot of plain risk ratios (exposed rate / reference rate) with 95% CI.

    ``rows`` needs columns: label, risk_ratio, rr_ci_low, rr_ci_high. This is a descriptive
    comparison on one common scale, not a fitted statistical model.
    """
    apply_theme()
    c = rows.iloc[::-1]
    fig, ax = plt.subplots(figsize=(8, 0.5 * len(c) + 1.5))
    y = np.arange(len(c))
    ax.errorbar(c["risk_ratio"], y, xerr=[c["risk_ratio"] - c["rr_ci_low"], c["rr_ci_high"] - c["risk_ratio"]],
                fmt="o", color=NAVY, ecolor=GRID, capsize=2)
    ax.axvline(1, color=CORAL, ls="--", lw=1.2)
    ax.set_xscale("log")
    ax.set_yticks(y, c["label"])
    ax.set_xlabel("Risk ratio (log scale; 95% CI)")
    ax.set_title(title, loc="left")
    return _save(fig, path)


def sensitivity_plot(overall: pd.DataFrame, drivers: pd.DataFrame, path: Path) -> Path:
    apply_theme()
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4.2), gridspec_kw={"width_ratios": [1, 1.7]})
    a1.bar([f"P{int(100 * p)}" for p in overall["percentile"]], overall["breach_rate_pct"], color=CORAL)
    for i, v in enumerate(overall["breach_rate_pct"]):
        a1.text(i, v + 0.5, f"{v:.1f}%", ha="center", fontsize=9)
    a1.set_ylabel("Breach rate (%)")
    a1.set_title("Breach rate by SLA percentile")
    for label, sub in drivers.groupby("contrast"):
        a2.plot([f"P{int(100 * p)}" for p in sub["percentile"]], sub["risk_ratio"], marker="o", label=label)
    a2.axhline(1, color=GREY, lw=1)
    a2.set_yscale("log")
    a2.set_ylabel("Risk ratio (log scale)")
    a2.set_title("Do the driver contrasts survive a different SLA?")
    a2.legend(fontsize=8, loc="upper center", bbox_to_anchor=(0.5, -0.1), ncol=2)
    return _save(fig, path)


def pareto_plot(p: pd.DataFrame, path: Path) -> Path:
    apply_theme()
    fig, ax = plt.subplots(figsize=(10, 4.8))
    ax.bar(p["segment"], p["breaches"], color=CORAL)
    ax.set_ylabel("SLA breaches")
    ax.tick_params(axis="x", rotation=70)
    ax2 = ax.twinx()
    ax2.plot(p["segment"], 100 * p["cumulative_share"], color=NAVY, marker="o", ms=4)
    ax2.axhline(80, color=TEAL, ls="--", lw=1)
    ax2.set_ylim(0, 105)
    ax2.set_ylabel("Cumulative % of breaches")
    ax2.grid(False)
    ax.set_title("Breach concentration: area x traffic (deterministic order)")
    return _save(fig, path)


def scenario_plot(sc: pd.DataFrame, path: Path) -> Path:
    apply_theme()
    fig, ax = plt.subplots(figsize=(8, 3.2))
    y = np.arange(len(sc))
    ax.barh(y, sc["reduction_pct_of_all_breaches"], 0.5, color=CORAL)
    for yi, v in zip(y, sc["reduction_pct_of_all_breaches"]):
        ax.text(v + 0.5, yi, f"{v:.1f}%", va="center", fontsize=9)
    ax.set_yticks(y, [s.split(" breach rate")[0] for s in sc["scenario"]])
    ax.invert_yaxis()
    ax.set_xlabel("Theoretical reduction, % of all breaches (rate difference x volume)")
    ax.set_title("Illustrative scenarios (not causal forecasts)", loc="left")
    return _save(fig, path)
