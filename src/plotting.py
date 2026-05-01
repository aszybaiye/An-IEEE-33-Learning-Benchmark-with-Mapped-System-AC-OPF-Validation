from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

METHOD_PALETTE = {
    "xrfm_dual_library": "#1f4e79",
    "xrfm": "#4f81bd",
    "spectral": "#c0504d",
    "hierarchical": "#8064a2",
    "kmedoids": "#c27c0e",
    "kmeans": "#7f7f7f",
    "kmeans_feature": "#7f7f7f",
    "forward_feature": "#5b9bd5",
    "opf_sensitivity": "#c0504d",
    "opf_kkt_active_set": "#8064a2",
}

METHOD_LABELS = {
    "xrfm_dual_library": "Dual-layer xRFM",
    "xrfm": "Single-layer xRFM",
    "spectral": "Spectral",
    "hierarchical": "Hierarchical",
    "kmedoids": "K-medoids",
    "kmeans": "K-means",
    "kmeans_feature": "K-means feature",
    "forward_feature": "Forward feature",
    "opf_sensitivity": "OPF sensitivity",
    "opf_kkt_active_set": "KKT-inspired",
}


def apply_publication_style(font_scale: float = 1.0) -> None:
    base = 12 * font_scale
    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["DejaVu Sans", "Arial", "Liberation Sans"],
            "font.size": base,
            "axes.titlesize": base * 1.1,
            "axes.labelsize": base,
            "xtick.labelsize": base * 0.9,
            "ytick.labelsize": base * 0.9,
            "legend.fontsize": base * 0.9,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.linewidth": 1.6,
            "axes.edgecolor": "#333333",
            "axes.axisbelow": True,
            "grid.color": "#C7CDD4",
            "grid.linestyle": "-",
            "grid.linewidth": 0.8,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "savefig.bbox": "tight",
            "savefig.pad_inches": 0.05,
        }
    )


def _display_method(name: str) -> str:
    return METHOD_LABELS.get(name, str(name))


def _with_method_labels(df: pd.DataFrame, method_col: str = "method") -> pd.DataFrame:
    plot_df = df.copy()
    if method_col in plot_df.columns:
        plot_df["method_label"] = plot_df[method_col].map(_display_method)
    return plot_df


def _palette_for_labels(labels: list[str]) -> dict[str, str]:
    palette = {}
    for raw, label in METHOD_LABELS.items():
        if label in labels:
            palette[label] = METHOD_PALETTE.get(raw, "#4C78A8")
    for label in labels:
        palette.setdefault(label, "#4C78A8")
    return palette


def _style_axes(ax: plt.Axes, grid_axis: str = "y") -> None:
    ax.grid(axis=grid_axis, alpha=0.35, linewidth=0.8)
    ax.tick_params(width=1.2, length=4, color="#333333")
    for spine_name in ["left", "bottom"]:
        if spine_name in ax.spines:
            ax.spines[spine_name].set_color("#333333")
            ax.spines[spine_name].set_linewidth(1.2)


def _rotate_xticks(ax: plt.Axes, angle: float = 15) -> None:
    ax.tick_params(axis="x", labelrotation=angle)
    for tick in ax.get_xticklabels():
        tick.set_ha("right")


def _annotate_bars(ax: plt.Axes, fmt: str = "{:.3f}", fraction: float = 0.02) -> None:
    ymin, ymax = ax.get_ylim()
    pad = max((ymax - ymin) * fraction, 1e-6)
    for patch in ax.patches:
        height = patch.get_height()
        if pd.isna(height):
            continue
        ax.text(
            patch.get_x() + patch.get_width() / 2,
            height + pad,
            fmt.format(height),
            ha="center",
            va="bottom",
            fontsize=9,
            color="#2F2F2F",
        )


def _add_errorbars_from_column(
    ax: plt.Axes, df: pd.DataFrame, order: list[str], y_col: str, err_col: str
) -> None:
    labeled = df.set_index("method_label").loc[order].reset_index()
    for patch, (_, row) in zip(ax.patches, labeled.iterrows()):
        x = patch.get_x() + patch.get_width() / 2
        ax.errorbar(
            x=x,
            y=row[y_col],
            yerr=row[err_col],
            fmt="none",
            ecolor="#2F2F2F",
            elinewidth=1.2,
            capsize=3.5,
            capthick=1.2,
            zorder=4,
        )


