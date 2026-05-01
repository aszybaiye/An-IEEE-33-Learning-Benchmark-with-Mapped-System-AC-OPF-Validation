from __future__ import annotations

import argparse
from pathlib import Path
import sys

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.io_utils import load_config
from src.plotting import (
    apply_publication_style,
    make_photo_text,
    plot_data_distribution,
    plot_ddre33_direct_validation,
    plot_distribution_opf_validation,
    plot_diagnostics,
    plot_opf_case_validation,
    plot_opf_reduction,
    plot_opf_reduction_repeated,
    plot_physical_validation,
    plot_penetration_curve,
    plot_scalability,
    plot_sensitivity_curves,
    plot_transfer_performance,
    save_png_and_pdf,
)


def plot_typical_profiles(data_dir: Path, out_path: Path, pdf_dir: Path | None = None) -> None:
    apply_publication_style(1.05)
    sample = pd.read_csv(data_dir / "1-Day Scenarios" / "scenario_001.csv")
    fig, axes = plt.subplots(2, 2, figsize=(11.0, 7.2), sharex=True)
    color_map = {
        "node_22_wind": "#1F77B4",
        "node_25_wind": "#5FA8D3",
        "node_18_PV": "#E07A5F",
        "node_33_PV": "#F2CC8F",
    }
    panel_map = {
        "node_22_wind": axes[0, 0],
        "node_25_wind": axes[0, 1],
        "node_18_PV": axes[1, 0],
        "node_33_PV": axes[1, 1],
    }
    title_map = {
        "node_22_wind": "Wind Node 22",
        "node_25_wind": "Wind Node 25",
        "node_18_PV": "PV Node 18",
        "node_33_PV": "PV Node 33",
    }
    for c in ["node_22_wind", "node_25_wind", "node_18_PV", "node_33_PV"]:
        marker = "o" if "wind" in c else "s"
        ax = panel_map[c]
        ax.plot(
            sample[c].to_numpy(),
            label=c,
            linewidth=2.2,
            color=color_map[c],
            marker=marker,
            markevery=8,
            markersize=4.5,
            alpha=0.95,
        )
        ax.set_title(title_map[c])
        ax.set_ylabel("Per-unit Output")
        ax.grid(axis="y", alpha=0.2, linewidth=0.8)
        ax.tick_params(width=1.2, length=4)
        ax.set_xticks([0, 24, 48, 72, 95])
        ax.set_xticklabels(["00:00", "06:00", "12:00", "18:00", "24:00"])
        ax.legend(frameon=False, loc="upper right")
    axes[1, 0].set_xlabel("15-min Step")
    axes[1, 1].set_xlabel("15-min Step")
    fig.suptitle("Typical Day Profiles", y=1.02)
    fig.tight_layout()
    save_png_and_pdf(fig, str(out_path), str(pdf_dir) if pdf_dir else None)
    plt.close(fig)


def plot_continual_curve(log_df: pd.DataFrame, out_path: Path, pdf_dir: Path | None = None) -> None:
    apply_publication_style(1.05)
    fig, ax = plt.subplots(figsize=(8.6, 4.8))
    ax.plot(
        log_df["round"],
        log_df["stability_score"],
        marker="o",
        linewidth=2.2,
        markersize=6,
        color="#2E5B9A",
        label="stability",
    )
    ax.plot(
        log_df["round"],
        log_df["adaptation_score"],
        marker="s",
        linewidth=2.2,
        markersize=6,
        color="#D95F5F",
        label="adaptation",
    )
    ax.set_xlabel("Round")
    ax.set_ylabel("Score")
    ax.set_title("Continual Update Curve")
    ax.legend()
    ax.grid(axis="y", alpha=0.2, linewidth=0.8)
    ax.tick_params(width=1.2, length=4)
    gap = (log_df["adaptation_score"] - log_df["stability_score"]).abs()
    idx = int(gap.idxmax())
    ax.annotate(
        "Largest divergence",
        xy=(log_df.loc[idx, "round"], log_df.loc[idx, "adaptation_score"]),
        xytext=(log_df.loc[idx, "round"] + 0.2, log_df.loc[idx, "adaptation_score"] + 0.12),
        arrowprops={"arrowstyle": "->", "linewidth": 1.2, "color": "#333333"},
        fontsize=10,
    )
    fig.tight_layout()
    save_png_and_pdf(fig, str(out_path), str(pdf_dir) if pdf_dir else None)
    plt.close(fig)


