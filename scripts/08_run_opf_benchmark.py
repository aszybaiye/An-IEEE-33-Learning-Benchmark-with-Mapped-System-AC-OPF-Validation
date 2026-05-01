from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys
import traceback

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
    summarize_case_results,
    summarize_reduction_best,
    summarize_reduction_results,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    cfg = load_config(args.config)
    p = cfg["paths"]
    opf_cfg = cfg.get("opf", {})
    case_names = [str(x) for x in opf_cfg.get("case_names", ["case30", "case118"])]
    sample_size = int(opf_cfg.get("scenario_sample_size", 60))
    reduction_sizes = [int(x) for x in opf_cfg.get("reduction_sizes", [6, 10, 14])]
    seed = int(opf_cfg.get("seed", cfg.get("seed", 2026)))
    repeated_sampling_count = int(opf_cfg.get("repeated_sampling_count", 5))
    repeated_sampling_seeds = [seed + i for i in range(repeated_sampling_count)]
    features = pd.read_csv(Path(p["interim"]) / "features.csv")
    log_path = Path(p["tables"]) / "opf_debug.log"
    with log_path.open("w", encoding="utf-8") as log:
        try:
            log.write("start\n")
            scenarios = sample_opf_scenarios(features, sample_size=sample_size, seed=seed)
            write_csv(scenarios, Path(p["tables"]) / "opf_scenarios.csv")
            log.write(f"scenarios:{len(scenarios)}\n")

            case_frames = []
            for case_name in case_names:
                log.write(f"run_case:{case_name}\n")
                case_df = run_case_opf(case_name, scenarios)
                case_frames.append(case_df)
                write_csv(case_df, Path(p["tables"]) / f"opf_case_results_{case_name}.csv")
                log.write(f"case_done:{case_name}:{len(case_df)}\n")
            opf_detail = pd.concat(case_frames, ignore_index=True)
            write_csv(opf_detail, Path(p["tables"]) / "opf_case_results.csv")
            log.write("detail_written\n")

            summary = summarize_case_results(opf_detail)
            write_csv(summary, Path(p["tables"]) / "opf_case_summary.csv")
            log.write("summary_written\n")

            reduction_rows = []
            methods = ["kmeans_feature", "forward_feature", "opf_sensitivity", "opf_kkt_active_set"]
            converged = opf_detail[opf_detail["converged"]].copy()
            for case_name, case_df in converged.groupby("case_name", sort=False):
                case_df = case_df.reset_index(drop=True)
                log.write(f"reduce_case:{case_name}:{len(case_df)}\n")
                for size in reduction_sizes:
                    for method in methods:
                        row = evaluate_reduction_method(
                            case_df,
                            method=method,
                            selected_count=size,
                            seed=seed,
                        )
                        reduction_rows.append(row)
            reduction_df = pd.DataFrame(reduction_rows)
            write_csv(reduction_df, Path(p["tables"]) / "opf_reduction_results.csv")
            log.write(f"reduction_written:{len(reduction_df)}\n")

            repeated_rows = []
            repeated_case_frames = []
            for sample_id, sample_seed in enumerate(repeated_sampling_seeds, start=1):
                scenarios_i = sample_opf_scenarios(features, sample_size=sample_size, seed=sample_seed)
                scenarios_i["sample_id"] = sample_id
                scenarios_i["sample_seed"] = sample_seed
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
            repeated_case_df = pd.DataFrame(repeated_case_frames)
            repeated_reduction_df = pd.DataFrame(repeated_rows)
            repeated_summary_df = summarize_reduction_results(repeated_reduction_df)
            repeated_best_df = summarize_reduction_best(repeated_summary_df)
            write_csv(repeated_case_df, Path(p["tables"]) / "opf_case_results_repeated.csv")
            write_csv(repeated_reduction_df, Path(p["tables"]) / "opf_reduction_repeated_results.csv")
            write_csv(repeated_summary_df, Path(p["tables"]) / "opf_reduction_repeated_summary.csv")
            write_csv(repeated_best_df, Path(p["tables"]) / "opf_reduction_repeated_best.csv")
            log.write(f"repeated_sampling_written:{len(repeated_reduction_df)}\n")
            print(
                "OPF_BENCHMARK_DONE",
                {
                    "cases": case_names,
                    "sample_size": sample_size,
                    "reduction_sizes": reduction_sizes,
                    "rows": len(reduction_df),
                    "repeated_sampling_count": repeated_sampling_count,
                },
            )
        except Exception:
            traceback.print_exc(file=log)
            raise


if __name__ == "__main__":
    main()