def save_png_and_pdf(fig: plt.Figure, out_path: str, pdf_dir: str | None = None) -> None:
    png_path = Path(out_path)
    png_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(
        png_path,
        dpi=360,
        facecolor="white",
        edgecolor="none",
        bbox_inches="tight",
        pad_inches=0.24,
    )
    if pdf_dir:
        pdf_path = Path(pdf_dir)
        pdf_path.mkdir(parents=True, exist_ok=True)
        fig.savefig(
            pdf_path / f"{png_path.stem}.pdf",
            facecolor="white",
            edgecolor="none",
            bbox_inches="tight",
            pad_inches=0.12,
        )
    else:
        fig.savefig(
            png_path.with_suffix(".pdf"),
            facecolor="white",
            edgecolor="none",
            bbox_inches="tight",
            pad_inches=0.12,
        )


def plot_data_distribution(df: pd.DataFrame, out_path: str, pdf_dir: str | None = None) -> None:
    apply_publication_style(1.05)
    fig, axes = plt.subplots(1, 2, figsize=(12.8, 4.6))
    low_thr = float(df["risk_score"].quantile(0.2))
    high_thr = float(df["risk_score"].quantile(0.8))
    sns.histplot(df["risk_score"], kde=True, ax=axes[0], color="#2E5B9A", edgecolor="white")
    axes[0].set_title("Risk Score Distribution")
    axes[0].set_xlabel("Risk score")
    axes[0].set_ylabel("Count")
    axes[0].axvspan(df["risk_score"].min(), low_thr, color="#8EC6D1", alpha=0.18)
    axes[0].axvspan(high_thr, df["risk_score"].max(), color="#D95F5F", alpha=0.16)
    axes[0].axvline(low_thr, color="#2E5B9A", linestyle="--", linewidth=1.8)
    axes[0].axvline(high_thr, color="#B22222", linestyle="--", linewidth=1.8)
    ymax = axes[0].get_ylim()[1]
    axes[0].text(low_thr, ymax * 0.92, "Low-risk threshold", ha="right", va="top", fontsize=10)
    axes[0].text(high_thr, ymax * 0.82, "High-risk threshold", ha="left", va="top", fontsize=10)
    palette_all = ["#8EC6D1", "#2E5B9A", "#D95F5F", "#7A5195", "#4C9A2A", "#C97B00"]
    pv_count = int(df["pv_label"].nunique()) if "pv_label" in df.columns else 3
    sns.countplot(
        data=df,
        x="wind_label",
        hue="pv_label",
        ax=axes[1],
        palette=palette_all[: max(1, pv_count)],
    )
    axes[1].set_title("Label Distribution")
    axes[1].set_xlabel("Wind label")
    axes[1].set_ylabel("Count")
    axes[1].legend(title="PV label", frameon=False, ncol=3, loc="upper right")
    for ax in axes:
        ax.grid(axis="y", alpha=0.18, linewidth=0.8)
        ax.tick_params(width=1.2, length=4)
    fig.tight_layout()
    save_png_and_pdf(fig, out_path, pdf_dir)
    plt.close(fig)


def plot_transfer_performance(
    results: pd.DataFrame, out_path: str, pdf_dir: str | None = None
) -> None:
    apply_publication_style(1.05)
    fig, ax = plt.subplots(figsize=(9.2, 4.8))
    plot_df = _with_method_labels(results)
    order = plot_df.sort_values("dispatch_error")["method_label"].tolist()
    palette = _palette_for_labels(order)
    sns.barplot(
        data=plot_df,
        x="method_label",
        y="dispatch_error",
        hue="method_label",
        order=order,
        palette=palette,
        dodge=False,
        legend=False,
        ax=ax,
    )
    ax.set_title("Transfer Dispatch Error")
    ax.set_xlabel("Method")
    ax.set_ylabel("Dispatch error")
    ymin = float(results["dispatch_error"].min())
    ymax = float(results["dispatch_error"].max())
    pad = max((ymax - ymin) * 0.3, 0.03)
    ax.set_ylim(max(0.0, ymin - pad * 0.2), ymax + pad)
    _style_axes(ax, "y")
    _rotate_xticks(ax, 15)
    _annotate_bars(ax, "{:.3f}", 0.03)
    if "dispatch_error_std" in results.columns:
        _add_errorbars_from_column(ax, plot_df, order, "dispatch_error", "dispatch_error_std")
    fig.tight_layout()
    save_png_and_pdf(fig, out_path, pdf_dir)
    plt.close(fig)


