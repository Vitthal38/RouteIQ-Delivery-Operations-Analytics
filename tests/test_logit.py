"""The transparent logistic regression must match scipy and recover known coefficients."""
import numpy as np
import pandas as pd
import pytest
from scipy.optimize import minimize
from scipy.special import expit

from routeiq.modeling.logit import SeparationError, auc, fit_logit, gvif


@pytest.fixture(scope="module")
def synth():
    rng = np.random.default_rng(1)
    n = 30_000
    X = pd.DataFrame({"const": 1.0, "x1": rng.normal(size=n), "x2": rng.integers(0, 2, n).astype(float),
                      "x3": rng.integers(0, 2, n).astype(float)})
    beta = np.array([-1.2, 0.8, -0.5, 0.6])
    y = (rng.random(n) < expit(X.to_numpy() @ beta)).astype(int)
    return X, y, beta


def test_recovers_known_coefficients(synth):
    X, y, beta = synth
    res = fit_logit(X, y)
    se = np.sqrt(np.diag(res.cov))
    assert (np.abs(res.beta - beta) / se < 3.5).all()


def test_matches_scipy_optimizer(synth):
    X, y, _ = synth
    res = fit_logit(X, y)
    Xv = X.to_numpy()
    nll = lambda b: -np.sum(y * (Xv @ b) - np.logaddexp(0, Xv @ b))
    ref = minimize(nll, np.zeros(4), method="BFGS", options={"gtol": 1e-9})
    assert np.allclose(res.beta, ref.x, atol=1e-5)
    assert res.loglik == pytest.approx(-ref.fun, abs=1e-4)


def test_perfect_separation_is_detected(synth):
    X, _, _ = synth
    with pytest.raises(SeparationError):
        fit_logit(X, X["x2"].astype(int).to_numpy())


def test_cluster_robust_close_to_model_based_for_iid_data(synth):
    X, y, _ = synth
    clusters = np.random.default_rng(2).integers(0, 40, len(y))
    res = fit_logit(X, y, cluster=clusters)
    ratio = np.sqrt(np.diag(res.cov_cluster)) / np.sqrt(np.diag(res.cov))
    assert ((ratio > 0.7) & (ratio < 1.4)).all()


def test_auc_and_gvif():
    y = np.array([0, 0, 1, 1])
    assert auc(y, np.array([0.1, 0.2, 0.8, 0.9])) == 1.0
    assert auc(y, np.array([0.9, 0.8, 0.2, 0.1])) == 0.0
    rng = np.random.default_rng(3)
    X = pd.DataFrame({"a": rng.normal(size=2000), "b": rng.normal(size=2000)})
    g = gvif(X, {"a": ["a"], "b": ["b"]})
    assert (g["gvif"] < 1.1).all()
