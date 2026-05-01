from __future__ import annotations

import numpy as np
import pandas as pd


POWER_COLS = ["node_22_wind", "node_25_wind", "node_18_PV", "node_33_PV"]
RISK_BASIS_COLS = ["ramp_max", "smoothness", "low_output_rate", "power_deficit"]


def smoothness(x: np.ndarray) -> float:
    d = np.diff(x)
    return float(np.mean(np.abs(d)))


def ramp_rate(x: np.ndarray) -> float:
    d = np.diff(x)
    return float(np.max(np.abs(d)))


def complementarity(wind: np.ndarray, pv: np.ndarray) -> float:
    if np.std(wind) < 1e-9 or np.std(pv) < 1e-9:
        return 0.0
    return float(-np.corrcoef(wind, pv)[0, 1])


def scenario_feature_row(df: pd.DataFrame) -> dict[str, float]:
    arr = df[POWER_COLS].to_numpy()
    wind = arr[:, :2].mean(axis=1)
    pv = arr[:, 2:].mean(axis=1)
    all_mix = arr.mean(axis=1)
    row: dict[str, float] = {}
    row["mean_power"] = float(np.mean(all_mix))
    row["std_power"] = float(np.std(all_mix))
    row["peak_power"] = float(np.max(all_mix))
    row["ramp_max"] = ramp_rate(all_mix)
    row["smoothness"] = smoothness(all_mix)
    row["complementarity"] = complementarity(wind, pv)
    row["wind_mean"] = float(np.mean(wind))
    row["pv_mean"] = float(np.mean(pv))
    row["wind_peak"] = float(np.max(wind))
    row["pv_peak"] = float(np.max(pv))
    row["wind_std"] = float(np.std(wind))
    row["pv_std"] = float(np.std(pv))
    row["low_output_rate"] = float(np.mean(all_mix < 0.1))
    row["power_deficit"] = float(max(0.0, 1 - np.mean(all_mix)))
    return row


def risk_score(df: pd.DataFrame) -> float:
    arr = df[POWER_COLS].to_numpy().mean(axis=1)
    ramp = ramp_rate(arr)
    smooth = smoothness(arr)
    low_output = float(np.mean(arr < 0.1))
    return float(0.45 * ramp + 0.35 * smooth + 0.20 * low_output)


def learn_risk_weights(features_df: pd.DataFrame) -> np.ndarray:
    x = features_df[RISK_BASIS_COLS].to_numpy(dtype=float)
    x = x / np.maximum(x.std(axis=0, keepdims=True), 1e-6)
    y = (
        0.55 * features_df["ramp_max"].to_numpy(dtype=float)
        + 0.25 * features_df["smoothness"].to_numpy(dtype=float)
        + 0.20 * features_df["power_deficit"].to_numpy(dtype=float)
    )
    coef, *_ = np.linalg.lstsq(x, y, rcond=None)
    coef = np.clip(coef, 0.0, None)
    if float(coef.sum()) <= 1e-9:
        coef = np.array([0.4, 0.25, 0.2, 0.15], dtype=float)
    coef = coef / coef.sum()
    return coef


def apply_learned_risk_score(features_df: pd.DataFrame, weights: np.ndarray, gamma: float = 0.35) -> pd.DataFrame:
    df = features_df.copy()
    basis = df[RISK_BASIS_COLS].to_numpy(dtype=float)
    basis = basis / np.maximum(basis.std(axis=0, keepdims=True), 1e-6)
    base = basis @ weights.reshape(-1, 1)
    base = base.reshape(-1)
    ref = float(df["mean_power"].mean())
    drift = 1.0 + gamma * np.abs(df["mean_power"].to_numpy(dtype=float) - ref) / max(abs(ref), 1e-6)
    df["risk_score"] = base * drift
    return df