def plot_sensitivity_curves(
    k_df: pd.DataFrame, alpha_df: pd.DataFrame, out_path: str, pdf_dir: str | None = None
) -> None:
    apply_publication_style(1.0)
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.4))
    axes[0].errorbar(
        k_df["k"],
        k_df["dispatch_error_mean"],
        yerr=k_df["dispatch_error_std"],
        color="#2E5B9A",
        marker="o",
        linewidth=2.1,
        capsize=4,
    )
    axes[0].set_title("Sensitivity to Number of Clusters")
    axes[0].set_xlabel("K")
    axes[0].set_ylabel("Transfer dispatch error")
    axes[1].errorbar(
        alpha_df["alpha"],
        alpha_df["dispatch_error_mean"],
        yerr=alpha_df["dispatch_error_std"],
        color="#D95F5F",
        marker="s",
        linewidth=2.1,
        capsize=4,
    )
    axes[1].set_title("Sensitivity to Risk Weight")
    axes[1].set_xlabel("Risk weight α")
    axes[1].set_ylabel("Transfer dispatch error")
    for ax in axes:
        _style_axes(ax, "y")
    fig.tight_layout()
    save_png_and_pdf(fig, out_path, pdf_dir)
    plt.close(fig)


def plot_penetration_curve(df: pd.DataFrame, out_path: str, pdf_dir: str | None = None) -> None:
    apply_publication_style(1.0)
    fig, ax = plt.subplots(figsize=(6.8, 4.5))
    x = df["penetration_level"] * 100
    ax.errorbar(
        x,
        df["dispatch_error_mean"],
        yerr=df["dispatch_error_std"],
        color="#7A5195",
        marker="D",
        linewidth=2.1,
        capsize=4,
    )
    ax.set_title("Renewable Penetration Stress Test")
    ax.set_xlabel("Renewable penetration (%)")
    ax.set_ylabel("Transfer dispatch error")
    _style_axes(ax, "y")
    fig.tight_layout()
    save_png_and_pdf(fig, out_path, pdf_dir)
    plt.close(fig)


def plot_diagnostics(
    gamma_df: pd.DataFrame, convergence_df: pd.DataFrame, out_path: str, pdf_dir: str | None = None
) -> None:
    apply_publication_style(1.0)
    fig, axes = plt.subplots(1, 2, figsize=(11.2, 4.4))
    axes[0].errorbar(
        gamma_df["gamma"],
        gamma_df["dispatch_error_mean"],
        yerr=gamma_df["dispatch_error_std"],
        color="#4C9A2A",
        marker="^",
        linewidth=2.1,
        capsize=4,
    )
    axes[0].set_title("Sensitivity to Drift Factor γ")
    axes[0].set_xlabel("γ")
    axes[0].set_ylabel("Transfer dispatch error")
    axes[1].plot(
        convergence_df["iteration"],
        convergence_df["objective_value"],
        color="#C97B00",
        marker="o",
        linewidth=2.1,
    )
    axes[1].set_title("Empirical Convergence of Alternating Updates")
    axes[1].set_xlabel("Iteration")
    axes[1].set_ylabel("Objective value")
    for ax in axes:
        _style_axes(ax, "y")
    fig.tight_layout()
    save_png_and_pdf(fig, out_path, pdf_dir)
    plt.close(fig)


def plot_physical_validation(df: pd.DataFrame, out_path: str, pdf_dir: str | None = None) -> None:
    apply_publication_style(1.0)
    fig, ax = plt.subplots(figsize=(9.6, 4.8))
    plot_df = _with_method_labels(df)
    if {"dispatch_cost_gap_std", "full_dispatch_cost"}.issubset(plot_df.columns):
        plot_df["dispatch_cost_gap_ratio_std"] = (
            plot_df["dispatch_cost_gap_std"] / plot_df["full_dispatch_cost"].clip(lower=1e-9)
        )
    plot_df["system_method"] = plot_df["system"] + "\n" + plot_df["method_label"]
    order = (
        plot_df.sort_values(["system", "dispatch_cost_gap_ratio"])["system_method"].tolist()
    )
    sns.barplot(
        data=plot_df,
        x="system_method",
        y="dispatch_cost_gap_ratio",
        hue="method_label",
        order=order,
        dodge=False,
        palette=_palette_for_labels(plot_df["method_label"].unique().tolist()),
        legend=False,
        ax=ax,
    )
    ax.set_title("Feeder-Aware Dispatch Cost Validation")
    ax.set_xlabel("System and method")
    ax.set_ylabel("Relative dispatch-cost gap")
    _style_axes(ax, "y")
    _rotate_xticks(ax, 18)
    _annotate_bars(ax, "{:.3f}", 0.025)
    if "dispatch_cost_gap_ratio_std" in plot_df.columns:
        _add_errorbars_from_column(
            ax,
            plot_df.rename(columns={"system_method": "method_label"}),
            order,
            "dispatch_cost_gap_ratio",
            "dispatch_cost_gap_ratio_std",
        )
    fig.tight_layout()
    save_png_and_pdf(fig, out_path, pdf_dir)
    plt.close(fig)


