"""Phase 4, Module 6 — Analytical visualizations.

Every chart here is justified by a specific documented business question
or statistical-assumption check — none is decorative. These are
analytical visuals for this phase's own review, not the final Power BI
visual design (explicitly out of scope, per Step 17).
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy import stats

from _common import load_cleaned_data, logger
from config import FIGURES_DIR

plt.rcParams.update({
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "axes.edgecolor": "#444444",
    "axes.grid": True,
    "grid.color": "#dddddd",
    "grid.linewidth": 0.6,
    "font.size": 10,
})


def save(fig, name: str) -> None:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    path = FIGURES_DIR / f"{name}.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    logger.info("Saved %s", path)


def chart_delivery_time_distribution(df: pd.DataFrame) -> None:
    """Overall delivery-time distribution — supports PYTHON_ANALYSIS_PLAN.md's
    EDA requirement and the delivery_bucket bin-edge review."""
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.hist(df["Delivery_Time"], bins=52, color="#3a6ea5", edgecolor="white", linewidth=0.3)
    median = df["Delivery_Time"].median()
    p90 = np.percentile(df["Delivery_Time"], 90)
    ax.axvline(median, color="#c0392b", linestyle="--", linewidth=1.2, label=f"Median = {median:.0f} min")
    ax.axvline(p90, color="#e67e22", linestyle="--", linewidth=1.2, label=f"P90 = {p90:.0f} min")
    ax.set_title("Delivery Time Distribution (n=43,648)")
    ax.set_xlabel("Delivery time (minutes)")
    ax.set_ylabel("Number of deliveries")
    ax.legend()
    save(fig, "01_delivery_time_distribution")


def chart_breach_rate_by_area(df: pd.DataFrame) -> None:
    """Supports Business Questions #1, #8, #16 (Q01/Q08/Q16)."""
    rates = (df.groupby("Area")["sla_breach_flag"].mean() * 100).sort_values(ascending=False)
    fig, ax = plt.subplots(figsize=(7, 4))
    bars = ax.bar(rates.index, rates.values, color="#3a6ea5")
    for bar, val in zip(bars, rates.values):
        ax.text(bar.get_x() + bar.get_width() / 2, val + 1, f"{val:.1f}%", ha="center", fontsize=9)
    ax.set_ylim(0, 110)
    ax.set_title("SLA Breach Rate by Area (analyst-defined benchmark)")
    ax.set_ylabel("Breach rate (%)")
    save(fig, "02_breach_rate_by_area")


def chart_delivery_time_by_category(df: pd.DataFrame) -> None:
    """Supports Business Questions #6, #18 (Q06/Q18)."""
    order = df.groupby("Category")["Delivery_Time"].mean().sort_values(ascending=False).index
    fig, ax = plt.subplots(figsize=(9, 4.5))
    data = [df.loc[df["Category"] == c, "Delivery_Time"].to_numpy() for c in order]
    ax.boxplot(data, tick_labels=list(order), showfliers=False)
    ax.set_title("Delivery Time by Category (box = IQR, whiskers = 1.5xIQR, outliers hidden for readability)")
    ax.set_ylabel("Delivery time (minutes)")
    ax.tick_params(axis="x", rotation=60)
    save(fig, "03_delivery_time_by_category")


def chart_weekly_trend(df: pd.DataFrame) -> None:
    """Supports Business Question #11 (Q11/Q17) — weekly avg/P90 trend."""
    weekly = df.groupby("week_number").agg(
        avg=("Delivery_Time", "mean"),
        p90=("Delivery_Time", lambda s: np.percentile(s, 90)),
        n=("Delivery_Time", "count"),
    )
    order_date = pd.to_datetime(df["Order_Date"])
    distinct_days = df.assign(_d=order_date).groupby("week_number")["_d"].nunique()
    partial = distinct_days < 7

    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(weekly.index, weekly["avg"], marker="o", label="Average", color="#3a6ea5")
    ax.plot(weekly.index, weekly["p90"], marker="o", label="P90", color="#e67e22")
    for wk in weekly.index:
        if partial.get(wk, False):
            ax.axvspan(wk - 0.3, wk + 0.3, color="#cccccc", alpha=0.3)
    ax.set_title("Weekly Delivery Time Trend (shaded = partial week, <7 distinct days observed)")
    ax.set_xlabel("ISO week number")
    ax.set_ylabel("Delivery time (minutes)")
    ax.legend()
    save(fig, "04_weekly_trend")


