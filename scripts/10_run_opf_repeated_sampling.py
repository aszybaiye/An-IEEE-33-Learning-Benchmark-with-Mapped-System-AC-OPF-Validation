from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys

import pandas as pd

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.io_utils import load_config, write_csv
from src.opf_utils import (
    evaluate_reduction_method,
    run_case_opf,
    sample_opf_scenarios,
    summarize_reduction_best,
    summarize_reduction_results,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--repeats", type=int, default=None)
    args = parser.parse_args()

    cfg = load_config(args.config)
    p = cfg["paths"]
    opf_cfg = cfg.get("opf", {})
    case_names = [str(x) for x in opf_cfg.get("case_names", ["case30", "case118"])]
    sample_size = int(opf_cfg.get("scenario_sample_size", 18))
    reduction_sizes = [int(x) for x in opf_cfg.get("reduction_sizes", [4, 8, 12])]
    base_seed = int(opf_cfg.get("seed", cfg.get("seed", 2026)))
    repeated_sampling_count = int(args.repeats or opf_cfg.get("repeated_sampling_count", 5))
    repeated_sampling_seeds = [base_seed + i for i in range(repeated_sampling_count)]
    methods = ["kmeans_feature", "forward_feature", "opf_sensitivity", "opf_kkt_active_set"]

    features = pd.read_csv(Path(p["interim"]) / "features.csv")

    repeated_case_frames = []
    repeated_rows = []
    for sample_id, sample_seed in enumerate(repeated_sampling_seeds, start=1):
        scenarios_i = sample_opf_scenarios(features, sample_size=sample_size, seed=sample_seed)
        scenarios_i["sample_id"] = sample_id
        scenarios_i["sample_seed"] = sample_seed
        write_csv(scenarios_i, Path(p["tables"]) / f"opf_scenarios_repeated_sample_{sample_id}.csv")
        for case_name in case_names:
            case_i = run_case_opf(case_name, scenarios_i)
            case_i["sample_id"] = sample_id
            case_i["sample_seed"] = sample_seed
            repeated_case_frames.append(case_i)
            case_conv = case_i[case_i["converged"]].reset_index(drop=True)
            for size in reduction_sizes:
                for method in methods:
                    row = evaluate_reduction_method(
                        case_conv,
                        method=method,
                        selected_count=size,
                        seed=sample_seed,
                    )
                    row["sample_id"] = sample_id
                    row["sample_seed"] = sample_seed
                    repeated_rows.append(row)

    repeated_case_df = pd.concat(repeated_case_frames, ignore_index=True)
    repeated_reduction_df = pd.DataFrame(repeated_rows)
    repeated_summary_df = summarize_reduction_results(repeated_reduction_df)
    repeated_best_df = summarize_reduction_best(repeated_summary_df)

    write_csv(repeated_case_df, Path(p["tables"]) / "opf_case_results_repeated.csv")
    write_csv(repeated_reduction_df, Path(p["tables"]) / "opf_reduction_repeated_results.csv")
    write_csv(repeated_summary_df, Path(p["tables"]) / "opf_reduction_repeated_summary.csv")
    write_csv(repeated_best_df, Path(p["tables"]) / "opf_reduction_repeated_best.csv")
    print(
        "OPF_REPEATED_SAMPLING_DONE",
        {
            "repeats": repeated_sampling_count,
            "cases": case_names,
            "sample_size": sample_size,
            "rows": len(repeated_reduction_df),
        },
    )


if __name__ == "__main__":
    main()
