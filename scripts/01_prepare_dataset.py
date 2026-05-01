from __future__ import annotations

import argparse
from pathlib import Path
import sys

import numpy as np
import pandas as pd

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.features import apply_learned_risk_score, learn_risk_weights, risk_score, scenario_feature_row
from src.io_utils import ensure_dirs, load_config, save_json, write_csv
from src.split import split_dataset


def collect_daily_features(data_dir: Path) -> pd.DataFrame:
    day_dir = data_dir / "1-Day Scenarios"
    labels = pd.read_csv(day_dir / "scenario_labels.csv")
    rows: list[dict[str, float | int]] = []
    for i in range(1, 201):
        f = day_dir / f"scenario_{i:03d}.csv"
        df = pd.read_csv(f)
        feat = scenario_feature_row(df)
        feat["risk_score"] = risk_score(df)
        feat["scenario_index"] = i
        rows.append(feat)
    features = pd.DataFrame(rows)
    merged = features.merge(labels, on="scenario_index", how="left")
    merged["stratify_tag"] = merged["wind_label"].astype(str) + "_" + merged["pv_label"].astype(str)
    return merged


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--data_dir", default="data")
    args = parser.parse_args()

    cfg = load_config(args.config)
    p = cfg["paths"]
    ensure_dirs([p["outputs"], p["interim"], p["models"], p["tables"], p["figures"], p["photos"], p["pdf"]])
    df = collect_daily_features(Path(args.data_dir))
    split_cfg = cfg["split"]
    splits = split_dataset(
        df,
        train_ratio=split_cfg["train"],
        val_ratio=split_cfg["val"],
        seed=cfg["seed"],
        stratify_cols=split_cfg["stratify_cols"],
    )
    df["subset"] = "train"
    df.loc[df["scenario_index"].isin(splits.val["scenario_index"]), "subset"] = "val"
    df.loc[df["scenario_index"].isin(splits.test["scenario_index"]), "subset"] = "test"
    train_df = df[df["subset"] == "train"].copy()
    weights = learn_risk_weights(train_df)
    df = apply_learned_risk_score(df, weights)
    df["risk_weight_1"] = float(weights[0])
    df["risk_weight_2"] = float(weights[1])
    df["risk_weight_3"] = float(weights[2])
    df["risk_weight_4"] = float(weights[3])
    write_csv(df, Path(p["interim"]) / "features.csv")
    split_meta = {
        "seed": cfg["seed"],
        "train_count": int(np.sum(df["subset"] == "train")),
        "val_count": int(np.sum(df["subset"] == "val")),
        "test_count": int(np.sum(df["subset"] == "test")),
        "risk_weights": [float(x) for x in weights],
    }
    save_json(split_meta, Path(p["interim"]) / "split_meta.json")
    print("PREPARE_DONE", split_meta)


if __name__ == "__main__":
    main()
