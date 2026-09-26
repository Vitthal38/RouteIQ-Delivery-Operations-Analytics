"""A small, transparent logistic regression (IRLS) with diagnostics.

statsmodels/scikit-learn are deliberately not dependencies: for a binary
outcome with ~40 columns, Newton/IRLS is ~30 lines and every number can be
audited. ``tests/test_logit.py`` checks it against ``scipy.optimize`` and against
synthetic data with known coefficients.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from scipy import stats
from scipy.special import expit

Z95 = 1.959963984540054


class SeparationError(RuntimeError):
    """Raised when the likelihood has no finite maximum (perfect/quasi separation)."""


# --------------------------------------------------------------------------
# Design matrix
# --------------------------------------------------------------------------
def design_matrix(
    df: pd.DataFrame,
    categorical: dict[str, str] | None = None,
    numeric: list[str] | None = None,
    interactions: list[tuple[str, str]] | None = None,
) -> tuple[pd.DataFrame, dict[str, list[str]]]:
    """One-hot encode with explicit reference levels; returns (X, term->columns).

    ``categorical`` maps column -> reference level. ``numeric`` columns (including
    0/1 flags) enter as-is. ``interactions`` are pairs of terms whose columns are
    multiplied pairwise. An intercept column 'const' is always first.
    """
    categorical = categorical or {}
    numeric = numeric or []
    cols: dict[str, pd.Series] = {"const": pd.Series(1.0, index=df.index)}
    groups: dict[str, list[str]] = {}
    for col, ref in categorical.items():
        levels = sorted(v for v in df[col].dropna().unique() if v != ref)
        names = []
        for lv in levels:
            name = f"{col}[{lv}]"
            cols[name] = (df[col] == lv).astype(float)
            names.append(name)
        groups[col] = names
    for col in numeric:
        cols[col] = df[col].astype(float)
        groups[col] = [col]
    for a, b in interactions or []:
        names = []
        for ca in groups[a]:
            for cb in groups[b]:
                name = f"{ca}:{cb}"
                cols[name] = cols[ca] * cols[cb]
                names.append(name)
        groups[f"{a}:{b}"] = names
    return pd.DataFrame(cols, index=df.index), groups


# --------------------------------------------------------------------------
# Fit
# --------------------------------------------------------------------------
@dataclass
class LogitResult:
    names: list[str]
    beta: np.ndarray
    cov: np.ndarray                      # model-based covariance (inverse Fisher information)
    cov_cluster: np.ndarray | None       # cluster-robust (CR1) covariance, if clusters given
    loglik: float
    null_loglik: float
    n: int
    n_events: int
    iterations: int
    _X: np.ndarray = field(repr=False, default=None)
    _y: np.ndarray = field(repr=False, default=None)

    @property
    def k(self) -> int:
        return len(self.beta)

    @property
    def aic(self) -> float:
        return -2 * self.loglik + 2 * self.k

    @property
    def bic(self) -> float:
        return -2 * self.loglik + np.log(self.n) * self.k

    @property
    def mcfadden_r2(self) -> float:
        return 1 - self.loglik / self.null_loglik

    def predict(self, X: pd.DataFrame | np.ndarray) -> np.ndarray:
        Xv = X[self.names].to_numpy(float) if isinstance(X, pd.DataFrame) else np.asarray(X, float)
        return expit(Xv @ self.beta)

    def table(self, cluster: bool = False) -> pd.DataFrame:
        """Coefficients, odds ratios with 95% CI and p-values (model-based or clustered)."""
        cov = self.cov_cluster if (cluster and self.cov_cluster is not None) else self.cov
        se = np.sqrt(np.diag(cov))
        z = self.beta / se
        out = pd.DataFrame({
            "term": self.names,
            "coef": self.beta,
            "std_err": se,
            "odds_ratio": np.exp(self.beta),
            "or_ci_low": np.exp(self.beta - Z95 * se),
            "or_ci_high": np.exp(self.beta + Z95 * se),
            "z": z,
            "p_value": 2 * stats.norm.sf(np.abs(z)),
        })
        return out


def _loglik(y: np.ndarray, eta: np.ndarray) -> float:
    # Stable Bernoulli log-likelihood: y*eta - log(1 + exp(eta))
    return float(np.sum(y * eta - np.logaddexp(0.0, eta)))


def fit_logit(X: pd.DataFrame, y: np.ndarray | pd.Series, cluster: np.ndarray | pd.Series | None = None,
              max_iter: int = 60, tol: float = 1e-10) -> LogitResult:
    """Maximum-likelihood logistic regression via Newton-Raphson (IRLS) with step halving."""
    names = list(X.columns)
    Xv = X.to_numpy(float)
    yv = np.asarray(y, float)
    n, k = Xv.shape
    beta = np.zeros(k)
    if "const" in names:  # start from the intercept-only solution
        p0 = yv.mean()
        beta[names.index("const")] = np.log(p0 / (1 - p0))
    eta = Xv @ beta
    ll = _loglik(yv, eta)
    converged = False
    it = 0
    for it in range(1, max_iter + 1):
        p = expit(eta)
        w = np.clip(p * (1 - p), 1e-12, None)
        grad = Xv.T @ (yv - p)
        info = (Xv * w[:, None]).T @ Xv
        step = np.linalg.solve(info, grad)
        t = 1.0
        while True:  # step halving guarantees the likelihood does not decrease
            new_beta = beta + t * step
            new_eta = Xv @ new_beta
            new_ll = _loglik(yv, new_eta)
            if new_ll >= ll - 1e-12 or t < 1e-8:
                break
            t /= 2
        delta = abs(new_ll - ll)
        beta, eta, ll = new_beta, new_eta, new_ll
        if delta < tol and np.max(np.abs(t * step)) < 1e-7:
            converged = True
            break
    if not converged or np.max(np.abs(beta)) > 25:
        raise SeparationError("Logistic fit did not converge to finite coefficients "
                              "(check for perfect/quasi separation).")
    p = expit(eta)
    w = np.clip(p * (1 - p), 1e-12, None)
    info = (Xv * w[:, None]).T @ Xv
    a_inv = np.linalg.inv(info)
    cov_c = None
    if cluster is not None:
        g = pd.factorize(np.asarray(cluster))[0]
        n_groups = g.max() + 1
        scores = Xv * (yv - p)[:, None]
        meat = np.zeros((k, k))
        for gi in range(n_groups):
            s = scores[g == gi].sum(axis=0)
            meat += np.outer(s, s)
        adj = (n_groups / (n_groups - 1)) * ((n - 1) / (n - k))
        cov_c = adj * a_inv @ meat @ a_inv
    p_bar = yv.mean()
    null_ll = float(yv.sum() * np.log(p_bar) + (n - yv.sum()) * np.log(1 - p_bar))
    return LogitResult(names, beta, a_inv, cov_c, ll, null_ll, n, int(yv.sum()), it, Xv, yv)


# --------------------------------------------------------------------------
# Diagnostics
# --------------------------------------------------------------------------
def influence(res: LogitResult) -> pd.DataFrame:
    """Leverage (hat values), Pearson residuals and Cook's distance per observation."""
    Xv, yv = res._X, res._y
    p = expit(Xv @ res.beta)
    w = np.clip(p * (1 - p), 1e-12, None)
    a_inv = res.cov
    h = w * np.einsum("ij,jk,ik->i", Xv, a_inv, Xv)
    r = (yv - p) / np.sqrt(w)
    cooks = (r ** 2) * h / (res.k * (1 - h) ** 2)
    return pd.DataFrame({"leverage": h, "pearson_resid": r, "cooks_d": cooks})


