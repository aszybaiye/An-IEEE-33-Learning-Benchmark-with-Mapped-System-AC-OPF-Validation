from __future__ import annotations

import copy
import os
import time
from dataclasses import dataclass

import numpy as np
import pandas as pd

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")

from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

from pypower.api import case30, case118, ppoption, runopf
from pypower.idx_brch import BR_STATUS, PF, PT, QF, QT, RATE_A
from pypower.idx_bus import BUS_I, BUS_TYPE, PD, QD, VM, VMAX, VMIN, PQ
from pypower.idx_cost import MODEL, NCOST
from pypower.idx_gen import GEN_BUS, PG, PMAX, PMIN, QG, QMAX, QMIN


CASE_LOADERS = {
    "case30": case30,
    "case118": case118,
}

SCENARIO_PARAM_COLS = [
    "load_scale",
    "reactive_scale",
    "renewable_scale",
    "ramp_max",
    "smoothness",
    "std_power",
    "complementarity",
]

OPF_RESPONSE_COLS = [
    "objective_eur",
    "max_line_loading_pct",
    "min_vm_pu",
    "active_line_constraints",
    "active_voltage_constraints",
    "active_gen_max_constraints",
    "active_gen_min_constraints",
]


@dataclass
class CaseTemplate:
    mpc: dict
    renewable_rows: np.ndarray
    renewable_caps: np.ndarray


def _copy_mpc(mpc: dict) -> dict:
    out = {}
    for key, value in mpc.items():
        if isinstance(value, np.ndarray):
            out[key] = value.copy()
        else:
            out[key] = copy.deepcopy(value)
    return out


def _select_renewable_rows(bus: np.ndarray, count: int) -> np.ndarray:
    pq_rows = np.where(bus[:, BUS_TYPE] == PQ)[0]
    if len(pq_rows) <= count:
        return pq_rows
    pos = np.linspace(0, len(pq_rows) - 1, count)
    return np.array([pq_rows[int(round(x))] for x in pos], dtype=int)


def _normalize_gencost(gencost: np.ndarray, ng: int) -> np.ndarray:
    cost = np.array(gencost, dtype=float, copy=True)
    if cost.shape[0] < ng:
        extra = np.repeat(cost[-1:, :], ng - cost.shape[0], axis=0)
        cost = np.vstack([cost, extra])
    if cost.shape[0] > ng:
        cost = cost[:ng, :]
    for i in range(cost.shape[0]):
        cost[i, MODEL] = 2.0
        cost[i, NCOST] = 3.0
    return cost


def create_case_template(case_name: str) -> CaseTemplate:
    if case_name not in CASE_LOADERS:
        raise ValueError(f"Unsupported case: {case_name}")
    mpc = CASE_LOADERS[case_name]()
    mpc = _copy_mpc(mpc)
    bus = mpc["bus"]
    gen = mpc["gen"]
    branch = mpc["branch"]
    branch[:, RATE_A] = np.where(branch[:, RATE_A] > 0, branch[:, RATE_A], 250.0)
    branch[:, BR_STATUS] = 1.0
    bus[:, VMIN] = np.maximum(bus[:, VMIN], 0.94)
    bus[:, VMAX] = np.minimum(np.maximum(bus[:, VMAX], 1.06), 1.08)
    gen[:, PMIN] = np.minimum(gen[:, PMIN], 0.3 * np.maximum(gen[:, PMAX], 1.0))
    gen[:, QMIN] = np.minimum(gen[:, QMIN], -1.2 * np.maximum(np.abs(gen[:, QMAX]), 10.0))
    gen[:, QMAX] = np.maximum(gen[:, QMAX], 1.2 * np.maximum(np.abs(gen[:, QMAX]), 10.0))
    renewable_count = 4 if case_name == "case30" else 8
    renewable_rows = _select_renewable_rows(bus, renewable_count)
    base_total_load = float(bus[:, PD].sum())
    renewable_total = 0.18 * base_total_load if case_name == "case30" else 0.15 * base_total_load
    weights = np.linspace(1.0, 1.5, len(renewable_rows))
    renewable_caps = renewable_total * weights / weights.sum()
    mpc["gencost"] = _normalize_gencost(mpc["gencost"], gen.shape[0])
    return CaseTemplate(mpc=mpc, renewable_rows=renewable_rows, renewable_caps=renewable_caps)


