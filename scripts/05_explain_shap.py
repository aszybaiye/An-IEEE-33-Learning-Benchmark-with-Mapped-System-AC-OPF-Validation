from __future__ import annotations

import argparse
from pathlib import Path
import sys

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.io_utils import load_config
from src.plotting import apply_publication_style, save_png_and_pdf


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    cfg = load_config(args.config)
    p = cfg["paths"]
    train = pd.read_csv(Path(p["interim"]) / "train_with_labels.csv")
    feature_cols = [
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
    x = train[feature_cols]
    y = train["xrfm_label"]
    model = RandomForestClassifier(n_estimators=250, random_state=cfg["seed"])
    model.fit(x, y)
    used_shap = False
    importance_df = None
    try:
        import shap

        apply_publication_style(1.0)
        explainer = shap.TreeExplainer(model)
        sv = explainer.shap_values(x, check_additivity=False)
        shap.summary_plot(sv, x, show=False, plot_type="bar")
        if isinstance(sv, list):
            mean_abs = np.mean([np.abs(v).mean(axis=0) for v in sv], axis=0)
        else:
            mean_abs = np.abs(sv).mean(axis=0)
        importance_df = pd.DataFrame({"feature": feature_cols, "importance": mean_abs})
        used_shap = True
    except ModuleNotFoundError:
        apply_publication_style(1.0)
        imp = pd.Series(model.feature_importances_, index=feature_cols).sort_values(ascending=True)
        plt.figure(figsize=(8, 5))
        imp.plot(kind="barh")
        plt.title("Feature Attribution Summary for Risk-Aware Selection")
        importance_df = pd.DataFrame({"feature": imp.index, "importance": imp.values})
    out_path = Path(p["figures"]) / "shap_summary.png"
    plt.tight_layout()
    save_png_and_pdf(plt.gcf(), str(out_path), p["pdf"])
    if importance_df is not None:
        importance_df.sort_values("importance", ascending=False).to_csv(
            Path(p["tables"]) / "shap_importance.csv", index=False
        )
    plt.close()
    print("SHAP_DONE", {"path": str(out_path), "used_shap": used_shap})


if __name__ == "__main__":
    main()
