"""Effect sizes and confidence intervals.

At n ~ 43,000 nearly every difference is "statistically significant", so this
project judges findings by effect size and interval width, not p-values. All
functions here are small, dependency-light (numpy/scipy) and unit tested.
"""

from __future__ import annotations

import math
from typing import Callable, Sequence

import numpy as np
import pandas as pd
from scipy import stats

Z95 = 1.959963984540054


# --------------------------------------------------------------------------
# Proportions
# --------------------------------------------------------------------------
def wilson_ci(k: float, n: float, z: float = Z95) -> tuple[float, float]:
    """Wilson score interval for a binomial proportion (well behaved near 0 and 1)."""
    if n <= 0:
        return (math.nan, math.nan)
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return (max(0.0, centre - half), min(1.0, centre + half))


def risk_difference(k1: float, n1: float, k0: float, n0: float) -> tuple[float, float, float]:
    """Risk difference p1 - p0 with a Wald 95% CI (in proportion units)."""
    p1, p0 = k1 / n1, k0 / n0
    se = math.sqrt(p1 * (1 - p1) / n1 + p0 * (1 - p0) / n0)
    d = p1 - p0
    return d, d - Z95 * se, d + Z95 * se


def risk_ratio(k1: float, n1: float, k0: float, n0: float) -> tuple[float, float, float]:
    """Risk ratio p1/p0 with a log-method 95% CI. NaN when either event count is 0."""
    if k1 == 0 or k0 == 0:
        return (math.nan, math.nan, math.nan)
    rr = (k1 / n1) / (k0 / n0)
    se = math.sqrt(1 / k1 - 1 / n1 + 1 / k0 - 1 / n0)
    return rr, rr * math.exp(-Z95 * se), rr * math.exp(Z95 * se)


def odds_ratio(k1: float, n1: float, k0: float, n0: float) -> tuple[float, float, float]:
    """Odds ratio (group 1 vs group 0) with a Woolf 95% CI."""
    a, b, c, d = k1, n1 - k1, k0, n0 - k0
    if min(a, b, c, d) == 0:
        return (math.nan, math.nan, math.nan)
    orr = (a * d) / (b * c)
    se = math.sqrt(1 / a + 1 / b + 1 / c + 1 / d)
    return orr, orr * math.exp(-Z95 * se), orr * math.exp(Z95 * se)


# --------------------------------------------------------------------------
# Association between categorical variables
# --------------------------------------------------------------------------
def cramers_v(table: pd.DataFrame | np.ndarray) -> dict[str, float]:
    """Cramer's V from a contingency table, with chi-square, dof and p-value.

    Also returns the bias-corrected V (Bergsma 2013), which is the safer number
    for tables with small cells.
    """
    obs = np.asarray(table, dtype=float)
    chi2, p, dof, _ = stats.chi2_contingency(obs, correction=False)
    n = obs.sum()
    r, c = obs.shape
    k = min(r - 1, c - 1)
    v = math.sqrt(chi2 / (n * k)) if k > 0 else math.nan
    phi2 = chi2 / n
    phi2c = max(0.0, phi2 - (r - 1) * (c - 1) / (n - 1))
    rc = r - (r - 1) ** 2 / (n - 1)
    cc = c - (c - 1) ** 2 / (n - 1)
    kc = min(rc - 1, cc - 1)
    vc = math.sqrt(phi2c / kc) if kc > 0 else math.nan
    return {"chi2": float(chi2), "dof": int(dof), "p_value": float(p), "cramers_v": v,
            "cramers_v_bias_corrected": vc, "n": int(n)}


def mantel_haenszel_or(tables: Sequence[Sequence[Sequence[float]]]) -> tuple[float, float, float]:
    """Common odds ratio across strata with the Robins-Breslow-Greenland 95% CI.

    Each table is [[a, b], [c, d]] = [[exposed events, exposed non-events],
    [unexposed events, unexposed non-events]]. Strata with an empty margin are skipped.
    """
    R = S = 0.0
    sPR = sPS_QR = sQS = 0.0
    for (a, b), (c, d) in tables:
        n = a + b + c + d
        if n == 0 or (a + b) == 0 or (c + d) == 0:
            continue
        r_i, s_i = a * d / n, b * c / n
        P, Q = (a + d) / n, (b + c) / n
        R += r_i
        S += s_i
        sPR += P * r_i
        sPS_QR += P * s_i + Q * r_i
        sQS += Q * s_i
    if R == 0 or S == 0:
        return (math.nan, math.nan, math.nan)
    orr = R / S
    var = sPR / (2 * R * R) + sPS_QR / (2 * R * S) + sQS / (2 * S * S)
    se = math.sqrt(var)
    return orr, orr * math.exp(-Z95 * se), orr * math.exp(Z95 * se)


