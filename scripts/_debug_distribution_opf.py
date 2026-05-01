from __future__ import annotations

import json
import traceback
from pathlib import Path

import pandas as pd

from src.ddre33_validation import load_actual_day_scenario
from src.dist_opf_utils import build_distribution_case_template, run_snapshot_opf
from src.io_utils import load_config


def main() -> None:
    out = {"steps": []}
    try:
        cfg = load_config("configs/experiment.yaml")
        out["steps"].append({"step": "load_config", "paths": cfg["paths"]})

        features = pd.read_csv(Path(cfg["paths"]["interim"]) / "features.csv")
        out["steps"].append({"step": "load_features", "rows": int(len(features))})

        for case_name in ["case33bw", "case69"]:
            template = build_distribution_case_template(case_name, "data")
            out["steps"].append(
                {
                    "step": f"build_template_{case_name}",
                    "renewable_rows": template.renewable_rows.tolist(),
                    "renewable_caps": [float(x) for x in template.renewable_caps.tolist()],
                }
            )
            scenario_df = load_actual_day_scenario("data", 1)
            row = run_snapshot_opf(template, 1, scenario_df)
            out["steps"].append({"step": f"run_snapshot_{case_name}", "result": row})
        out["ok"] = True
    except Exception:
        out["ok"] = False
        out["traceback"] = traceback.format_exc()

    Path("Outputs/tables/distribution_opf_probe.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
