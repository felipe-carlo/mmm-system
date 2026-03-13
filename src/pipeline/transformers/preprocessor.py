"""Preprocessing for model-ready data: scaling, encoding, trend generation."""

from __future__ import annotations

import numpy as np
import pandas as pd
from loguru import logger


def scale_spend_columns(df: pd.DataFrame, spend_cols: list[str]) -> tuple[pd.DataFrame, dict]:
    """Scale spend columns by dividing by their mean (mean-scaling).

    This is the recommended approach for PyMC-Marketing:
    - Preserves zero values
    - Makes coefficients interpretable (1 unit = 1 mean-week of spend)
    - Returns scalers dict for inverse transform
    """
    df = df.copy()
    scalers = {}
    for col in spend_cols:
        mean_val = df[col][df[col] > 0].mean()
        if pd.isna(mean_val) or mean_val == 0:
            mean_val = 1.0
        scalers[col] = float(mean_val)
        df[col] = df[col] / mean_val

    logger.info(f"Scaled {len(spend_cols)} spend columns by their mean")
    return df, scalers


def standardize_controls(
    df: pd.DataFrame, control_cols: list[str]
) -> tuple[pd.DataFrame, dict]:
    """Standardize continuous control variables (zero mean, unit variance).

    Skips binary/flag columns (columns with only 0/1 values).
    """
    df = df.copy()
    stats = {}
    for col in control_cols:
        if col not in df.columns:
            continue
        unique_vals = df[col].dropna().unique()
        # Skip binary columns
        if set(unique_vals).issubset({0, 1, 0.0, 1.0}):
            stats[col] = {"type": "binary"}
            continue

        mean_val = df[col].mean()
        std_val = df[col].std()
        if std_val == 0:
            std_val = 1.0
        df[col] = (df[col] - mean_val) / std_val
        stats[col] = {"type": "standardized", "mean": float(mean_val), "std": float(std_val)}

    logger.info(f"Standardized {len([s for s in stats.values() if s['type'] == 'standardized'])} control columns")
    return df, stats


def add_fourier_seasonality(df: pd.DataFrame, n_order: int = 2, period: float = 52.0) -> pd.DataFrame:
    """Add Fourier features for yearly seasonality.

    Creates sin/cos pairs for yearly cycles. n_order=2 means 4 features
    (sin1, cos1, sin2, cos2), which captures annual and semi-annual patterns.
    """
    df = df.copy()
    t = df["trend"].values
    for i in range(1, n_order + 1):
        df[f"sin_{i}"] = np.sin(2 * np.pi * i * t / period)
        df[f"cos_{i}"] = np.cos(2 * np.pi * i * t / period)

    logger.info(f"Added {n_order * 2} Fourier seasonality features (period={period})")
    return df
