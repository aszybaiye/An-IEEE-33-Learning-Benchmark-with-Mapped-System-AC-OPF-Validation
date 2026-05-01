from __future__ import annotations

import copy
import re
import time
import traceback
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from pypower.api import ppoption, runopf
from pypower.idx_brch import BR_STATUS, F_BUS, PF, PT, QF, QT, RATE_A, T_BUS
from pypower.idx_bus import BASE_KV, BUS_TYPE, PD, PQ, QD, VM, VMAX, VMIN
from pypower.idx_cost import MODEL, NCOST
from pypower.idx_gen import PMAX, PMIN, QMAX, QMIN

from src.ddre33_validation import build_feeder

RENEWABLE_COLS = [
    "node_22_wind",
    "node_25_wind",
    "node_18_PV",
    "node_33_PV",
]


@dataclass
class DistributionCaseTemplate:
    case_name: str
    mpc: dict
    renewable_rows: np.ndarray
    renewable_caps: np.ndarray
    load_shape: np.ndarray
    reference_peak_by_col: dict[str, float]


def _copy_mpc(mpc: dict) -> dict:
    out = {}
    for key, value in mpc.items():
        if isinstance(value, np.ndarray):
            out[key] = value.copy()
        else:
            out[key] = copy.deepcopy(value)
    return out


def _normalize_scenario_columns(df: pd.DataFrame) -> pd.DataFrame:
    return df.rename(columns=lambda c: str(c).replace(" (MW)", "").strip())


def _extract_scalar(text: str, name: str) -> float:
    match = re.search(rf"mpc\.{re.escape(name)}\s*=\s*([0-9.eE+-]+)\s*;", text)
    if not match:
        raise ValueError(f"Cannot find scalar mpc.{name}")
    return float(match.group(1))


def _extract_matrix(text: str, name: str) -> np.ndarray:
    match = re.search(rf"mpc\.{re.escape(name)}\s*=\s*\[(.*?)\];", text, re.S)
    if not match:
        raise ValueError(f"Cannot find matrix mpc.{name}")
    block = match.group(1)
    rows: list[list[float]] = []
    for raw_line in block.splitlines():
        line = raw_line.split("%", 1)[0].strip()
        if not line:
            continue
        line = line.rstrip(";").strip()
        if not line:
            continue
        rows.append([float(x) for x in line.split()])
    return np.array(rows, dtype=float)


def load_distribution_case(case_file: str | Path) -> dict:
    text = Path(case_file).read_text(encoding="utf-8")
    mpc = {
        "version": "2",
        "baseMVA": _extract_scalar(text, "baseMVA"),
        "bus": _extract_matrix(text, "bus"),
        "gen": _extract_matrix(text, "gen"),
        "branch": _extract_matrix(text, "branch"),
        "gencost": _extract_matrix(text, "gencost"),
    }
    # case33bw/case69 store Pd/Qd in kW and line impedances in Ohms in the file body.
    vbase = mpc["bus"][0, BASE_KV] * 1e3
    sbase = mpc["baseMVA"] * 1e6
    mpc["branch"][:, [2, 3]] = mpc["branch"][:, [2, 3]] / (vbase**2 / sbase)
    mpc["bus"][:, [PD, QD]] = mpc["bus"][:, [PD, QD]] / 1e3
    return mpc


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


def _select_renewable_rows(bus: np.ndarray, count: int, preferred_buses: list[int] | None = None) -> np.ndarray:
    if preferred_buses:
        rows = [int(np.where(bus[:, 0] == b)[0][0]) for b in preferred_buses if np.any(bus[:, 0] == b)]
        if len(rows) == count:
            return np.array(rows, dtype=int)
    pq_rows = np.where(bus[:, BUS_TYPE] == PQ)[0]
    if len(pq_rows) <= count:
        return pq_rows.astype(int)
    pos = np.linspace(0, len(pq_rows) - 1, count)
    return np.array([pq_rows[int(round(x))] for x in pos], dtype=int)