def sample_opf_scenarios(features: pd.DataFrame, sample_size: int, seed: int) -> pd.DataFrame:
    if sample_size >= len(features):
        sampled = features.copy()
    else:
        work = features.copy()
        work["risk_bin"] = pd.qcut(
            work["risk_score"].rank(method="first"),
            q=min(4, len(work)),
            labels=False,
            duplicates="drop",
        )
        work["opf_tag"] = (
            work["wind_label"].astype(str)
            + "_"
            + work["pv_label"].astype(str)
            + "_"
            + work["risk_bin"].astype(str)
        )
        parts = []
        rng = np.random.default_rng(seed)
        for _, group in work.groupby("opf_tag", sort=False):
            take = max(1, int(round(sample_size * len(group) / len(work))))
            idx = rng.choice(group.index.to_numpy(), size=min(take, len(group)), replace=False)
            parts.append(work.loc[idx])
        sampled = pd.concat(parts, ignore_index=True)
        if len(sampled) > sample_size:
            sampled = sampled.sample(sample_size, random_state=seed).reset_index(drop=True)
        elif len(sampled) < sample_size:
            remaining = work.loc[~work["scenario_index"].isin(sampled["scenario_index"])]
            extra = remaining.sample(min(sample_size - len(sampled), len(remaining)), random_state=seed)
            sampled = pd.concat([sampled, extra], ignore_index=True)
    sampled = sampled.sort_values("scenario_index").reset_index(drop=True)
    sampled["load_scale"] = (
        0.78
        + 0.32 * sampled["mean_power"]
        + 0.10 * sampled["peak_power"]
        + 0.12 * sampled["power_deficit"]
    ).clip(0.70, 1.35)
    sampled["reactive_scale"] = (
        0.82 + 0.22 * sampled["std_power"] + 0.18 * sampled["smoothness"]
    ).clip(0.75, 1.25)
    sampled["renewable_scale"] = (
        0.12 + 1.05 * sampled["mean_power"] + 0.10 * sampled["pv_mean"]
    ).clip(0.05, 1.15)
    sampled["scenario_stress"] = (
        0.50 * sampled["ramp_max"]
        + 0.20 * sampled["std_power"]
        + 0.20 * sampled["power_deficit"]
        + 0.10 * sampled["smoothness"]
    )
    return sampled


def _apply_scenario(template: CaseTemplate, scenario: pd.Series) -> dict:
    mpc = _copy_mpc(template.mpc)
    bus = mpc["bus"]
    base_pd = template.mpc["bus"][:, PD]
    base_qd = template.mpc["bus"][:, QD]
    bus[:, PD] = base_pd * float(scenario["load_scale"])
    bus[:, QD] = base_qd * float(scenario["reactive_scale"])
    renewable = template.renewable_caps * float(scenario["renewable_scale"])
    for row, injection in zip(template.renewable_rows, renewable):
        bus[row, PD] -= injection
        bus[row, QD] -= 0.05 * injection
    return mpc


def validate_constraints(result: dict) -> dict[str, float]:
    bus = result["bus"]
    gen = result["gen"]
    branch = result["branch"]
    total_gen = float(gen[:, PG].sum())
    total_load = float(bus[:, PD].sum())
    total_losses = float(np.maximum(branch[:, PF] + branch[:, PT], 0.0).sum())
    s_from = np.sqrt(branch[:, PF] ** 2 + branch[:, QF] ** 2)
    s_to = np.sqrt(branch[:, PT] ** 2 + branch[:, QT] ** 2)
    rates = np.maximum(branch[:, RATE_A], 1e-9)
    line_loading = np.maximum(s_from, s_to) / rates * 100.0
    voltage_low = np.maximum(bus[:, VMIN] - bus[:, VM], 0.0)
    voltage_high = np.maximum(bus[:, VM] - bus[:, VMAX], 0.0)
    return {
        "power_balance_residual_mw": float(abs(total_gen - total_load - total_losses)),
        "line_violation_pct": float(np.maximum(line_loading - 100.0, 0.0).max()),
        "voltage_violation_pu": float(max(voltage_low.max(), voltage_high.max())),
    }


