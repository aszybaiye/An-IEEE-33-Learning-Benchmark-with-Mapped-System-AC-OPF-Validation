from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd


# Standard Baran-Wu IEEE-33 radial feeder base loads in MW / MVAr.
BUS_LOADS = {
    1: (0.0, 0.0),
    2: (0.100, 0.060),
    3: (0.090, 0.040),
    4: (0.120, 0.080),
    5: (0.060, 0.030),
    6: (0.060, 0.020),
    7: (0.200, 0.100),
    8: (0.200, 0.100),
    9: (0.060, 0.020),
    10: (0.060, 0.020),
    11: (0.045, 0.030),
    12: (0.060, 0.035),
    13: (0.060, 0.035),
    14: (0.120, 0.080),
    15: (0.060, 0.010),
    16: (0.060, 0.020),
    17: (0.060, 0.020),
    18: (0.090, 0.040),
    19: (0.090, 0.040),
    20: (0.090, 0.040),
    21: (0.090, 0.040),
    22: (0.090, 0.040),
    23: (0.090, 0.050),
    24: (0.420, 0.200),
    25: (0.420, 0.200),
    26: (0.060, 0.025),
    27: (0.060, 0.025),
    28: (0.060, 0.020),
    29: (0.120, 0.070),
    30: (0.200, 0.600),
    31: (0.150, 0.070),
    32: (0.210, 0.100),
    33: (0.060, 0.040),
}


# Standard Baran-Wu branch parameters in Ohm.
BRANCH_DATA = [
    (1, 2, 0.0922, 0.0470),
    (2, 3, 0.4930, 0.2511),
    (3, 4, 0.3660, 0.1864),
    (4, 5, 0.3811, 0.1941),
    (5, 6, 0.8190, 0.7070),
    (6, 7, 0.1872, 0.6188),
    (7, 8, 1.7114, 1.2351),
    (8, 9, 1.0300, 0.7400),
    (9, 10, 1.0440, 0.7400),
    (10, 11, 0.1966, 0.0650),
    (11, 12, 0.3744, 0.1238),
    (12, 13, 1.4680, 1.1550),
    (13, 14, 0.5416, 0.7129),
    (14, 15, 0.5910, 0.5260),
    (15, 16, 0.7463, 0.5450),
    (16, 17, 1.2890, 1.7210),
    (17, 18, 0.7320, 0.5740),
    (2, 19, 0.1640, 0.1565),
    (19, 20, 1.5042, 1.3554),
    (20, 21, 0.4095, 0.4784),
    (21, 22, 0.7089, 0.9373),
    (3, 23, 0.4512, 0.3083),
    (23, 24, 0.8980, 0.7091),
    (24, 25, 0.8960, 0.7011),
    (6, 26, 0.2030, 0.1034),
    (26, 27, 0.2842, 0.1447),
    (27, 28, 1.0590, 0.9337),
    (28, 29, 0.8042, 0.7006),
    (29, 30, 0.5075, 0.2585),
    (30, 31, 0.9744, 0.9630),
    (31, 32, 0.3105, 0.3619),
    (32, 33, 0.3410, 0.5302),
]


RENEWABLE_BUS_MAP = {
    "node_18_PV": 18,
    "node_22_wind": 22,
    "node_25_wind": 25,
    "node_33_PV": 33,
}


@dataclass
class DDRE33Feeder:
    n_bus: int
    parent: np.ndarray
    child_branch_index: list[list[int]]
    branches_from: np.ndarray
    branches_to: np.ndarray
    r_pu: np.ndarray
    x_pu: np.ndarray
    base_pd_mw: np.ndarray
    base_qd_mvar: np.ndarray
    branch_limit_mva: np.ndarray
    load_shape: np.ndarray
    s_base_mva: float = 100.0
    v_min_pu: float = 0.95
    v_max_pu: float = 1.05


