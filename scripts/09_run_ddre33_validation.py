from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys

import numpy as np
import pandas as pd

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")

from sklearn.cluster import AgglomerativeClustering, KMeans, SpectralClustering

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.ddre33_validation import build_all_scenario_physics
from src.features import apply_learned_risk_score, learn_risk_weights
from src.io_utils import load_config, write_csv
from src.library import build_dual_library
from src.split import split_dataset
from src.xrfm import RiskAwareEmbedding


FEATURE_COLS = [
    "mean_power",
    "std_power",
    "peak_power",
    "ramp_max",
    "smoothness",
    "complementarity",
    "wind_mean",
    "pv_mean",
    "wind_peak",
    "pv_peak",
    "wind_std",
    "pv_std",
]


def pairwise_l2(x: np.ndarray) -> np.ndarray:
    return np.linalg.norm(x[:, None, :] - x[None, :, :], axis=2)


def fit_kmedoids_labels(x: np.ndarray, n_clusters: int, seed: int, max_iter: int = 20) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    dist = pairwise_l2(x)
    km = KMeans(n_clusters=n_clusters, random_state=seed, n_init=20)
    km.fit(x)
    medoids: list[int] = []
    for center in km.cluster_centers_:
        nearest = int(np.argmin(np.linalg.norm(x - center, axis=1)))
        if nearest not in medoids:
            medoids.append(nearest)
    if len(medoids) < n_clusters:
        candidates = [i for i in rng.permutation(len(x)).tolist() if i not in medoids]
        medoids.extend(candidates[: n_clusters - len(medoids)])
    medoids_arr = np.array(medoids[:n_clusters], dtype=int)
    for _ in range(max_iter):
        assign = dist[:, medoids_arr].argmin(axis=1)
        new_medoids = medoids_arr.copy()
        for cluster_id in range(n_clusters):
            members = np.where(assign == cluster_id)[0]
            if len(members) == 0:
                farthest = int(np.argmax(dist[:, medoids_arr].min(axis=1)))
                if farthest not in new_medoids:
                    new_medoids[cluster_id] = farthest
                continue
            subdist = dist[np.ix_(members, members)]
            new_medoids[cluster_id] = int(members[np.argmin(subdist.sum(axis=1))])
        if np.array_equal(np.sort(new_medoids), np.sort(medoids_arr)):
            medoids_arr = new_medoids
            break
        medoids_arr = new_medoids
    labels = dist[:, medoids_arr].argmin(axis=1)
    return labels.astype(int), medoids_arr.astype(int)