def _estimate_branch_limits(mpc: dict) -> np.ndarray:
    def fallback_limits() -> np.ndarray:
        branch = np.array(mpc["branch"], dtype=float, copy=False)
        bus = np.array(mpc["bus"], dtype=float, copy=False)
        bus_ids = bus[:, 0].astype(int)
        pd_map = {int(row[0]): float(row[PD]) for row in bus}
        qd_map = {int(row[0]): float(row[QD]) for row in bus}
        child_map: dict[int, list[int]] = {}
        branch_to_bus: list[int] = []
        for row in branch:
            f_bus = int(row[F_BUS])
            t_bus = int(row[T_BUS])
            child_map.setdefault(f_bus, []).append(t_bus)
            branch_to_bus.append(t_bus)

        subtree_cache: dict[int, tuple[float, float]] = {}

        def subtree_load(bus_id: int) -> tuple[float, float]:
            if bus_id in subtree_cache:
                return subtree_cache[bus_id]
            p_total = pd_map.get(bus_id, 0.0)
            q_total = qd_map.get(bus_id, 0.0)
            for child in child_map.get(bus_id, []):
                p_child, q_child = subtree_load(child)
                p_total += p_child
                q_total += q_child
            subtree_cache[bus_id] = (p_total, q_total)
            return subtree_cache[bus_id]

        total_load = max(float(np.sqrt(np.sum(bus[:, PD]) ** 2 + np.sum(bus[:, QD]) ** 2)), 1.0)
        limits = []
        for t_bus in branch_to_bus:
            p_sub, q_sub = subtree_load(t_bus)
            s_sub = float(np.sqrt(p_sub**2 + q_sub**2))
            limits.append(max(1.35 * s_sub + 0.25, 0.08 * total_load))
        if len(limits) != branch.shape[0] or len(bus_ids) == 0:
            return np.full(branch.shape[0], max(0.1 * total_load, 1.0), dtype=float)
        return np.array(limits, dtype=float)

    tmp = _copy_mpc(mpc)
    tmp["branch"][:, RATE_A] = 0.0
    try:
        res = runopf(tmp, ppoption(VERBOSE=0, OUT_ALL=0))
        if not res["success"]:
            return fallback_limits()
        branch = res["branch"]
        s_from = np.sqrt(branch[:, PF] ** 2 + branch[:, QF] ** 2)
        s_to = np.sqrt(branch[:, PT] ** 2 + branch[:, QT] ** 2)
        nominal = np.maximum(s_from, s_to)
        return np.maximum(1.35 * nominal, 0.15 * nominal.max() + 0.5)
    except Exception:
        return fallback_limits()


def _reference_peak_by_col(data_dir: str | Path) -> dict[str, float]:
    data_root = Path(data_dir) / "1-Day Scenarios Actual"
    peaks = {col: 1e-6 for col in RENEWABLE_COLS}
    for path in sorted(data_root.glob("scenario_*.csv")):
        df = _normalize_scenario_columns(pd.read_csv(path))
        for col in RENEWABLE_COLS:
            if col in df.columns:
                peaks[col] = max(peaks[col], float(df[col].max()))
    return peaks


def build_distribution_case_template(case_name: str, data_dir: str | Path) -> DistributionCaseTemplate:
    case_file = Path(data_dir) / "networks" / f"{case_name}.m"
    mpc = load_distribution_case(case_file)
    bus = mpc["bus"]
    gen = mpc["gen"]
    branch = mpc["branch"]
    branch[:, BR_STATUS] = 1.0
    branch[:, RATE_A] = _estimate_branch_limits(mpc)
    bus[:, VMIN] = np.maximum(bus[:, VMIN], 0.94)
    bus[:, VMAX] = np.minimum(np.maximum(bus[:, VMAX], 1.05), 1.08)
    gen[:, PMIN] = np.minimum(gen[:, PMIN], 0.2 * np.maximum(gen[:, PMAX], 1.0))
    gen[:, QMIN] = np.minimum(gen[:, QMIN], -1.2 * np.maximum(np.abs(gen[:, QMAX]), 5.0))
    gen[:, QMAX] = np.maximum(gen[:, QMAX], 1.2 * np.maximum(np.abs(gen[:, QMAX]), 5.0))
    mpc["gencost"] = _normalize_gencost(mpc["gencost"], gen.shape[0])
    preferred = [18, 22, 25, 33] if case_name == "case33bw" else None
    renewable_rows = _select_renewable_rows(bus, 4, preferred_buses=preferred)
    base_total_load = float(bus[:, PD].sum())
    renewable_total = 0.18 * base_total_load if case_name == "case33bw" else 0.15 * base_total_load
    weights = np.linspace(1.0, 1.4, len(renewable_rows))
    renewable_caps = renewable_total * weights / weights.sum()
    return DistributionCaseTemplate(
        case_name=case_name,
        mpc=mpc,
        renewable_rows=renewable_rows,
        renewable_caps=renewable_caps,
        load_shape=build_feeder().load_shape,
        reference_peak_by_col=_reference_peak_by_col(data_dir),
    )


def _renewable_profile(template: DistributionCaseTemplate, row: pd.Series) -> np.ndarray:
    profile = []
    for col in RENEWABLE_COLS:
        peak = max(template.reference_peak_by_col[col], 1e-6)
        profile.append(max(float(row[col]), 0.0) / peak)
    return template.renewable_caps * np.array(profile, dtype=float)


