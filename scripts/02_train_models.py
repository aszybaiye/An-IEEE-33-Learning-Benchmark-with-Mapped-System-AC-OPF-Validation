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

from sklearn.cluster import KMeans, SpectralClustering

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.io_utils import load_config, save_json, write_csv
from src.xrfm import RiskAwareEmbedding


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    cfg = load_config(args.config)
    p = cfg["paths"]
    features = pd.read_csv(Path(p["interim"]) / "features.csv")
    train = features[features["subset"] == "train"].copy().reset_index(drop=True)
    cols = [
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
    x_train = train[cols].to_numpy()
    n_clusters = int(cfg["model"]["n_clusters"])
    kmeans = KMeans(n_clusters=n_clusters, random_state=cfg["seed"], n_init=20)
    train["kmeans_label"] = kmeans.fit_predict(x_train)
    spectral = SpectralClustering(
        n_clusters=n_clusters,
        random_state=cfg["seed"],
        affinity="nearest_neighbors",
        n_neighbors=12,
        assign_labels="kmeans",
    )
    train["spectral_label"] = spectral.fit_predict(x_train)
    xrfm = RiskAwareEmbedding(
        embedding_dim=int(cfg["model"]["embedding_dim"]),
        risk_alpha=float(cfg["model"]["risk_alpha"]),
    )
    emb = xrfm.fit_transform(x_train, train["risk_score"].to_numpy())
    km_emb = KMeans(n_clusters=n_clusters, random_state=cfg["seed"], n_init=20)
    train["xrfm_label"] = km_emb.fit_predict(emb)
    emb_df = pd.DataFrame(emb, columns=[f"z{i+1}" for i in range(emb.shape[1])])
    emb_df["scenario_index"] = train["scenario_index"].to_numpy()
    write_csv(train, Path(p["interim"]) / "train_with_labels.csv")
    write_csv(emb_df, Path(p["interim"]) / "embedding_train.csv")
    np.save(Path(p["models"]) / "xrfm_projection.npy", xrfm.proj)
    np.save(Path(p["models"]) / "xrfm_scaler_mean.npy", xrfm.scaler.mean_)
    np.save(Path(p["models"]) / "xrfm_scaler_scale.npy", xrfm.scaler.scale_)
    save_json(
        {
            "n_clusters": n_clusters,
            "embedding_dim": int(cfg["model"]["embedding_dim"]),
            "train_samples": int(len(train)),
        },
        Path(p["models"]) / "model_summary.json",
    )
    print("TRAIN_MODELS_DONE", {"train_samples": len(train), "n_clusters": n_clusters})


if __name__ == "__main__":
    main()