def plot_method_workflow(out_path: Path, pdf_dir: Path | None = None) -> None:
    apply_publication_style(1.0)
    fig, ax = plt.subplots(figsize=(11.5, 3.8))
    ax.axis("off")
    boxes = [
        (0.03, 0.35, 0.16, 0.32, "DDRE-33\nDaily Scenarios"),
        (0.24, 0.35, 0.18, 0.32, "Feature\nExtraction"),
        (0.47, 0.35, 0.18, 0.32, "Risk-Aware\nxRFM"),
        (0.70, 0.35, 0.18, 0.32, "SHAP-Guided\nInterpretation"),
    ]
    facecolors = ["#DCEAF7", "#E6F3E6", "#FDE6D8", "#EFE3F8"]
    for (x, y, w, h, text), fc in zip(boxes, facecolors):
        ax.add_patch(
            FancyBboxPatch(
                (x, y),
                w,
                h,
                boxstyle="round,pad=0.02,rounding_size=0.02",
                linewidth=1.5,
                edgecolor="#4A4A4A",
                facecolor=fc,
            )
        )
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=11, weight="bold")
    bottom_box = FancyBboxPatch(
        (0.38, 0.05),
        0.26,
        0.18,
        boxstyle="round,pad=0.02,rounding_size=0.02",
        linewidth=1.5,
        edgecolor="#4A4A4A",
        facecolor="#FFF6D8",
    )
    ax.add_patch(bottom_box)
    ax.text(0.51, 0.14, "Dual-Layer Library\nNormal + High-Risk Days", ha="center", va="center", fontsize=11, weight="bold")
    arrows = [
        ((0.19, 0.51), (0.24, 0.51)),
        ((0.42, 0.51), (0.47, 0.51)),
        ((0.65, 0.51), (0.70, 0.51)),
        ((0.56, 0.35), (0.56, 0.23)),
        ((0.78, 0.35), (0.60, 0.23)),
    ]
    for start, end in arrows:
        ax.add_patch(FancyArrowPatch(start, end, arrowstyle="->", mutation_scale=12, linewidth=1.4, color="#4A4A4A"))
    ax.text(0.90, 0.50, "Selection feedback\nfor risk-aware ranking", fontsize=10, ha="left", va="center")
    fig.tight_layout()
    save_png_and_pdf(fig, str(out_path), str(pdf_dir) if pdf_dir else None)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--data_dir", default="data")
    args = parser.parse_args()
    cfg = load_config(args.config)
    p = cfg["paths"]
    pdf_dir = Path(p["pdf"])
    pdf_dir.mkdir(parents=True, exist_ok=True)
    feat = pd.read_csv(Path(p["interim"]) / "features.csv")
    results = pd.read_csv(Path(p["tables"]) / "main_results.csv")
    logs = pd.read_csv(Path(p["interim"]) / "continual_logs.csv")
    k_df = pd.read_csv(Path(p["tables"]) / "k_sensitivity_results.csv")
    alpha_df = pd.read_csv(Path(p["tables"]) / "alpha_sensitivity_results.csv")
    penetration_df = pd.read_csv(Path(p["tables"]) / "penetration_results.csv")
    gamma_df = pd.read_csv(Path(p["tables"]) / "gamma_sensitivity_results.csv")
    convergence_df = pd.read_csv(Path(p["tables"]) / "convergence_results.csv")
    physical_df = pd.read_csv(Path(p["tables"]) / "physical_dispatch_results.csv")
    ddre33_direct_df = pd.read_csv(Path(p["tables"]) / "ddre33_direct_validation.csv")
    distribution_opf_path = Path(p["tables"]) / "distribution_opf_validation.csv"
    scalability_df = pd.read_csv(Path(p["tables"]) / "scalability_results.csv")
    opf_case_df = pd.read_csv(Path(p["tables"]) / "opf_case_summary.csv")
    opf_reduction_df = pd.read_csv(Path(p["tables"]) / "opf_reduction_results.csv")
    opf_reduction_repeated_df = pd.read_csv(Path(p["tables"]) / "opf_reduction_repeated_summary.csv")
    plot_data_distribution(feat, str(Path(p["figures"]) / "data_distribution.png"), str(pdf_dir))
    plot_transfer_performance(
        results, str(Path(p["figures"]) / "transfer_performance.png"), str(pdf_dir)
    )
    plot_typical_profiles(
        Path(args.data_dir), Path(p["figures"]) / "typical_day_profiles.png", pdf_dir
    )
    plot_continual_curve(logs, Path(p["figures"]) / "continual_update_curve.png", pdf_dir)
    plot_method_workflow(Path(p["figures"]) / "risk_workflow_diagram.png", pdf_dir)
    plot_sensitivity_curves(
        k_df,
        alpha_df,
        str(Path(p["figures"]) / "sensitivity_analysis.png"),
        str(pdf_dir),
    )
    plot_penetration_curve(
        penetration_df, str(Path(p["figures"]) / "penetration_stress_test.png"), str(pdf_dir)
    )
    plot_diagnostics(
        gamma_df,
        convergence_df,
        str(Path(p["figures"]) / "diagnostic_analysis.png"),
        str(pdf_dir),
    )
    plot_physical_validation(
        physical_df, str(Path(p["figures"]) / "physical_dispatch_validation.png"), str(pdf_dir)
    )
    plot_ddre33_direct_validation(
        ddre33_direct_df, str(Path(p["figures"]) / "ddre33_direct_validation.png"), str(pdf_dir)
    )
    if distribution_opf_path.exists():
        distribution_opf_df = pd.read_csv(distribution_opf_path)
        plot_distribution_opf_validation(
            distribution_opf_df, str(Path(p["figures"]) / "distribution_opf_validation.png"), str(pdf_dir)
        )
    plot_scalability(
        scalability_df, str(Path(p["figures"]) / "scalability_analysis.png"), str(pdf_dir)
    )
    plot_opf_case_validation(
        opf_case_df, str(Path(p["figures"]) / "opf_case_validation.png"), str(pdf_dir)
    )
    plot_opf_reduction(
        opf_reduction_df, str(Path(p["figures"]) / "opf_reduction_comparison.png"), str(pdf_dir)
    )
    plot_opf_reduction_repeated(
        opf_reduction_repeated_df,
        str(Path(p["figures"]) / "opf_reduction_repeated.png"),
        str(pdf_dir),
    )
    txt1 = "Training finished\nGenerated: features, models, tables, figures\nStatus: SUCCESS"
    txt2 = "Outputs tree\nOutputs/interim\nOutputs/models\nOutputs/tables\nOutputs/figures\nOutputs/photos"
    txt3 = "Key results\nBest method from main_results.csv\nCheck dispatch_error and extreme_miss"
    make_photo_text(txt1, str(Path(p["photos"]) / "photo_training_log.png"))
    make_photo_text(txt2, str(Path(p["photos"]) / "photo_outputs_tree.png"))
    make_photo_text(txt3, str(Path(p["photos"]) / "photo_key_results.png"))
    print("ASSETS_DONE")


if __name__ == "__main__":
    main()
