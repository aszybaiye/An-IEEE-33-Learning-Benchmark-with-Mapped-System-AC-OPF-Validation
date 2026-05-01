from __future__ import annotations

import numpy as np
import pandas as pd


def pick_medoid_indices(embedding: np.ndarray, labels: np.ndarray) -> list[int]:
    medoids: list[int] = []
    for c in np.unique(labels):
        idx = np.where(labels == c)[0]
        group = embedding[idx]
        center = group.mean(axis=0)
        d = np.linalg.norm(group - center, axis=1)
        medoids.append(int(idx[np.argmin(d)]))
    return medoids


def compute_ood_scores(embedding: np.ndarray) -> np.ndarray:
    if embedding.size == 0:
        return np.array([], dtype=float)
    center = np.median(embedding, axis=0)
    mad = np.median(np.abs(embedding - center), axis=0)
    mad = np.where(mad < 1e-6, 1e-6, mad)
    robust_scaled = (embedding - center) / mad
    return np.linalg.norm(robust_scaled, axis=1)


def build_dual_library(
    metadata: pd.DataFrame,
    embedding: np.ndarray,
    labels: np.ndarray,
    risk_quantile: float,
    ood_quantile: float = 0.98,
    ood_min_count: int = 2,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    data = metadata.copy().reset_index(drop=True)
    data["_row_id"] = np.arange(len(data))
    data["ood_score"] = compute_ood_scores(embedding)
    normal_idx = pick_medoid_indices(embedding, labels)
    normal_library = data.iloc[normal_idx].copy().reset_index(drop=True)

    risk_threshold = float(data["risk_score"].quantile(risk_quantile))
    risk_pool = data[data["risk_score"] >= risk_threshold].copy()

    ood_threshold = float(data["ood_score"].quantile(ood_quantile))
    ood_pool = data[data["ood_score"] >= ood_threshold].copy()
    if len(ood_pool) < int(ood_min_count):
        ood_pool = data.sort_values("ood_score", ascending=False).head(int(ood_min_count)).copy()

    merged = pd.concat([risk_pool, ood_pool], ignore_index=True).drop_duplicates(subset="_row_id")
    if merged.empty:
        merged = data.sort_values("risk_score", ascending=False).head(max(6, len(normal_idx))).copy()
    risk_norm = merged["risk_score"] / max(float(merged["risk_score"].max()), 1e-9)
    ood_norm = merged["ood_score"] / max(float(merged["ood_score"].max()), 1e-9)
    merged["selection_score"] = 0.7 * risk_norm + 0.3 * ood_norm
    target_size = max(6, len(normal_idx), int(ood_min_count))
    risk_part = (
        merged.sort_values(["selection_score", "risk_score", "ood_score"], ascending=False)
        .head(target_size)
        .drop(columns=["_row_id", "selection_score"], errors="ignore")
        .reset_index(drop=True)
    )
    normal_library = normal_library.drop(columns=["_row_id"], errors="ignore")
    return normal_library, risk_part
