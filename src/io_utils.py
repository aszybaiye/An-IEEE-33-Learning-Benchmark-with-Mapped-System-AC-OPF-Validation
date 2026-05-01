from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import pandas as pd
import yaml


def load_config(config_path: str | Path) -> dict[str, Any]:
    with Path(config_path).open("r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    output_root = os.getenv("OPEN2PAPER_OUTPUTS_ROOT")
    if output_root:
        p = cfg.setdefault("paths", {})
        p["outputs"] = output_root
        p["interim"] = str(Path(output_root) / "interim")
        p["models"] = str(Path(output_root) / "models")
        p["tables"] = str(Path(output_root) / "tables")
        p["figures"] = str(Path(output_root) / "figures")
        p["photos"] = str(Path(output_root) / "photos")
    return cfg


def ensure_dirs(paths: list[str | Path]) -> None:
    for p in paths:
        Path(p).mkdir(parents=True, exist_ok=True)


def save_json(data: dict[str, Any], path: str | Path) -> None:
    with Path(path).open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def read_csv(path: str | Path) -> pd.DataFrame:
    return pd.read_csv(path)


def write_csv(df: pd.DataFrame, path: str | Path) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
