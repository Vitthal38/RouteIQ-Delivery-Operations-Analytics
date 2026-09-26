"""Driver analysis: a transparent logistic regression of SLA breach on operating conditions.

Purpose: understand ASSOCIATIONS with breach, on one consistent scale (odds ratios and
predicted-rate differences), instead of comparing incomparable statistics. This is
an explanatory baseline, not a prediction product and not a causal model.

Model set
    A  main effects: traffic, weather, area, vehicle, rating < 4.5, age >= 30, prep time (per 5 min)
    B  A + hour band     -> shows how much of "traffic" is time of day (collinearity)
    C  A + traffic x weather interactions (tested with a likelihood-ratio test)

Population: complete cases, excluding Semi-Urban (n=152, 100% breach -> complete
separation; reported descriptively) and the 54 rows with no rating.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

from routeiq.config import RANDOM_SEED
from routeiq.modeling.logit import (
    LogitResult, SeparationError, calibration_table, design_matrix, fit_logit, gvif,
    influence, performance, standardized_rates, youden_threshold,
)

REF = {"traffic": "Low", "weather": "Sunny", "area": "Metropolitian", "vehicle": "motorcycle",
       "hour_band": "5_17-18 early evening"}

SPECS: dict[str, dict] = {
    "A": {"categorical": {"traffic": REF["traffic"], "weather": REF["weather"], "area": REF["area"],
                          "vehicle": REF["vehicle"]},
          "numeric": ["rating_lt_4_5", "age_ge_30", "prep_per_5min"], "interactions": []},
    "B": {"categorical": {"traffic": REF["traffic"], "weather": REF["weather"], "area": REF["area"],
                          "vehicle": REF["vehicle"], "hour_band": REF["hour_band"]},
          "numeric": ["rating_lt_4_5", "age_ge_30", "prep_per_5min"], "interactions": []},
    "C": {"categorical": {"traffic": REF["traffic"], "weather": REF["weather"], "area": REF["area"],
                          "vehicle": REF["vehicle"]},
          "numeric": ["rating_lt_4_5", "age_ge_30", "prep_per_5min"], "interactions": [("traffic", "weather")]},
}


def prepare_model_frame(df: pd.DataFrame, outcome: str = "breach_flag") -> tuple[pd.DataFrame, dict]:
    """Complete-case modelling frame plus a record of every exclusion."""
    total = len(df)
    semi = int((df["area"] == "Semi-Urban").sum())
    no_rating = int(df["rating_lt_4_5"].isna().sum())
    frame = df[(df["area"] != "Semi-Urban") & df["rating_lt_4_5"].notna()].copy()
    frame["prep_per_5min"] = frame["prep_time_minutes"] / 5.0
    frame["y"] = frame[outcome].astype(int)
    info = {"n_total": total, "excluded_semi_urban": semi, "excluded_missing_rating": no_rating,
            "excluded_both": int(((df["area"] == "Semi-Urban") & df["rating_lt_4_5"].isna()).sum()),
            "n_model": len(frame), "n_events": int(frame["y"].sum()), "event_rate": float(frame["y"].mean())}
    return frame, info


def build_X(frame: pd.DataFrame, spec: dict) -> tuple[pd.DataFrame, dict[str, list[str]]]:
    return design_matrix(frame, spec["categorical"], spec["numeric"], spec["interactions"])


def fit_spec(frame: pd.DataFrame, spec: dict, cluster: bool = True) -> tuple[LogitResult, pd.DataFrame, dict]:
    X, groups = build_X(frame, spec)
    res = fit_logit(X, frame["y"].to_numpy(), cluster=frame["order_date"].to_numpy() if cluster else None)
    return res, X, groups


def holdout(frame: pd.DataFrame, spec: dict, seed: int = RANDOM_SEED, test_frac: float = 0.30) -> dict:
    """Stratified 70/30 split: fit on train, report on test (threshold chosen on train only)."""
    rng = np.random.default_rng(seed)
    idx_test = np.zeros(len(frame), bool)
    for _, pos in frame.groupby("y").indices.items():
        idx_test[rng.choice(pos, int(round(test_frac * len(pos))), replace=False)] = True
    train, test = frame[~idx_test], frame[idx_test]
    X_tr, _ = build_X(train, spec)
    res = fit_logit(X_tr, train["y"].to_numpy())
    X_te = build_X(test, spec)[0].reindex(columns=res.names, fill_value=0.0)
    p_tr, p_te = res.predict(X_tr), res.predict(X_te)
    t_star = youden_threshold(train["y"].to_numpy(), p_tr)
    out = {"n_train": len(train), "n_test": len(test),
           "test_at_0_5": performance(test["y"].to_numpy(), p_te, 0.5),
           "test_at_youden": performance(test["y"].to_numpy(), p_te, t_star),
           "train_auc": performance(train["y"].to_numpy(), p_tr, 0.5)["auc"]}
    return out


def lr_test(small: LogitResult, big: LogitResult) -> dict:
    stat = 2 * (big.loglik - small.loglik)
    dof = big.k - small.k
    return {"chi2": float(stat), "df": int(dof), "p_value": float(stats.chi2.sf(stat, dof)),
            "delta_aic": float(big.aic - small.aic), "delta_bic": float(big.bic - small.bic)}


def practical_summary(res: LogitResult, frame: pd.DataFrame, spec: dict) -> pd.DataFrame:
    """Predicted breach rate if everyone had each level (holding other terms as observed)."""
    levels = {c: sorted(frame[c].unique()) for c in spec["categorical"]}
    levels["rating_lt_4_5"] = [0, 1]
    levels["age_ge_30"] = [0, 1]
    levels["prep_per_5min"] = [1.0, 2.0, 3.0]
    builder = lambda f: build_X(f, spec)[0]
    return standardized_rates(res, frame, builder, levels)


def run_driver_models(df: pd.DataFrame, outcome: str = "breach_flag") -> dict:
    frame, info = prepare_model_frame(df, outcome)
    results: dict = {"info": info, "tables": {}, "fits": {}}
    fitted: dict[str, tuple[LogitResult, pd.DataFrame, dict]] = {}
    for name, spec in SPECS.items():
        fitted[name] = fit_spec(frame, spec)
    results["fits"] = fitted

    # --- coefficient tables: model-based and date-clustered intervals side by side
    for name, (res, X, groups) in fitted.items():
        t = res.table()
        tc = res.table(cluster=True)
        t["or_ci_low_clustered"] = tc["or_ci_low"]
        t["or_ci_high_clustered"] = tc["or_ci_high"]
        t["p_value_clustered"] = tc["p_value"]
        t.insert(0, "model", name)
        results["tables"][f"coef_{name}"] = t

    # --- model comparison
    rows, perf = [], {}
    for name, spec in SPECS.items():
        res = fitted[name][0]
        hp = holdout(frame, spec)
        perf[name] = hp
        rows.append({"model": name, "n": res.n, "events": res.n_events, "k_parameters": res.k,
                     "aic": res.aic, "bic": res.bic, "mcfadden_r2": res.mcfadden_r2,
                     "test_auc": hp["test_at_0_5"]["auc"], "test_brier": hp["test_at_0_5"]["brier"],
                     "test_log_loss": hp["test_at_0_5"]["log_loss"],
                     "test_accuracy_at_0_5": hp["test_at_0_5"]["accuracy"],
                     "test_sensitivity_at_youden": hp["test_at_youden"]["sensitivity"],
                     "test_specificity_at_youden": hp["test_at_youden"]["specificity"],
                     "majority_class_accuracy": hp["test_at_0_5"]["baseline_accuracy_majority"]})
    results["tables"]["model_comparison"] = pd.DataFrame(rows)
    results["holdout"] = perf
    results["lr_tests"] = {"A_vs_B_adds_hour_band": lr_test(fitted["A"][0], fitted["B"][0]),
                           "A_vs_C_adds_traffic_x_weather": lr_test(fitted["A"][0], fitted["C"][0])}

    # --- multicollinearity (generalised VIF) for A and B
    for name in ("A", "B"):
        res, X, groups = fitted[name]
        v = gvif(X, groups)
        v.insert(0, "model", name)
        results["tables"][f"gvif_{name}"] = v

    # --- influence (model A)
    res_a, X_a, groups_a = fitted["A"]
    inf = influence(res_a)
    cutoff = 4 / res_a.n
    top = inf["cooks_d"].nlargest(max(1, int(0.005 * res_a.n))).index
    keep = np.ones(res_a.n, bool)
    keep[top] = False
    refit = fit_logit(X_a[keep], frame["y"].to_numpy()[keep])
    or_full, or_drop = np.exp(res_a.beta), np.exp(refit.beta)
    results["influence"] = {
        "max_cooks_d": float(inf["cooks_d"].max()),
        "n_above_4_over_n": int((inf["cooks_d"] > cutoff).sum()),
        "max_leverage": float(inf["leverage"].max()),
        "mean_leverage": float(inf["leverage"].mean()),
        "refit_dropping_top_0_5pct_cooks": {
            "n_dropped": int((~keep).sum()),
            "max_abs_log_or_change": float(np.max(np.abs(np.log(or_drop) - np.log(or_full)))),
        },
    }

    # --- calibration, class balance, practical (standardised) effects, robustness
    p_a = res_a.predict(X_a)
    results["tables"]["calibration_A"] = calibration_table(frame["y"].to_numpy(), p_a)
    results["class_balance"] = {"events": info["n_events"], "non_events": info["n_model"] - info["n_events"],
                                "event_rate": info["event_rate"],
                                "note": "Event rate ~24%: no resampling needed; AUC/Brier/log-loss used instead of accuracy alone."}
    results["tables"]["standardized_rates_A"] = practical_summary(res_a, frame, SPECS["A"])
    res_b = fitted["B"][0]
    results["tables"]["standardized_rates_B"] = practical_summary(res_b, frame, SPECS["B"])

    frame_r = frame.copy()
    frame_r["is_grocery"] = (frame_r["category"] == "Grocery").astype(float)
    spec_r = {**SPECS["A"], "numeric": SPECS["A"]["numeric"] + ["is_grocery"]}
    res_r, _, _ = fit_spec(frame_r, spec_r, cluster=False)
    common = [n for n in res_a.names if n in res_r.names]
    change = {n: float(np.exp(res_r.beta[res_r.names.index(n)] - res_a.beta[res_a.names.index(n)])) for n in common}
    results["robustness_grocery_flag"] = {"odds_ratio_multiplier_vs_A": change,
                                             "max_abs_pct_change": float(100 * max(abs(v - 1) for v in change.values()))}

    # --- missingness / exclusions and rating-linearity sensitivity
    results["missingness"] = {**info}
    return results


def main_effect_summary(res: LogitResult) -> dict[str, dict[str, float]]:
    """Odds ratio + CI per term, for quoting in docs."""
    t = res.table()
    return {r.term: {"odds_ratio": r.odds_ratio, "ci_low": r.or_ci_low, "ci_high": r.or_ci_high}
            for r in t.itertuples()}