def chart_distance_scatter(df: pd.DataFrame) -> None:
    """Linearity review for STATISTICAL_ANALYSIS.md Test 4's assumption
    check — visual complement to the quantitative Pearson/Spearman gap
    diagnostic in Module 4."""
    valid = df.loc[df["coordinates_valid_flag"]]
    sample = valid.sample(n=min(4000, len(valid)), random_state=42)
    r = stats.pearsonr(valid["distance_km"], valid["Delivery_Time"])[0]

    fig, ax = plt.subplots(figsize=(7, 5))
    ax.scatter(sample["distance_km"], sample["Delivery_Time"], s=6, alpha=0.25, color="#3a6ea5")
    z = np.polyfit(valid["distance_km"], valid["Delivery_Time"], 1)
    xs = np.linspace(valid["distance_km"].min(), valid["distance_km"].max(), 100)
    ax.plot(xs, np.polyval(z, xs), color="#c0392b", linewidth=1.5, label=f"Linear fit (Pearson r={r:.3f})")
    ax.set_title(f"Distance vs. Delivery Time (n={len(valid):,} coordinate-valid rows; {len(sample):,} plotted)")
    ax.set_xlabel("Distance (km)")
    ax.set_ylabel("Delivery time (minutes)")
    ax.legend()
    save(fig, "05_distance_vs_delivery_time_scatter")


def chart_agent_rating_scatter(df: pd.DataFrame) -> None:
    """Linearity review for STATISTICAL_ANALYSIS.md Test 3's assumption check."""
    valid = df.loc[df["agent_rating_valid_flag"]]
    band_means = valid.groupby("Agent_Rating")["Delivery_Time"].mean()

    fig, ax = plt.subplots(figsize=(7, 5))
    ax.scatter(band_means.index, band_means.values, s=25, color="#3a6ea5")
    ax.set_title(f"Average Delivery Time by Agent Rating (n={len(valid):,} rating-valid rows)")
    ax.set_xlabel("Agent rating")
    ax.set_ylabel("Average delivery time (minutes)")
    save(fig, "06_agent_rating_vs_delivery_time")


def chart_pareto_area_traffic(df: pd.DataFrame) -> None:
    """Supports KPI_DEFINITIONS.md #7 (Pareto concentration) — cross-validates
    against sql/analysis/Q20."""
    g = (
        df.groupby(["Area", "Traffic"])["sla_breach_flag"]
        .sum()
        .sort_values(ascending=False)
        .reset_index()
    )
    g.columns = ["Area", "Traffic", "breach_count"]
    g["segment"] = g["Area"] + " / " + g["Traffic"]
    g["cumulative_pct"] = 100 * g["breach_count"].cumsum() / g["breach_count"].sum()

    fig, ax1 = plt.subplots(figsize=(10, 5))
    ax1.bar(g["segment"], g["breach_count"], color="#3a6ea5")
    ax1.set_ylabel("Breach count")
    ax1.tick_params(axis="x", rotation=75)
    ax2 = ax1.twinx()
    ax2.plot(g["segment"], g["cumulative_pct"], color="#c0392b", marker="o", markersize=3)
    ax2.set_ylabel("Cumulative % of total breaches")
    ax2.set_ylim(0, 105)
    ax1.set_title("Pareto: Breach Concentration by Area x Traffic")
    save(fig, "07_pareto_area_traffic")


def main() -> None:
    df = load_cleaned_data()
    chart_delivery_time_distribution(df)
    chart_breach_rate_by_area(df)
    chart_delivery_time_by_category(df)
    chart_weekly_trend(df)
    chart_distance_scatter(df)
    chart_agent_rating_scatter(df)
    chart_pareto_area_traffic(df)
    logger.info("Module 6 (visualizations) complete: 7 figures written to %s", FIGURES_DIR)


if __name__ == "__main__":
    main()