def mantel_haenszel_rr(strata: Sequence[tuple[float, float, float, float]]) -> tuple[float, float, float]:
    """Common risk ratio across strata (Greenland-Robins), 95% CI.

    Each stratum is (events_exposed, n_exposed, events_unexposed, n_unexposed).
    """
    num = den = 0.0
    var_num = 0.0
    for a, n1, c, n0 in strata:
        n = n1 + n0
        if n == 0 or n1 == 0 or n0 == 0:
            continue
        num += a * n0 / n
        den += c * n1 / n
        var_num += (n1 * n0 * (a + c) - a * c * n) / (n * n)
    if num == 0 or den == 0:
        return (math.nan, math.nan, math.nan)
    rr = num / den
    se = math.sqrt(var_num / (num * den))
    return rr, rr * math.exp(-Z95 * se), rr * math.exp(Z95 * se)


# --------------------------------------------------------------------------
# Continuous outcomes
# --------------------------------------------------------------------------
def cohens_d(x: np.ndarray, y: np.ndarray) -> tuple[float, float, float]:
    """Cohen's d (pooled SD) for x minus y with an approximate 95% CI."""
    x, y = np.asarray(x, float), np.asarray(y, float)
    n1, n2 = len(x), len(y)
    sp = math.sqrt(((n1 - 1) * x.var(ddof=1) + (n2 - 1) * y.var(ddof=1)) / (n1 + n2 - 2))
    d = (x.mean() - y.mean()) / sp
    se = math.sqrt((n1 + n2) / (n1 * n2) + d * d / (2 * (n1 + n2)))
    return d, d - Z95 * se, d + Z95 * se


def probability_of_superiority(x: np.ndarray, y: np.ndarray) -> float:
    """Probability of superiority (common-language effect size): P(random x > random y), ties count
    half. A standard, model-free effect size for a two-group rank comparison - the same quantity
    the Mann-Whitney U statistic is built from (U / (n_x * n_y))."""
    x, y = np.asarray(x, float), np.asarray(y, float)
    ranks = stats.rankdata(np.concatenate([x, y]))
    u = ranks[: len(x)].sum() - len(x) * (len(x) + 1) / 2
    return float(u / (len(x) * len(y)))


def kruskal_epsilon_squared(groups: Sequence[np.ndarray]) -> tuple[float, float, float]:
    """Kruskal-Wallis H, p-value and epsilon-squared = (H - k + 1) / (n - k)."""
    h, p = stats.kruskal(*groups)
    n = sum(len(g) for g in groups)
    k = len(groups)
    return float(h), float(p), float((h - k + 1) / (n - k))


def bootstrap_ci(stat: Callable[..., float], *arrays: np.ndarray, n_boot: int = 2000,
                 seed: int = 42, alpha: float = 0.05) -> tuple[float, float, float]:
    """Percentile bootstrap CI for ``stat(*arrays)``; arrays are resampled independently."""
    rng = np.random.default_rng(seed)
    arrays = tuple(np.asarray(a) for a in arrays)
    point = float(stat(*arrays))
    draws = np.empty(n_boot)
    for i in range(n_boot):
        draws[i] = stat(*[a[rng.integers(0, len(a), len(a))] for a in arrays])
    lo, hi = np.quantile(draws, [alpha / 2, 1 - alpha / 2])
    return point, float(lo), float(hi)


def classify_cramers_v(v: float, df_star: int = 1) -> str:
    """Cohen (1988) bands scaled by min(r-1, c-1): small 0.10, medium 0.30, large 0.50 for df*=1."""
    s = 1 / math.sqrt(df_star)
    if v < 0.1 * s:
        return "negligible"
    if v < 0.3 * s:
        return "small"
    if v < 0.5 * s:
        return "medium"
    return "large"