def _active_constraint_signature(result: dict) -> tuple[str, dict[str, int]]:
    bus = result["bus"]
    gen = result["gen"]
    branch = result["branch"]
    s_from = np.sqrt(branch[:, PF] ** 2 + branch[:, QF] ** 2)
    s_to = np.sqrt(branch[:, PT] ** 2 + branch[:, QT] ** 2)
    rates = np.maximum(branch[:, RATE_A], 1e-9)
    line_loading = np.maximum(s_from, s_to) / rates * 100.0
    line_bind = [int(i) for i in np.where(line_loading >= 97.0)[0].tolist()]
    vm_low = [int(i) for i in np.where(bus[:, VM] <= bus[:, VMIN] + 0.01)[0].tolist()]
    vm_high = [int(i) for i in np.where(bus[:, VM] >= bus[:, VMAX] - 0.01)[0].tolist()]
    gen_max = [int(i) for i in np.where(np.isclose(gen[:, PG], gen[:, PMAX], atol=1e-3))[0].tolist()]
    gen_min = [int(i) for i in np.where(np.isclose(gen[:, PG], gen[:, PMIN], atol=1e-3))[0].tolist()]
    key = (
        f"L:{','.join(map(str, line_bind[:3])) or 'none'}|"
        f"VL:{','.join(map(str, vm_low[:2])) or 'none'}|"
        f"VH:{','.join(map(str, vm_high[:2])) or 'none'}|"
        f"GMAX:{','.join(map(str, gen_max[:2])) or 'none'}|"
        f"GMIN:{','.join(map(str, gen_min[:2])) or 'none'}"
    )
    return key, {
        "active_line_constraints": len(line_bind),
        "active_voltage_constraints": len(vm_low) + len(vm_high),
        "active_gen_max_constraints": len(gen_max),
        "active_gen_min_constraints": len(gen_min),
    }


def run_case_opf(case_name: str, scenarios: pd.DataFrame) -> pd.DataFrame:
    template = create_case_template(case_name)
    ppopt = ppoption(VERBOSE=0, OUT_ALL=0)
    rows: list[dict[str, float | int | str | bool]] = []
    for scenario in scenarios.itertuples(index=False):
        scenario_dict = scenario._asdict()
        mpc = _apply_scenario(template, pd.Series(scenario_dict))
        start = time.perf_counter()
        result = runopf(mpc, ppopt)
        solve_time = time.perf_counter() - start
        if not result["success"]:
            rows.append(
                {
                    "case_name": case_name,
                    "scenario_index": int(scenario_dict["scenario_index"]),
                    "converged": False,
                    "solve_time_s": float(solve_time),
                    **{k: float(scenario_dict[k]) for k in SCENARIO_PARAM_COLS},
                }
            )
            continue
        bus = result["bus"]
        branch = result["branch"]
        s_from = np.sqrt(branch[:, PF] ** 2 + branch[:, QF] ** 2)
        s_to = np.sqrt(branch[:, PT] ** 2 + branch[:, QT] ** 2)
        line_loading = np.maximum(s_from, s_to) / np.maximum(branch[:, RATE_A], 1e-9) * 100.0
        constraint_metrics = validate_constraints(result)
        active_key, active_counts = _active_constraint_signature(result)
        rows.append(
            {
                "case_name": case_name,
                "scenario_index": int(scenario_dict["scenario_index"]),
                "converged": True,
                "solve_time_s": float(solve_time),
                "objective_eur": float(result["f"]),
                "max_line_loading_pct": float(line_loading.max()),
                "min_vm_pu": float(bus[:, VM].min()),
                "max_vm_pu": float(bus[:, VM].max()),
                "active_set_key": active_key,
                **constraint_metrics,
                **active_counts,
                **{k: float(scenario_dict[k]) for k in SCENARIO_PARAM_COLS},
            }
        )
    return pd.DataFrame(rows)


