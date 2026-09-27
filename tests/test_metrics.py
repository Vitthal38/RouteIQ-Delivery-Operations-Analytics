"""KPI values and the statistical helper functions (unit tests with known answers)."""
import numpy as np
import pytest

from routeiq.analysis import segments
from routeiq.statistics import effects as fx


def test_headline_kpis(analytical):
    k = segments.kpis(analytical)
    assert k["total_deliveries"] == 43_648
    assert k["breached_deliveries"] == 10_328
    assert k["breach_rate_pct"] == pytest.approx(23.6620, abs=5e-5)
    assert k["on_time_rate_pct"] == pytest.approx(76.3380, abs=5e-5)
    assert k["average_delivery_minutes"] == pytest.approx(124.9145, abs=5e-5)
    assert k["p90_delivery_minutes"] == 195.0


def test_semi_urban_is_small_and_all_breach(analytical):
    su = analytical[analytical["area"] == "Semi-Urban"]
    assert len(su) == 152 and su["breach_flag"].all()


def test_pareto_is_deterministic_and_strictly_cumulative(analytical):
    p = segments.pareto(analytical, ("area", "traffic"))
    assert p["rank"].tolist() == list(range(1, len(p) + 1))
    assert (p["cumulative_share"].diff().dropna() > 0).all()  # no duplicated cumulative labels
    assert p["cumulative_share"].iloc[-1] == pytest.approx(1.0)
    assert p.loc[0, "segment"] == "Metropolitian / Jam" and p.loc[0, "breaches"] == 4877
    tie = p[p["breaches"] == 131]["segment"].tolist()  # Urban/High vs Urban/Low: broken by name
    assert tie == sorted(tie)
    assert p["cumulative_share"].iloc[3] == pytest.approx(0.8388, abs=1e-4)  # top four = 83.88%


def test_segment_table_shares_sum_to_one(analytical):
    t = segments.segment_table(analytical, "traffic")
    assert t["share_of_deliveries"].sum() == pytest.approx(1)
    assert t["share_of_breaches"].sum() == pytest.approx(1)
    assert (t["ci_low"] <= t["breach_rate"]).all() and (t["breach_rate"] <= t["ci_high"]).all()


def test_wilson_ci_known_value():
    lo, hi = fx.wilson_ci(50, 100)
    assert (lo, hi) == pytest.approx((0.4038, 0.5962), abs=1e-3)
    lo0, hi0 = fx.wilson_ci(0, 50)
    assert lo0 == pytest.approx(0.0, abs=1e-12) and 0 < hi0 < 0.1


def test_risk_and_odds_ratio_known_table():
    rr, lo, hi = fx.risk_ratio(30, 100, 10, 100)
    assert rr == pytest.approx(3.0) and lo < 3.0 < hi
    orr, _, _ = fx.odds_ratio(30, 100, 10, 100)
    assert orr == pytest.approx((30 / 70) / (10 / 90))
    rd, _, _ = fx.risk_difference(30, 100, 10, 100)
    assert rd == pytest.approx(0.2)


def test_cramers_v_extremes():
    perfect = np.array([[50, 0], [0, 50]])
    none = np.array([[25, 25], [25, 25]])
    assert fx.cramers_v(perfect)["cramers_v"] == pytest.approx(1.0)
    assert fx.cramers_v(none)["cramers_v"] == pytest.approx(0.0, abs=1e-9)


def test_mantel_haenszel_equals_crude_when_strata_identical():
    table = [[30, 70], [10, 90]]
    orr, lo, hi = fx.mantel_haenszel_or([table, table, table])
    assert orr == pytest.approx((30 * 90) / (70 * 10)) and lo < orr < hi
    rr, _, _ = fx.mantel_haenszel_rr([(30, 100, 10, 100)] * 3)
    assert rr == pytest.approx(3.0)


def test_cohens_d_and_probability_of_superiority():
    rng = np.random.default_rng(0)
    x, y = rng.normal(1, 1, 5000), rng.normal(0, 1, 5000)
    d, lo, hi = fx.cohens_d(x, y)
    assert d == pytest.approx(1.0, abs=0.06) and lo < d < hi
    assert fx.probability_of_superiority(x, y) == pytest.approx(0.76, abs=0.02)  # Phi(d / sqrt 2)
    assert fx.probability_of_superiority(y, y) == pytest.approx(0.5, abs=1e-9)
