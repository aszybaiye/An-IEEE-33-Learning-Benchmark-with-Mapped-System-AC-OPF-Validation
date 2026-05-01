from __future__ import annotations

import argparse
import subprocess
import sys


def run_cmd(cmd: list[str]) -> None:
    print("RUN", " ".join(cmd))
    completed = subprocess.run(cmd, check=True)
    if completed.returncode != 0:
        raise RuntimeError("Command failed")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--data_dir", default="data")
    parser.add_argument("--weekly_dir", default="data/1-Week Scenarios/1-Week Scenarios")
    args = parser.parse_args()
    py = sys.executable
    run_cmd([py, "scripts/01_prepare_dataset.py", "--config", args.config, "--data_dir", args.data_dir])
    run_cmd([py, "scripts/02_train_models.py", "--config", args.config])
    run_cmd([py, "scripts/03_build_library.py", "--config", args.config])
    run_cmd([py, "scripts/04_evaluate_transfer.py", "--config", args.config])
    run_cmd([py, "scripts/05_explain_shap.py", "--config", args.config])
    run_cmd(
        [
            py,
            "scripts/06_continual_learning.py",
            "--config",
            args.config,
            "--weekly_dir",
            args.weekly_dir,
        ]
    )
    run_cmd([py, "scripts/08_run_opf_benchmark.py", "--config", args.config])
    run_cmd([py, "scripts/09_run_ddre33_validation.py", "--config", args.config, "--data_dir", args.data_dir])
    run_cmd([py, "scripts/10_run_opf_repeated_sampling.py", "--config", args.config])
    run_cmd([py, "scripts/11_run_distribution_opf_validation.py", "--config", args.config, "--data_dir", args.data_dir])
    run_cmd([py, "scripts/07_make_assets.py", "--config", args.config, "--data_dir", args.data_dir])
    print("PIPELINE_FINISHED")


if __name__ == "__main__":
    main()
