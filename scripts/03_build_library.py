from __future__ import annotations

import argparse
from pathlib import Path
import sys

import pandas as pd

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.io_utils import load_config, write_csv
from src.library import build_dual_library


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    cfg = load_config(args.config)
    p = cfg["paths"]
    train = pd.read_csv(Path(p["interim"]) / "train_with_labels.csv")
    emb = pd.read_csv(Path(p["interim"]) / "embedding_train.csv")
    z_cols = [c for c in emb.columns if c.startswith("z")]
    train = train.merge(emb, on="scenario_index", how="left")
    embedding = train[z_cols].to_numpy()
    normal, risk = build_dual_library(
        train,
        embedding,
        train["xrfm_label"].to_numpy(),
        float(cfg["model"]["risk_quantile"]),
        float(cfg["model"].get("ood_quantile", 0.98)),
        int(cfg["model"].get("ood_min_count", 2)),
    )
    write_csv(normal, Path(p["interim"]) / "library_normal.csv")
    write_csv(risk, Path(p["interim"]) / "library_risk.csv")
    print("BUILD_LIBRARY_DONE", {"normal": len(normal), "risk": len(risk)})


if __name__ == "__main__":
    main()
