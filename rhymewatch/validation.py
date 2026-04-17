"""Walk-forward cross-validation with embargo.

Replaces the textbook leakage pattern `train_test_split(shuffle=True)`, which
on time-series data inflates reported accuracy by 5–15pp vs. honest out-of-
sample evaluation.
"""
from __future__ import annotations
from typing import Iterator, Tuple, Callable, List
import numpy as np


def walk_forward(n: int, initial: int = 1000, step: int = 21,
                 embargo: int = 5) -> Iterator[Tuple[range, range]]:
    """Yield (train_idx, test_idx) pairs.

        initial   minimum training window before the first test fold
        step      test-fold length in trading days
        embargo   leave this many days unlearned between train and test to
                  prevent overlap-leakage when features span multiple days
    """
    if n < initial + step + embargo:
        raise ValueError(
            f"Not enough data: need at least {initial + step + embargo}, got {n}"
        )
    for t in range(initial, n - step, step):
        train_idx = range(0, max(0, t - embargo))
        test_idx = range(t, min(t + step, n))
        yield train_idx, test_idx


def directional_accuracy(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    if len(y_true) == 0:
        return float("nan")
    return float(np.mean(np.sign(y_true) == np.sign(y_pred)))


def mae(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return float(np.mean(np.abs(y_true - y_pred)))


def sharpe_net(y_true: np.ndarray, y_pred: np.ndarray,
               cost_bps: float = 10.0, trading_days: int = 252) -> float:
    """Signal-following Sharpe, net of a round-trip transaction cost.

        cost_bps   basis points per round-trip trade (default 10bps = 0.10%)
    """
    if len(y_true) == 0:
        return float("nan")
    position = np.sign(y_pred)
    # realized per-day return from the signal
    pnl = position * y_true
    # pay cost on position change
    turn = np.abs(np.diff(position, prepend=0))
    pnl = pnl - turn * (cost_bps / 1e4)
    sd = pnl.std()
    if sd == 0:
        return 0.0
    return float((pnl.mean() / sd) * np.sqrt(trading_days))


def cross_validate(X: np.ndarray, y: np.ndarray,
                   fit_predict: Callable[[np.ndarray, np.ndarray, np.ndarray], np.ndarray],
                   initial: int = 1000, step: int = 21, embargo: int = 5) -> dict:
    """Generic walk-forward driver. `fit_predict(X_train, y_train, X_test)`
    returns predictions for X_test. Returns aggregated metrics."""
    preds: List[float] = []
    trues: List[float] = []
    for tr, te in walk_forward(len(X), initial, step, embargo):
        if len(tr) == 0:
            continue
        p = fit_predict(X[list(tr)], y[list(tr)], X[list(te)])
        preds.extend(p.tolist())
        trues.extend(y[list(te)].tolist())
    preds_a = np.asarray(preds)
    trues_a = np.asarray(trues)
    return {
        "mae": mae(trues_a, preds_a),
        "directional_accuracy": directional_accuracy(trues_a, preds_a),
        "sharpe_net_10bps": sharpe_net(trues_a, preds_a, cost_bps=10.0),
        "n_predictions": len(preds_a),
    }