def prepare_seeded_dataset(features: pd.DataFrame, cfg: dict, seed: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    split_cfg = cfg["split"]
    splits = split_dataset(
        features,
        train_ratio=split_cfg["train"],
        val_ratio=split_cfg["val"],
        seed=seed,
        stratify_cols=split_cfg["stratify_cols"],
    )
    df = features.copy()
    df["subset"] = "train"
    df.loc[df["scenario_index"].isin(splits.val["scenario_index"]), "subset"] = "val"
    df.loc[df["scenario_index"].isin(splits.test["scenario_index"]), "subset"] = "test"
    weights = learn_risk_weights(df[df["subset"] == "train"].copy())
    df = apply_learned_risk_score(df, weights)
    return df[df["subset"] == "train"].reset_index(drop=True), df[df["subset"] == "test"].reset_index(drop=True)


def build_representative_maps(train: pd.DataFrame, seed: int, cfg: dict) -> dict[str, pd.DataFrame]:
    n_clusters = int(cfg["model"]["n_clusters"])
    risk_alpha = float(cfg["model"]["risk_alpha"])
    risk_quantile = float(cfg["model"]["risk_quantile"])
    x_train = train[FEATURE_COLS].to_numpy()
    spectral_neighbors = max(2, min(12, len(train) - 1))

    train_labeled = train.copy()
    train_labeled["kmeans_label"] = KMeans(n_clusters=n_clusters, random_state=seed, n_init=20).fit_predict(x_train)
    train_labeled["spectral_label"] = SpectralClustering(
        n_clusters=n_clusters,
        random_state=seed,
        affinity="nearest_neighbors",
        n_neighbors=spectral_neighbors,
        assign_labels="kmeans",
    ).fit_predict(x_train)
    train_labeled["hierarchical_label"] = AgglomerativeClustering(n_clusters=n_clusters, linkage="ward").fit_predict(
        x_train
    )
    train_labeled["kmedoids_label"] = fit_kmedoids_labels(x_train, n_clusters, seed)[0]

    xrfm = RiskAwareEmbedding(embedding_dim=int(min(4, x_train.shape[1])), risk_alpha=risk_alpha)
    embedding = xrfm.fit_transform(x_train, train["risk_score"].to_numpy())
    train_labeled["xrfm_label"] = KMeans(n_clusters=n_clusters, random_state=seed, n_init=20).fit_predict(embedding)

    rep_map: dict[str, pd.DataFrame] = {}
    for method_col in ["kmeans_label", "kmedoids_label", "spectral_label", "hierarchical_label", "xrfm_label"]:
        rep_map[method_col.replace("_label", "")] = (
            train_labeled.sort_values("risk_score", ascending=False)
            .groupby(method_col, as_index=False)
            .first()
            .reset_index(drop=True)
        )

    normal_lib, risk_lib = build_dual_library(
        train_labeled,
        embedding,
        train_labeled["xrfm_label"].to_numpy(),
        risk_quantile,
        float(cfg["model"].get("ood_quantile", 0.98)),
        int(cfg["model"].get("ood_min_count", 2)),
    )
    rep_map["xrfm_dual_library"] = pd.concat(
        [
            normal_lib[FEATURE_COLS + ["risk_score", "scenario_index"]],
            risk_lib[FEATURE_COLS + ["risk_score", "scenario_index"]],
        ],
        ignore_index=True,
    )
    return rep_map


def evaluate_direct_ddre33_validation(
    rep_map: dict[str, pd.DataFrame], test: pd.DataFrame, physics_df: pd.DataFrame
) -> list[dict[str, float | str | int]]:
    physics_lookup = physics_df.set_index("scenario_index")
    x_test = test[FEATURE_COLS].to_numpy()
    rows: list[dict[str, float | str | int]] = []
    for method, reps in rep_map.items():
        x_rep = reps[FEATURE_COLS].to_numpy()
        assign = np.linalg.norm(x_test[:, None, :] - x_rep[None, :, :], axis=2).argmin(axis=1)
        rep_indices = reps.iloc[assign]["scenario_index"].to_numpy(dtype=int)
        true_metrics = physics_lookup.loc[test["scenario_index"].to_numpy(dtype=int)]
        rep_metrics = physics_lookup.loc[rep_indices]
        rows.append(
            {
                "system": "DDRE-33-radial",
                "method": method,
                "min_voltage_mae_pu": float(
                    np.mean(np.abs(true_metrics["min_voltage_pu"].to_numpy() - rep_metrics["min_voltage_pu"].to_numpy()))
                ),
                "max_branch_loading_mae_pct": float(
                    np.mean(
                        np.abs(
                            true_metrics["max_branch_loading_pct"].to_numpy()
                            - rep_metrics["max_branch_loading_pct"].to_numpy()
                        )
                    )
                ),
                "feasible_share_gap": float(
                    np.mean(
                        np.abs(
                            true_metrics["feasible_step_share"].to_numpy()
                            - rep_metrics["feasible_step_share"].to_numpy()
                        )
                    )
                ),
                "daily_loss_mae_mwh": float(
                    np.mean(np.abs(true_metrics["daily_loss_mwh"].to_numpy() - rep_metrics["daily_loss_mwh"].to_numpy()))
                ),
                "true_feasible_share": float(true_metrics["feasible_step_share"].mean()),
                "rep_feasible_share": float(rep_metrics["feasible_step_share"].mean()),
                "true_min_voltage_mean": float(true_metrics["min_voltage_pu"].mean()),
                "rep_min_voltage_mean": float(rep_metrics["min_voltage_pu"].mean()),
            }
        )
    return rows


def summarize(rows_df: pd.DataFrame) -> pd.DataFrame:
    summary = (
        rows_df.groupby(["system", "method"], as_index=False)
        .agg(
            min_voltage_mae_pu=("min_voltage_mae_pu", "mean"),
            min_voltage_mae_std=("min_voltage_mae_pu", "std"),
            max_branch_loading_mae_pct=("max_branch_loading_mae_pct", "mean"),
            max_branch_loading_mae_std=("max_branch_loading_mae_pct", "std"),
            feasible_share_gap=("feasible_share_gap", "mean"),
            feasible_share_gap_std=("feasible_share_gap", "std"),
            daily_loss_mae_mwh=("daily_loss_mae_mwh", "mean"),
            daily_loss_mae_std=("daily_loss_mae_mwh", "std"),
            true_feasible_share=("true_feasible_share", "mean"),
            rep_feasible_share=("rep_feasible_share", "mean"),
            true_min_voltage_mean=("true_min_voltage_mean", "mean"),
            rep_min_voltage_mean=("rep_min_voltage_mean", "mean"),
        )
        .sort_values(["feasible_share_gap", "min_voltage_mae_pu", "daily_loss_mae_mwh"])
        .reset_index(drop=True)
    )
    for col in [c for c in summary.columns if c.endswith("_std")]:
        summary[col] = summary[col].fillna(0.0)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--data_dir", default="data")
    args = parser.parse_args()

    cfg = load_config(args.config)
    p = cfg["paths"]
    features = pd.read_csv(Path(p["interim"]) / "features.csv")

    physics_df = build_all_scenario_physics(args.data_dir)
    write_csv(physics_df, Path(p["tables"]) / "ddre33_scenario_physics.csv")

    seeds = [int(x) for x in cfg["analysis"]["multi_seeds"]]
    seed_rows: list[dict[str, float | str | int]] = []
    for seed in seeds:
        train, test = prepare_seeded_dataset(features, cfg, seed)
        rep_map = build_representative_maps(train, seed, cfg)
        result_rows = evaluate_direct_ddre33_validation(rep_map, test, physics_df)
        for row in result_rows:
            row["seed"] = seed
            seed_rows.append(row)

    seed_df = pd.DataFrame(seed_rows)
    summary_df = summarize(seed_df)
    write_csv(seed_df, Path(p["tables"]) / "ddre33_direct_validation_seed.csv")
    write_csv(summary_df, Path(p["tables"]) / "ddre33_direct_validation.csv")
    print("DDRE33_DIRECT_VALIDATION_DONE")


if __name__ == "__main__":
    main()