def make_daily_load_shape(n_steps: int = 96) -> np.ndarray:
    t = np.arange(n_steps, dtype=float)
    morning = 0.12 * np.exp(-0.5 * ((t - 30.0) / 9.0) ** 2)
    evening = 0.24 * np.exp(-0.5 * ((t - 75.0) / 11.0) ** 2)
    midday = 0.08 * np.exp(-0.5 * ((t - 52.0) / 12.0) ** 2)
    circadian = 0.06 * np.cos((t - 70.0) * 2.0 * np.pi / n_steps)
    shape = 0.74 + morning + evening + midday + circadian
    return np.clip(shape, 0.62, 1.12)


def build_feeder() -> DDRE33Feeder:
    n_bus = 33
    s_base_mva = 100.0
    v_base_kv = 12.66
    z_base = (v_base_kv**2) / s_base_mva

    parent = np.full(n_bus, -1, dtype=int)
    child_branch_index: list[list[int]] = [[] for _ in range(n_bus)]
    branches_from = np.zeros(len(BRANCH_DATA), dtype=int)
    branches_to = np.zeros(len(BRANCH_DATA), dtype=int)
    r_pu = np.zeros(len(BRANCH_DATA), dtype=float)
    x_pu = np.zeros(len(BRANCH_DATA), dtype=float)

    for idx, (f_bus, t_bus, r_ohm, x_ohm) in enumerate(BRANCH_DATA):
        f_idx = f_bus - 1
        t_idx = t_bus - 1
        branches_from[idx] = f_idx
        branches_to[idx] = t_idx
        r_pu[idx] = r_ohm / z_base
        x_pu[idx] = x_ohm / z_base
        parent[t_idx] = f_idx
        child_branch_index[f_idx].append(idx)

    base_pd_mw = np.array([BUS_LOADS[i + 1][0] for i in range(n_bus)], dtype=float)
    base_qd_mvar = np.array([BUS_LOADS[i + 1][1] for i in range(n_bus)], dtype=float)
    load_shape = make_daily_load_shape()

    feeder = DDRE33Feeder(
        n_bus=n_bus,
        parent=parent,
        child_branch_index=child_branch_index,
        branches_from=branches_from,
        branches_to=branches_to,
        r_pu=r_pu,
        x_pu=x_pu,
        base_pd_mw=base_pd_mw,
        base_qd_mvar=base_qd_mvar,
        branch_limit_mva=np.ones(len(BRANCH_DATA), dtype=float),
        load_shape=load_shape,
        s_base_mva=s_base_mva,
    )
    feeder.branch_limit_mva = compute_branch_limits(feeder)
    return feeder