def gvif(X: pd.DataFrame, groups: dict[str, list[str]]) -> pd.DataFrame:
    """Generalised VIF (Fox & Monette) per model term; GVIF^(1/(2*df)) is comparable across terms.

    Interaction terms are excluded (their VIF is inflated by construction).
    """
    terms = {t: c for t, c in groups.items() if ":" not in t}
    cols = [c for cs in terms.values() for c in cs]
    corr = np.corrcoef(X[cols].to_numpy(float), rowvar=False)
    idx = {c: i for i, c in enumerate(cols)}
    _, logdet_all = np.linalg.slogdet(corr)
    rows = []
    for term, cs in terms.items():
        ii = [idx[c] for c in cs]
        rest = [i for i in range(len(cols)) if i not in ii]
        _, ld_g = np.linalg.slogdet(corr[np.ix_(ii, ii)])
        _, ld_r = np.linalg.slogdet(corr[np.ix_(rest, rest)]) if rest else (1, 0.0)
        g = float(np.exp(ld_g + ld_r - logdet_all))
        rows.append({"term": term, "df": len(cs), "gvif": g, "gvif_adj": g ** (1 / (2 * len(cs)))})
    return pd.DataFrame(rows)


def auc(y: np.ndarray, score: np.ndarray) -> float:
    y = np.asarray(y)
    ranks = stats.rankdata(score)
    n1 = y.sum()
    n0 = len(y) - n1
    return float((ranks[y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


def performance(y: np.ndarray, p: np.ndarray, threshold: float = 0.5) -> dict[str, float]:
    y = np.asarray(y)
    pred = (p >= threshold).astype(int)
    tp = int(((pred == 1) & (y == 1)).sum())
    tn = int(((pred == 0) & (y == 0)).sum())
    fp = int(((pred == 1) & (y == 0)).sum())
    fn = int(((pred == 0) & (y == 1)).sum())
    eps = 1e-12
    return {
        "auc": auc(y, p),
        "brier": float(np.mean((p - y) ** 2)),
        "log_loss": float(-np.mean(y * np.log(p + eps) + (1 - y) * np.log(1 - p + eps))),
        "threshold": threshold,
        "accuracy": (tp + tn) / len(y),
        "sensitivity": tp / (tp + fn) if (tp + fn) else float("nan"),
        "specificity": tn / (tn + fp) if (tn + fp) else float("nan"),
        "precision": tp / (tp + fp) if (tp + fp) else float("nan"),
        "baseline_accuracy_majority": float(max(y.mean(), 1 - y.mean())),
    }


def youden_threshold(y: np.ndarray, p: np.ndarray) -> float:
    """Threshold maximising sensitivity + specificity - 1 (choose on training data only)."""
    qs = np.unique(np.quantile(p, np.linspace(0.01, 0.99, 99)))
    best, best_t = -1.0, 0.5
    y = np.asarray(y)
    for t in qs:
        pred = p >= t
        sens = (pred & (y == 1)).sum() / max((y == 1).sum(), 1)
        spec = ((~pred) & (y == 0)).sum() / max((y == 0).sum(), 1)
        if sens + spec - 1 > best:
            best, best_t = sens + spec - 1, float(t)
    return best_t


def calibration_table(y: np.ndarray, p: np.ndarray, bins: int = 10) -> pd.DataFrame:
    df = pd.DataFrame({"y": np.asarray(y), "p": np.asarray(p)})
    df["decile"] = pd.qcut(df["p"].rank(method="first"), bins, labels=False) + 1
    return (df.groupby("decile").agg(n=("y", "size"), mean_predicted=("p", "mean"), observed_rate=("y", "mean"))
            .reset_index())


def standardized_rates(res: LogitResult, X_base: pd.DataFrame, builder, term_levels: dict[str, list],
                       n_sim: int = 500, seed: int = 42) -> pd.DataFrame:
    """Predictive margins: average predicted breach rate if EVERY row had a given level.

    ``builder(df_modified)`` must return the design matrix for a modified copy of the
    source frame; ``X_base`` here is that source frame. Intervals are parametric
    (draws from N(beta, cov)); they reflect coefficient uncertainty only.
    """
    rng = np.random.default_rng(seed)
    draws = rng.multivariate_normal(res.beta, res.cov, size=n_sim)
    rows = []
    for col, levels in term_levels.items():
        for lv in levels:
            mod = X_base.copy()
            mod[col] = lv
            Xm = builder(mod).reindex(columns=res.names, fill_value=0.0).to_numpy(float)
            point = float(expit(Xm @ res.beta).mean())
            sims = expit(Xm @ draws.T).mean(axis=0)
            rows.append({"variable": col, "level": lv, "standardized_rate": point,
                         "ci_low": float(np.quantile(sims, 0.025)), "ci_high": float(np.quantile(sims, 0.975))})
    return pd.DataFrame(rows)