def plot_ddre33_direct_validation(df: pd.DataFrame, out_path: str, pdf_dir: str | None = None) -> None:
    apply_publication_style(0.98)
    fig, axes = plt.subplots(1, 2, figsize=(11.6, 4.6))
    plot_df = _with_method_labels(df)
    order = plot_df.sort_values("min_voltage_mae_pu")["method_label"].tolist()
    palette = _palette_for_labels(order)
    sns.barplot(
        data=plot_df,
        x="method_label",
        y="min_voltage_mae_pu",
        hue="method_label",
        dodge=False,
        order=order,
        palette=palette,
        legend=False,
        ax=axes[0],
    )
    axes[0].set_title("DDRE-33 Voltage Preservation Error")
    axes[0].set_xlabel("Method")
    axes[0].set_ylabel("Mean absolute error of daily min voltage (p.u.)", labelpad=10)

    sns.barplot(
        data=plot_df,
        x="method_label",
        y="max_branch_loading_mae_pct",
        hue="method_label",
        dodge=False,
        order=order,
        palette=palette,
        legend=False,
        ax=axes[1],
    )
    axes[1].set_title("DDRE-33 Branch-Loading Preservation Error")
    axes[1].set_xlabel("Method")
    axes[1].set_ylabel("Mean absolute error of max branch loading (%)", labelpad=12)

    _add_errorbars_from_column(axes[0], plot_df, order, "min_voltage_mae_pu", "min_voltage_mae_std")
    _annotate_bars(axes[0], "{:.4f}", 0.03)
    _add_errorbars_from_column(
        axes[1],
        plot_df,
        order,
        "max_branch_loading_mae_pct",
        "max_branch_loading_mae_std",
    )
    _annotate_bars(axes[1], "{:.2f}", 0.02)
    for ax in axes:
        _style_axes(ax, "y")
        _rotate_xticks(ax, 18)
    fig.subplots_adjust(left=0.11, right=0.985, bottom=0.24, top=0.88, wspace=0.20)
    save_png_and_pdf(fig, out_path, pdf_dir)
    plt.close(fig)


def plot_distribution_opf_validation(df: pd.DataFrame, out_path: str, pdf_dir: str | None = None) -> None:
    apply_publication_style(0.98)
    fig, axes = plt.subplots(1, 2, figsize=(12.0, 4.8))
    plot_df = _with_method_labels(df)
    plot_df["system_method"] = plot_df["system"] + " | " + plot_df["method_label"]
    order = (
        plot_df.sort_values(["system", "objective_mape_pct"])[["system_method"]]
        .drop_duplicates()["system_method"]
        .tolist()
    )
    palette = _palette_for_labels(plot_df["method_label"].unique().tolist())
    system_palette = {row["system_method"]: palette[row["method_label"]] for _, row in plot_df.iterrows()}
    sns.barplot(
        data=plot_df,
        x="system_method",
        y="objective_mape_pct",
        order=order,
        palette=system_palette,
        ax=axes[0],
    )
    axes[0].set_title("Distribution AC-OPF Objective Error")
    axes[0].set_xlabel("System and method")
    axes[0].set_ylabel("Objective MAPE (%)")

    sns.barplot(
        data=plot_df,
        x="system_method",
        y="min_voltage_mae_pu",
        order=order,
        palette=system_palette,
        ax=axes[1],
    )
    axes[1].set_title("Distribution AC-OPF Voltage Preservation Error")
    axes[1].set_xlabel("System and method")
    axes[1].set_ylabel("Mean absolute error of minimum voltage (p.u.)")

    _add_errorbars_from_column(axes[0], plot_df.rename(columns={"system_method": "method_label"}), order, "objective_mape_pct", "objective_mape_std")
    _annotate_bars(axes[0], "{:.2f}", 0.03)
    _add_errorbars_from_column(axes[1], plot_df.rename(columns={"system_method": "method_label"}), order, "min_voltage_mae_pu", "min_voltage_mae_std")
    _annotate_bars(axes[1], "{:.4f}", 0.03)
    for ax in axes:
        _style_axes(ax, "y")
        _rotate_xticks(ax, 18)
    fig.tight_layout()
    save_png_and_pdf(fig, out_path, pdf_dir)
    plt.close(fig)