def backward_forward_sweep(
    feeder: DDRE33Feeder, p_net_pu: np.ndarray, q_net_pu: np.ndarray, max_iter: int = 40, tol: float = 1e-7
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    v_sq = np.ones(feeder.n_bus, dtype=float)
    p_flow = np.zeros(len(feeder.branches_from), dtype=float)
    q_flow = np.zeros(len(feeder.branches_from), dtype=float)
    ell = np.zeros(len(feeder.branches_from), dtype=float)

    for _ in range(max_iter):
        old_v_sq = v_sq.copy()
        for br in range(len(feeder.branches_from) - 1, -1, -1):
            child = feeder.branches_to[br]
            downstream_p = p_net_pu[child]
            downstream_q = q_net_pu[child]
            for child_br in feeder.child_branch_index[child]:
                downstream_p += p_flow[child_br]
                downstream_q += q_flow[child_br]
            parent = feeder.branches_from[br]
            v_parent = max(v_sq[parent], 1e-4)
            loss_term = (downstream_p**2 + downstream_q**2) / v_parent
            p_flow[br] = downstream_p + feeder.r_pu[br] * loss_term
            q_flow[br] = downstream_q + feeder.x_pu[br] * loss_term
            ell[br] = (p_flow[br] ** 2 + q_flow[br] ** 2) / v_parent

        v_sq[0] = 1.0
        for br in range(len(feeder.branches_from)):
            parent = feeder.branches_from[br]
            child = feeder.branches_to[br]
            drop = (
                2.0 * (feeder.r_pu[br] * p_flow[br] + feeder.x_pu[br] * q_flow[br])
                - (feeder.r_pu[br] ** 2 + feeder.x_pu[br] ** 2) * ell[br]
            )
            v_sq[child] = max(v_sq[parent] - drop, 0.80**2)

        if float(np.max(np.abs(v_sq - old_v_sq))) < tol:
            break

    return np.sqrt(np.maximum(v_sq, 1e-8)), p_flow, q_flow, ell


def compute_branch_limits(feeder: DDRE33Feeder) -> np.ndarray:
    max_s_mva = np.zeros(len(feeder.branches_from), dtype=float)
    for scale in feeder.load_shape:
        p_net = feeder.base_pd_mw * scale / feeder.s_base_mva
        q_net = feeder.base_qd_mvar * scale / feeder.s_base_mva
        _, p_flow, q_flow, _ = backward_forward_sweep(feeder, p_net, q_net)
        s_mva = np.sqrt(p_flow**2 + q_flow**2) * feeder.s_base_mva
        max_s_mva = np.maximum(max_s_mva, s_mva)
    return np.maximum(1.35 * max_s_mva + 0.05, 0.12)


def evaluate_daily_profile(feeder: DDRE33Feeder, scenario_df: pd.DataFrame) -> dict[str, float | int]:
    scenario_df = scenario_df.rename(columns=lambda c: str(c).replace(" (MW)", ""))
    renewable_cols = list(RENEWABLE_BUS_MAP.keys())
    required = ["timestamp", *renewable_cols]
    missing = [c for c in required if c not in scenario_df.columns]
    if missing:
        raise ValueError(f"Scenario file is missing columns: {missing}")

    max_loading = 0.0
    min_voltage = 10.0
    loss_mwh = 0.0
    voltage_violation_steps = 0
    line_violation_steps = 0
    feasible_steps = 0

    dt_hours = 0.25
    for t, (_, row) in enumerate(scenario_df.iterrows()):
        scale = feeder.load_shape[min(t, len(feeder.load_shape) - 1)]
        p_net_mw = feeder.base_pd_mw * scale
        q_net_mvar = feeder.base_qd_mvar * scale
        for col, bus in RENEWABLE_BUS_MAP.items():
            p_net_mw[bus - 1] -= float(row[col])

        voltages, p_flow, q_flow, ell = backward_forward_sweep(
            feeder, p_net_mw / feeder.s_base_mva, q_net_mvar / feeder.s_base_mva
        )
        s_mva = np.sqrt(p_flow**2 + q_flow**2) * feeder.s_base_mva
        loading_pct = s_mva / np.maximum(feeder.branch_limit_mva, 1e-6) * 100.0
        step_min_v = float(voltages.min())
        step_max_loading = float(loading_pct.max())
        max_loading = max(max_loading, step_max_loading)
        min_voltage = min(min_voltage, step_min_v)
        loss_mwh += float(np.sum(feeder.r_pu * ell) * feeder.s_base_mva * dt_hours)

        voltage_ok = (step_min_v >= feeder.v_min_pu) and (float(voltages.max()) <= feeder.v_max_pu)
        line_ok = step_max_loading <= 100.0
        voltage_violation_steps += int(not voltage_ok)
        line_violation_steps += int(not line_ok)
        feasible_steps += int(voltage_ok and line_ok)

    total_steps = max(len(scenario_df), 1)
    return {
        "scenario_index": int(scenario_df["scenario_id"].iloc[0]),
        "min_voltage_pu": float(min_voltage),
        "max_branch_loading_pct": float(max_loading),
        "daily_loss_mwh": float(loss_mwh),
        "voltage_violation_rate": float(voltage_violation_steps / total_steps),
        "line_violation_rate": float(line_violation_steps / total_steps),
        "feasible_step_share": float(feasible_steps / total_steps),
    }


def load_actual_day_scenario(data_dir: str | Path, scenario_index: int) -> pd.DataFrame:
    path = Path(data_dir) / "1-Day Scenarios Actual" / f"scenario_{scenario_index:03d}.csv"
    return pd.read_csv(path)


def build_all_scenario_physics(data_dir: str | Path) -> pd.DataFrame:
    feeder = build_feeder()
    rows = []
    for scenario_index in range(1, 201):
        rows.append(evaluate_daily_profile(feeder, load_actual_day_scenario(data_dir, scenario_index)))
    return pd.DataFrame(rows).sort_values("scenario_index").reset_index(drop=True)
