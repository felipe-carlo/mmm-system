"""Daily to weekly aggregation for MMM data.

Aggregation rules:
- Spend columns: SUM per ISO week
- Impressions/GRPs/Spots: SUM per ISO week
- Boolean flags (promotions, holidays): MAX per week (1 if any day had the flag)
- Macro variables (IPCA, SELIC, USD/BRL): MEAN per week
- Revenue/KPIs: SUM per week
"""

from __future__ import annotations

import pandas as pd
from loguru import logger

# Columns that use MAX aggregation (boolean flags)
FLAG_COLUMNS = {
    "promotion",
    "black_friday",
    "christmas",
    "carnival",
    "mothers_day",
    "competitor_major_campaign",
    "other_holiday",
}

# Columns that use MEAN aggregation (macro/continuous variables)
MEAN_COLUMNS = {
    "ipca_monthly",
    "usd_brl",
    "selic_rate",
    "price_index",
    "promotion_discount_pct",
}


def _add_week_column(df: pd.DataFrame) -> pd.DataFrame:
    """Add ISO week column (Monday of the week) to a dataframe with 'date' column."""
    df = df.copy()
    df["date_week"] = df["date"].dt.to_period("W-SUN").dt.start_time
    return df


def aggregate_media_spend(daily: pd.DataFrame) -> pd.DataFrame:
    """Aggregate daily media spend to weekly. All columns SUM'd."""
    df = _add_week_column(daily)
    numeric_cols = [c for c in df.columns if c not in ("date", "date_week")]
    agg_dict = {col: "sum" for col in numeric_cols}
    weekly = df.groupby("date_week").agg(agg_dict).reset_index()
    logger.info(f"Aggregated media_spend: {len(daily)} daily rows -> {len(weekly)} weekly rows")
    return weekly


def aggregate_kpi(daily: pd.DataFrame) -> pd.DataFrame:
    """Aggregate daily KPIs to weekly. All columns SUM'd."""
    df = _add_week_column(daily)
    numeric_cols = [c for c in df.columns if c not in ("date", "date_week")]
    agg_dict = {col: "sum" for col in numeric_cols}
    weekly = df.groupby("date_week").agg(agg_dict).reset_index()
    logger.info(f"Aggregated kpi: {len(daily)} daily rows -> {len(weekly)} weekly rows")
    return weekly


def aggregate_external_factors(daily: pd.DataFrame) -> pd.DataFrame:
    """Aggregate daily external factors to weekly.

    - Flag columns (0/1): MAX (if any day in week had 1, week gets 1)
    - Continuous/macro columns: MEAN
    - Other columns: MEAN (default)
    """
    df = _add_week_column(daily)
    numeric_cols = [c for c in df.columns if c not in ("date", "date_week")]

    agg_dict = {}
    for col in numeric_cols:
        if col in FLAG_COLUMNS:
            agg_dict[col] = "max"
        elif col in MEAN_COLUMNS:
            agg_dict[col] = "mean"
        else:
            agg_dict[col] = "mean"

    weekly = df.groupby("date_week").agg(agg_dict).reset_index()
    logger.info(
        f"Aggregated external_factors: {len(daily)} daily rows -> {len(weekly)} weekly rows"
    )
    return weekly


def build_model_dataframe(
    media_spend_weekly: pd.DataFrame,
    kpi_weekly: pd.DataFrame,
    external_factors_weekly: pd.DataFrame,
) -> pd.DataFrame:
    """Merge all weekly dataframes into a single model-ready wide dataframe.

    Output columns:
    - date_week (Monday of ISO week)
    - {channel}_spend columns
    - {channel}_impressions columns (where available)
    - revenue (primary KPI)
    - All control/external factor columns
    - trend (integer week index)
    """
    # Merge on date_week
    df = media_spend_weekly.merge(kpi_weekly, on="date_week", how="inner")
    df = df.merge(external_factors_weekly, on="date_week", how="left")

    # Sort by date and add trend column
    df = df.sort_values("date_week").reset_index(drop=True)
    df["trend"] = range(len(df))

    logger.info(
        f"Built model dataframe: {len(df)} weeks, {len(df.columns)} columns"
    )
    return df