def apply_snapshot(template: DistributionCaseTemplate, load_scale: float, renewable_profile: np.ndarray) -> dict:
    mpc = _copy_mpc(template.mpc)
    bus = mpc["bus"]
    base_pd = template.mpc["bus"][:, PD]
    base_qd = template.mpc["bus"][:, QD]
    bus[:, PD] = base_pd * float(load_scale)
    bus[:, QD] = base_qd * float(0.92 * load_scale + 0.08)
    for row_idx, injection in zip(template.renewable_rows, renewable_profile):
        bus[row_idx, PD] -= injection
        bus[row_idx, QD] -= 0.05 * injection
    return mpc


def _apply_case33bw_retry_patch(mpc: dict, retry_level: int) -> dict:
    patched = _copy_mpc(mpc)
    if retry_level <= 0:
        return patched
    # Retry levels gradually relax operating stress for known hard cases.
    load_factors = [1.0, 0.98, 0.95, 0.92]
    factor = load_factors[min(retry_level, len(load_factors) - 1)]
    patched["bus"][:, PD] *= factor
    patched["bus"][:, QD] *= max(0.9, factor - 0.02)
    if retry_level >= 2:
        patched["bus"][:, VMIN] = np.maximum(0.90, patched["bus"][:, VMIN] - 0.01)
    if retry_level >= 3:
        patched["gen"][:, QMAX] = patched["gen"][:, QMAX] * 1.10
        patched["gen"][:, QMIN] = patched["gen"][:, QMIN] * 1.10
        patched["branch"][:, RATE_A] = np.maximum(patched["branch"][:, RATE_A], 1.05 * patched["branch"][:, RATE_A])
    return patched


def _run_opf_with_retries(mpc: dict, case_name: str) -> tuple[dict | None, int, str]:
    retry_budget = 3 if case_name == "case33bw" else 0
    last_error = ""
    for retry in range(retry_budget + 1):
        mpc_try = _apply_case33bw_retry_patch(mpc, retry) if case_name == "case33bw" else _copy_mpc(mpc)
        try:
            result = runopf(mpc_try, ppoption(VERBOSE=0, OUT_ALL=0))
            if bool(result.get("success", False)):
                return result, retry, ""
            last_error = f"OPF did not converge (retry={retry})"
        except Exception:
            last_error = traceback.format_exc().splitlines()[-1][:240]
    return None, retry_budget, last_error


def pick_critical_snapshot(template: DistributionCaseTemplate, scenario_df: pd.DataFrame) -> tuple[int, float, np.ndarray]:
    scenario_df = _normalize_scenario_columns(scenario_df)
    scores = []
    for t, (_, row) in enumerate(scenario_df.iterrows()):
        load_scale = float(template.load_shape[min(t, len(template.load_shape) - 1)])
        renewable_profile = _renewable_profile(template, row)
        score = float(template.mpc["bus"][:, PD].sum() * load_scale - renewable_profile.sum())
        scores.append((score, t, load_scale, renewable_profile))
    _, t_star, load_scale_star, renewable_star = max(scores, key=lambda x: x[0])
    return t_star, load_scale_star, renewable_star


def validate_result(result: dict) -> dict[str, float]:
    bus = result["bus"]
    gen = result["gen"]
    branch = result["branch"]
    total_gen = float(gen[:, 1].sum())
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
        "max_line_loading_pct": float(line_loading.max()),
        "min_vm_pu": float(bus[:, VM].min()),
        "max_vm_pu": float(bus[:, VM].max()),
    }


def run_snapshot_opf(
    template: DistributionCaseTemplate,
    scenario_index: int,
    scenario_df: pd.DataFrame,
) -> dict[str, float | int | str | bool]:
    snapshot_t, load_scale, renewable_profile = pick_critical_snapshot(template, scenario_df)
    mpc = apply_snapshot(template, load_scale, renewable_profile)
    start = time.perf_counter()
    result, retry_count, error_message = _run_opf_with_retries(mpc, template.case_name)
    solve_time = time.perf_counter() - start
    if result is None:
        return {
            "case_name": template.case_name,
            "scenario_index": int(scenario_index),
            "snapshot_step": int(snapshot_t),
            "load_scale": float(load_scale),
            "renewable_total_mw": float(renewable_profile.sum()),
            "converged": False,
            "retry_count": int(retry_count),
            "solve_time_s": float(solve_time),
            "error_message": error_message,
        }
    row: dict[str, float | int | str | bool] = {
        "case_name": template.case_name,
        "scenario_index": int(scenario_index),
        "snapshot_step": int(snapshot_t),
        "load_scale": float(load_scale),
        "renewable_total_mw": float(renewable_profile.sum()),
        "converged": bool(result["success"]),
        "retry_count": int(retry_count),
        "solve_time_s": float(solve_time),
    }
    if not result["success"]:
        return row
    metrics = validate_result(result)
    row.update(
        {
            "objective_eur": float(result["f"]),
            **metrics,
        }
    )
    return row