def summarize_case_results(result_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for case_name, group in result_df.groupby("case_name"):
        conv = group[group["converged"]].copy()
        rows.append(
            {
                "case_name": case_name,
                "scenario_count": int(len(group)),
                "convergence_rate": float(group["converged"].mean()),
                "mean_objective_eur": float(conv["objective_eur"].mean()),
                "std_objective_eur": float(conv["objective_eur"].std(ddof=0)),
                "mean_solve_time_s": float(conv["solve_time_s"].mean()),
                "mean_power_balance_residual_mw": float(conv["power_balance_residual_mw"].mean()),
                "max_line_violation_pct": float(conv["line_violation_pct"].max()),
                "max_voltage_violation_pu": float(conv["voltage_violation_pu"].max()),
            }
        )
    return pd.DataFrame(rows)


def _standardize(x: np.ndarray) -> np.ndarray:
    if len(x) == 0:
        return x
    return StandardScaler().fit_transform(x)


def _pick_medoids(data: np.ndarray, labels: np.ndarray) -> list[int]:
    medoids: list[int] = []
    for c in np.unique(labels):
        idx = np.where(labels == c)[0]
        subset = data[idx]
        center = subset.mean(axis=0, keepdims=True)
        dist = np.linalg.norm(subset - center, axis=1)
        medoids.append(int(idx[np.argmin(dist)]))
    return medoids


def _kmeans_medoids(x: np.ndarray, k: int, seed: int) -> list[int]:
    if k >= len(x):
        return list(range(len(x)))
    km = KMeans(n_clusters=k, random_state=seed, n_init=20)
    labels = km.fit_predict(x)
    return _pick_medoids(x, labels)


def _farthest_point_selection(x: np.ndarray, k: int) -> list[int]:
    if k >= len(x):
        return list(range(len(x)))
    picked = [int(np.argmax(np.linalg.norm(x - x.mean(axis=0, keepdims=True), axis=1)))]
    while len(picked) < k:
        dist = np.linalg.norm(x[:, None, :] - x[np.array(picked)][None, :, :], axis=2)
        idx = int(np.argmax(dist.min(axis=1)))
        if idx in picked:
            break
        picked.append(idx)
    return picked


def _sensitivity_scores(df: pd.DataFrame) -> np.ndarray:
    obj = df["objective_eur"].to_numpy(dtype=float)
    obj_dev = np.abs(obj - obj.mean()) / (obj.std(ddof=0) + 1e-9)
    loading = df["max_line_loading_pct"].to_numpy(dtype=float) / 100.0
    vm = np.abs(1.0 - df["min_vm_pu"].to_numpy(dtype=float)) / 0.05
    active = (
        df["active_line_constraints"].to_numpy(dtype=float)
        + df["active_voltage_constraints"].to_numpy(dtype=float)
        + df["active_gen_max_constraints"].to_numpy(dtype=float)
    )
    active = active / (active.max() + 1e-9)
    return obj_dev + 0.8 * loading + 0.7 * vm + 0.7 * active


def select_representatives(method: str, df: pd.DataFrame, k: int, seed: int) -> list[int]:
    if k >= len(df):
        return list(range(len(df)))
    feat_x = _standardize(df[SCENARIO_PARAM_COLS].to_numpy(dtype=float))
    resp_x = _standardize(df[OPF_RESPONSE_COLS].to_numpy(dtype=float))
    if method == "kmeans_feature":
        return _kmeans_medoids(feat_x, k, seed)
    if method == "forward_feature":
        return _farthest_point_selection(feat_x, k)
    if method == "opf_sensitivity":
        scores = _sensitivity_scores(df)
        extreme_n = max(2, k // 3)
        selected = list(np.argsort(scores)[::-1][:extreme_n])
        remain_mask = np.ones(len(df), dtype=bool)
        remain_mask[np.array(selected, dtype=int)] = False
        remain_idx = np.where(remain_mask)[0]
        if len(remain_idx) and len(selected) < k:
            medoids = _kmeans_medoids(resp_x[remain_idx], k - len(selected), seed)
            selected.extend([int(remain_idx[i]) for i in medoids])
        return selected[:k]
    if method == "opf_kkt_active_set":
        scores = _sensitivity_scores(df)
        selected: list[int] = []
        grouped = []
        for key, group in df.assign(_score=scores).groupby("active_set_key", sort=False):
            rep = group.sort_values(["_score", "objective_eur"], ascending=[False, False]).iloc[0]
            grouped.append((key, float(group["_score"].mean()), int(len(group)), int(rep.name)))
        grouped.sort(key=lambda item: (item[1], item[2]), reverse=True)
        for _, _, _, idx in grouped:
            if idx not in selected:
                selected.append(idx)
            if len(selected) >= k:
                return selected[:k]
        for idx in np.argsort(scores)[::-1].tolist():
            if idx not in selected:
                selected.append(int(idx))
            if len(selected) >= k:
                break
        return selected[:k]
    raise ValueError(f"Unsupported reduction method: {method}")


def evaluate_reduction_method(
    case_df: pd.DataFrame,
    method: str,
    selected_count: int,
    seed: int,
) -> dict[str, float | int | str]:
    start = time.perf_counter()
    selected_idx = select_representatives(method, case_df, selected_count, seed)
    selection_time = time.perf_counter() - start
    selected = case_df.iloc[selected_idx].copy().reset_index(drop=True)
    feat_x = _standardize(case_df[SCENARIO_PARAM_COLS].to_numpy(dtype=float))
    rep_x = _standardize(selected[SCENARIO_PARAM_COLS].to_numpy(dtype=float))
    dist = np.linalg.norm(feat_x[:, None, :] - rep_x[None, :, :], axis=2)
    assign = dist.argmin(axis=1)
    true_cost = case_df["objective_eur"].to_numpy(dtype=float)
    true_line = case_df["max_line_loading_pct"].to_numpy(dtype=float)
    true_vm = case_df["min_vm_pu"].to_numpy(dtype=float)
    approx_cost = selected["objective_eur"].to_numpy(dtype=float)[assign]
    approx_line = selected["max_line_loading_pct"].to_numpy(dtype=float)[assign]
    approx_vm = selected["min_vm_pu"].to_numpy(dtype=float)[assign]
    cost_err = np.abs(true_cost - approx_cost) / np.maximum(np.abs(true_cost), 1e-9) * 100.0
    reduced_time = float(selected["solve_time_s"].sum())
    full_time = float(case_df["solve_time_s"].sum())
    return {
        "case_name": str(case_df["case_name"].iloc[0]),
        "method": method,
        "selected_count": int(len(selected)),
        "objective_mape_pct": float(np.mean(cost_err)),
        "worst_objective_error_pct": float(np.max(cost_err)),
        "line_loading_mae_pct": float(np.mean(np.abs(true_line - approx_line))),
        "voltage_min_mae_pu": float(np.mean(np.abs(true_vm - approx_vm))),
        "selection_time_s": float(selection_time),
        "reduced_opf_time_s": reduced_time,
        "full_opf_time_s": full_time,
        "time_saving_ratio": float(full_time / max(reduced_time, 1e-9)),
        "scenario_retention_ratio": float(len(selected) / len(case_df)),
    }


def summarize_reduction_results(reduction_df: pd.DataFrame) -> pd.DataFrame:
    grouped = (
        reduction_df.groupby(["case_name", "selected_count", "method"], as_index=False)
        .agg(
            objective_mape_pct_mean=("objective_mape_pct", "mean"),
            objective_mape_pct_std=("objective_mape_pct", "std"),
            worst_objective_error_pct_mean=("worst_objective_error_pct", "mean"),
            worst_objective_error_pct_std=("worst_objective_error_pct", "std"),
            line_loading_mae_pct_mean=("line_loading_mae_pct", "mean"),
            line_loading_mae_pct_std=("line_loading_mae_pct", "std"),
            voltage_min_mae_pu_mean=("voltage_min_mae_pu", "mean"),
            voltage_min_mae_pu_std=("voltage_min_mae_pu", "std"),
            selection_time_s_mean=("selection_time_s", "mean"),
            reduced_opf_time_s_mean=("reduced_opf_time_s", "mean"),
            full_opf_time_s_mean=("full_opf_time_s", "mean"),
            time_saving_ratio_mean=("time_saving_ratio", "mean"),
            time_saving_ratio_std=("time_saving_ratio", "std"),
            scenario_retention_ratio=("scenario_retention_ratio", "mean"),
            n_samples=("sample_id", "nunique"),
        )
        .sort_values(["case_name", "selected_count", "objective_mape_pct_mean", "line_loading_mae_pct_mean"])
        .reset_index(drop=True)
    )
    std_cols = [c for c in grouped.columns if c.endswith("_std")]
    grouped[std_cols] = grouped[std_cols].fillna(0.0)
    grouped["objective_mape_pct_ci95"] = 1.96 * grouped["objective_mape_pct_std"] / np.sqrt(
        np.maximum(grouped["n_samples"], 1)
    )
    grouped["time_saving_ratio_ci95"] = 1.96 * grouped["time_saving_ratio_std"] / np.sqrt(
        np.maximum(grouped["n_samples"], 1)
    )
    return grouped


def summarize_reduction_best(summary_df: pd.DataFrame) -> pd.DataFrame:
    idx = (
        summary_df.groupby(["case_name", "selected_count"])["objective_mape_pct_mean"]
        .idxmin()
        .to_numpy(dtype=int)
    )
    return summary_df.loc[idx].reset_index(drop=True)
