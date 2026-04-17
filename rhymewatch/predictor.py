"""LightGBM predictor on log-returns.

Target: next-day log return (f["y_logret"]). NOT raw price. Random Forest
cannot extrapolate beyond values seen in training, so a price target regresses
to the mean; returns target does not have that bug.

Export trained model to ONNX via `hummingbird-ml` or `onnxmltools` for 3×
faster cold starts. Not bundled here to keep the Vercel image lean; the
project ships the `.pkl` by default and can drop to ONNX when needed.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Tuple
from datetime import datetime, timezone
import numpy as np
import pandas as pd

try:
    import lightgbm as lgb
    _HAS_LGBM = True
except ImportError:
    _HAS_LGBM = False

from . import validation


@dataclass
class PredictionReport:
    direction: str                    # "↑" | "↓" | "→"
    expected_return: float            # log return
    directional_accuracy: float       # walk-forward %
    sharpe_net_10bps: float
    mae: float
    n_predictions: int
    features: int
    model: str
    trained_at: str


def _fit_lgbm(X_train: np.ndarray, y_train: np.ndarray) -> "lgb.LGBMRegressor":
    if not _HAS_LGBM:
        raise RuntimeError("lightgbm not installed")
    model = lgb.LGBMRegressor(
        n_estimators=400,
        learning_rate=0.03,
        num_leaves=31,
        max_depth=-1,
        min_child_samples=20,
        subsample=0.85,
        subsample_freq=1,
        colsample_bytree=0.85,
        reg_alpha=0.05,
        reg_lambda=0.05,
        random_state=42,
        verbosity=-1,
        n_jobs=1,
    )
    model.fit(X_train, y_train)
    return model


def _fallback_fit_predict(X_train: np.ndarray, y_train: np.ndarray,
                          X_test: np.ndarray) -> np.ndarray:
    """Ridge-ish OLS fallback when lightgbm isn't available (e.g. in unit
    tests). Returns predictions for X_test."""
    X = np.hstack([np.ones((X_train.shape[0], 1)), X_train])
    Xt = np.hstack([np.ones((X_test.shape[0], 1)), X_test])
    ridge = 1e-3 * np.eye(X.shape[1])
    beta = np.linalg.solve(X.T @ X + ridge, X.T @ y_train)
    return Xt @ beta


def fit_predict(X_train: np.ndarray, y_train: np.ndarray,
                X_test: np.ndarray) -> np.ndarray:
    if _HAS_LGBM:
        m = _fit_lgbm(X_train, y_train)
        return m.predict(X_test)
    return _fallback_fit_predict(X_train, y_train, X_test)


def train_and_report(features: pd.DataFrame, target_col: str = "y_logret",
                     feature_cols: Optional[list] = None,
                     initial: int = 250, step: int = 21,
                     embargo: int = 5) -> Tuple["object", PredictionReport]:
    """Train a final model on all data AND compute walk-forward metrics.

    `initial` is set to 250 (1 trading year) so the toy per-ticker endpoint
    works; production cron should raise it to 1000+ for a proper five-year
    window.
    """
    if feature_cols is None:
        feature_cols = [c for c in features.columns if c != target_col]
    X = features[feature_cols].values.astype(np.float64)
    y = features[target_col].values.astype(np.float64)

    try:
        metrics = validation.cross_validate(
            X, y, fit_predict, initial=initial, step=step, embargo=embargo
        )
    except ValueError:
        metrics = {
            "mae": float("nan"),
            "directional_accuracy": float("nan"),
            "sharpe_net_10bps": float("nan"),
            "n_predictions": 0,
        }

    # Final model on everything.
    if _HAS_LGBM:
        model = _fit_lgbm(X, y)
        model_name = "lightgbm · returns target"
    else:
        X_aug = np.hstack([np.ones((X.shape[0], 1)), X])
        beta = np.linalg.solve(
            X_aug.T @ X_aug + 1e-3 * np.eye(X_aug.shape[1]), X_aug.T @ y
        )
        model = {"beta": beta, "feature_cols": feature_cols}
        model_name = "ridge-ols · returns target (lightgbm unavailable)"

    last = X[-1:]
    pred = _predict(model, last)[0] if len(last) else 0.0
    direction = "↑" if pred > 1e-4 else "↓" if pred < -1e-4 else "→"
    return model, PredictionReport(
        direction=direction,
        expected_return=float(pred),
        directional_accuracy=float(metrics["directional_accuracy"]),
        sharpe_net_10bps=float(metrics["sharpe_net_10bps"]),
        mae=float(metrics["mae"]),
        n_predictions=int(metrics["n_predictions"]),
        features=len(feature_cols),
        model=model_name,
        trained_at=datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
    )


def _predict(model, X: np.ndarray) -> np.ndarray:
    if _HAS_LGBM and hasattr(model, "predict"):
        return model.predict(X)
    X_aug = np.hstack([np.ones((X.shape[0], 1)), X])
    return X_aug @ model["beta"]


def predict(model, X: np.ndarray) -> np.ndarray:
    return _predict(model, X)