def plot_scalability(df: pd.DataFrame, out_path: str, pdf_dir: str | None = None) -> None:
    apply_publication_style(1.0)
    fig, axes = plt.subplots(1, 2, figsize=(11.2, 4.4))
    n_df = df[df["study_axis"] == "n_scenarios"]
    d_df = df[df["study_axis"] == "feature_dim"]
    axes[0].plot(n_df["value"], n_df["runtime_seconds"], color="#2E5B9A", marker="o", linewidth=2.2)
    axes[0].set_title("Runtime vs Number of Scenarios")
    axes[0].set_xlabel("Number of scenarios")
    axes[0].set_ylabel("Runtime (s)")
    axes[1].plot(d_df["value"], d_df["runtime_seconds"], color="#D95F5F", marker="s", linewidth=2.2)
    axes[1].set_title("Runtime vs Feature Dimension")
    axes[1].set_xlabel("Feature dimension")
    axes[1].set_ylabel("Runtime (s)")
    for ax in axes:
        _style_axes(ax, "y")
    fig.tight_layout()
    save_png_and_pdf(fig, out_path, pdf_dir)
    plt.close(fig)


def plot_opf_case_validation(df: pd.DataFrame, out_path: str, pdf_dir: str | None = None) -> None:
    apply_publication_style(1.0)
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.4))
    case_order = df.sort_values("case_name")["case_name"].tolist()
    sns.barplot(data=df, x="case_name", y="convergence_rate", order=case_order, color="#2E5B9A", ax=axes[0])
    axes[0].set_title("AC-OPF Convergence Rate")
    axes[0].set_xlabel("Test case")
    axes[0].set_ylabel("Convergence rate")
    axes[0].set_ylim(0.0, 1.05)
    for patch, (_, row) in zip(axes[0].patches, df.set_index("case_name").loc[case_order].reset_index().iterrows()):
        axes[0].text(
            patch.get_x() + patch.get_width() / 2,
            row["convergence_rate"] + 0.02,
            f"{row['convergence_rate']:.2f}",
            ha="center",
            va="bottom",
            fontsize=10,
        )
    sns.barplot(
        data=df, x="case_name", y="mean_power_balance_residual_mw", order=case_order, color="#D95F5F", ax=axes[1]
    )
    axes[1].set_title("Explicit Constraint Residual")
    axes[1].set_xlabel("Test case")
    axes[1].set_ylabel("Mean power-balance residual (MW)")
    for ax in axes:
        _style_axes(ax, "y")
    _annotate_bars(axes[1], "{:.2e}", 0.04)
    fig.tight_layout()
    save_png_and_pdf(fig, out_path, pdf_dir)
    plt.close(fig)


def plot_opf_reduction(df: pd.DataFrame, out_path: str, pdf_dir: str | None = None) -> None:
    apply_publication_style(0.95)
    fig, axes = plt.subplots(1, 2, figsize=(12.2, 4.6))
    plot_df = _with_method_labels(df)
    plot_df["selection_label"] = plot_df["case_name"] + " | K=" + plot_df["selected_count"].astype(str)
    order = (
        plot_df[["case_name", "selected_count", "selection_label"]]
        .drop_duplicates()
        .sort_values(["case_name", "selected_count"])["selection_label"]
        .tolist()
    )
    hue_order = [label for label in METHOD_LABELS.values() if label in plot_df["method_label"].unique().tolist()]
    sns.barplot(
        data=plot_df,
        x="selection_label",
        y="objective_mape_pct",
        hue="method_label",
        order=order,
        hue_order=hue_order,
        palette=_palette_for_labels(hue_order),
        ax=axes[0],
    )
    axes[0].set_title("OPF Objective Error After Scenario Reduction")
    axes[0].set_xlabel("Case and retained scenario count")
    axes[0].set_ylabel("Objective MAPE (%)")
    sns.barplot(
        data=plot_df,
        x="selection_label",
        y="time_saving_ratio",
        hue="method_label",
        order=order,
        hue_order=hue_order,
        palette=_palette_for_labels(hue_order),
        ax=axes[1],
    )
    axes[1].set_title("AC-OPF Time Saving Ratio")
    axes[1].set_xlabel("Case and retained scenario count")
    axes[1].set_ylabel("Full OPF time / reduced OPF time")
    for ax in axes:
        _style_axes(ax, "y")
        _rotate_xticks(ax, 20)
    handles, labels = axes[0].get_legend_handles_labels()
    axes[0].legend(handles, labels, frameon=False, fontsize=9)
    axes[1].legend_.remove()
    fig.tight_layout()
    save_png_and_pdf(fig, out_path, pdf_dir)
    plt.close(fig)


