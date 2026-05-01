from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
from sklearn.model_selection import train_test_split


@dataclass
class SplitResult:
    train: pd.DataFrame
    val: pd.DataFrame
    test: pd.DataFrame


def make_stratify_label(df: pd.DataFrame, cols: list[str]) -> pd.Series:
    s = df[cols[0]].astype(str)
    for c in cols[1:]:
        s = s + "_" + df[c].astype(str)
    return s


def split_dataset(
    df: pd.DataFrame, train_ratio: float, val_ratio: float, seed: int, stratify_cols: list[str]
) -> SplitResult:
    stratify = make_stratify_label(df, stratify_cols)
    train_df, temp_df = train_test_split(
        df, test_size=1 - train_ratio, random_state=seed, stratify=stratify
    )
    temp_ratio = 1 - train_ratio
    test_ratio = 1 - train_ratio - val_ratio
    val_size_in_temp = val_ratio / temp_ratio
    stratify_temp = make_stratify_label(temp_df, stratify_cols)
    val_df, test_df = train_test_split(
        temp_df, test_size=test_ratio / temp_ratio, random_state=seed, stratify=stratify_temp
    )
    _ = val_size_in_temp
    return SplitResult(
        train=train_df.reset_index(drop=True),
        val=val_df.reset_index(drop=True),
        test=test_df.reset_index(drop=True),
    )
