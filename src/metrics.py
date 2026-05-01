from __future__ import annotations

import numpy as np
import pandas as pd


def dispatch_proxy_score(df: pd.DataFrame) -> np.ndarray:
    a = 0.55 * df["ramp_max"].to_numpy()
    b = 0.25 * df["smoothness"].to_numpy()
    c = 0.20 * (1 - df["mean_power"].to_numpy())
    return a + b + c


def feeder_dispatch_cost(df: pd.DataFrame, feeder_scale: float = 1.0) -> np.ndarray:
    reserve = 18.0 * df["ramp_max"].to_numpy()
    fluctuation = 11.0 * df["smoothness"].to_numpy()
    deficit = 42.0 * np.maximum(0.0, 1 - df["mean_power"].to_numpy())
    losses = 9.0 * feeder_scale * (df["peak_power"].to_numpy() ** 2)
    variability = 6.0 * feeder_scale * (df["std_power"].to_numpy())
    return reserve + fluctuation + deficit + losses + variability


def evaluate_by_representatives(
    all_df: pd.DataFrame, rep_df: pd.DataFrame, feature_cols: list[str], extreme_quantile: float = 0.9
) -> dict[str, float]:
    x_all = all_df[feature_cols].to_numpy()
    x_rep = rep_df[feature_cols].to_numpy()
    dist = np.linalg.norm(x_all[:, None, :] - x_rep[None, :, :], axis=2)
    min_dist = dist.min(axis=1)
    dispatch_error = float(np.mean(min_dist))
    coverage = float(np.mean(min_dist <= np.quantile(min_dist, 0.7)))
    risk = all_df["risk_score"].to_numpy()
    threshold = float(np.quantile(risk, extreme_quantile))
    extreme_mask = risk >= threshold
    extreme_miss = float(np.mean(min_dist[extreme_mask] > np.quantile(min_dist, 0.7)))
    return {
        "dispatch_error": dispatch_error,
        "coverage": coverage,
        "extreme_miss": extreme_miss,
    }


def evaluate_dispatch_cost(
    all_df: pd.DataFrame, rep_df: pd.DataFrame, feature_cols: list[str], feeder_scale: float = 1.0
) -> dict[str, float]:
    x_all = all_df[feature_cols].to_numpy()
    x_rep = rep_df[feature_cols].to_numpy()
    dist = np.linalg.norm(x_all[:, None, :] - x_rep[None, :, :], axis=2)
    assign = dist.argmin(axis=1)
    actual = feeder_dispatch_cost(all_df, feeder_scale=feeder_scale)
    rep_cost = feeder_dispatch_cost(rep_df, feeder_scale=feeder_scale)
    assigned = rep_cost[assign]
    gap = float(np.mean(np.abs(actual - assigned)))
    rel_gap = float(gap / (np.mean(actual) + 1e-9))
    return {
        "dispatch_cost_gap": gap,
        "dispatch_cost_gap_ratio": rel_gap,
        "full_dispatch_cost": float(np.mean(actual)),
        "reduced_dispatch_cost": float(np.mean(assigned)),
    }