def plot_opf_reduction_repeated(df: pd.DataFrame, out_path: str, pdf_dir: str | None = None) -> None:
    apply_publication_style(0.95)
    fig, axes = plt.subplots(1, 2, figsize=(12.2, 4.8))
    plot_df = _with_method_labels(df)
    plot_df["selection_label"] = plot_df["case_name"] + " | K=" + plot_df["selected_count"].astype(str)
    order = (
        plot_df[["case_name", "selected_count", "selection_label"]]
        .drop_duplicates()
        .sort_values(["case_name", "selected_count"])["selection_label"]
        .tolist()
    )
    hue_order = [label for label in METHOD_LABELS.values() if label in plot_df["method_label"].unique().tolist()]
    sns.barplot(
        data=plot_df,
        x="selection_label",
        y="objective_mape_pct_mean",
        hue="method_label",
        order=order,
        hue_order=hue_order,
        palette=_palette_for_labels(hue_order),
        ax=axes[0],
    )
    axes[0].set_title("Repeated-Sampling OPF Objective Error")
    axes[0].set_xlabel("Case and retained scenario count")
    axes[0].set_ylabel("Objective MAPE mean (%)")
    sns.barplot(
        data=plot_df,
        x="selection_label",
        y="time_saving_ratio_mean",
        hue="method_label",
        order=order,
        hue_order=hue_order,
        palette=_palette_for_labels(hue_order),
        ax=axes[1],
    )
    axes[1].set_title("Repeated-Sampling OPF Time Saving")
    axes[1].set_xlabel("Case and retained scenario count")
    axes[1].set_ylabel("Time-saving ratio mean")
    for ax in axes:
        _style_axes(ax, "y")
        _rotate_xticks(ax, 20)
    objective_ordered = plot_df.set_index(["selection_label", "method_label"]).loc[
        [(sel, method) for sel in order for method in hue_order if (sel, method) in plot_df.set_index(["selection_label", "method_label"]).index]
    ].reset_index()
    time_ordered = objective_ordered
    for patch, (_, row) in zip(axes[0].patches, objective_ordered.iterrows()):
        x = patch.get_x() + patch.get_width() / 2
        axes[0].errorbar(
            x=x,
            y=row["objective_mape_pct_mean"],
            yerr=row["objective_mape_pct_ci95"],
            fmt="none",
            ecolor="#2F2F2F",
            elinewidth=1.1,
            capsize=3,
            capthick=1.1,
            zorder=4,
        )
    for patch, (_, row) in zip(axes[1].patches, time_ordered.iterrows()):
        x = patch.get_x() + patch.get_width() / 2
        axes[1].errorbar(
            x=x,
            y=row["time_saving_ratio_mean"],
            yerr=row["time_saving_ratio_ci95"],
            fmt="none",
            ecolor="#2F2F2F",
            elinewidth=1.1,
            capsize=3,
            capthick=1.1,
            zorder=4,
        )
    handles, labels = axes[0].get_legend_handles_labels()
    axes[0].legend(handles, labels, frameon=False, fontsize=9)
    axes[1].legend_.remove()
    fig.tight_layout()
    save_png_and_pdf(fig, out_path, pdf_dir)
    plt.close(fig)


def make_photo_text(text: str, out_path: str) -> None:
    fig, ax = plt.subplots(figsize=(11, 4))
    ax.text(0.01, 0.98, text, va="top", ha="left", fontsize=10, family="monospace")
    ax.axis("off")
    fig.tight_layout()
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=220)
    plt.close(fig)
