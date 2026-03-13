"""PostgreSQL storage layer for MMM data.

Stores data in long/melted format so adding new channels doesn't require schema changes.
"""

from __future__ import annotations

import pandas as pd
from loguru import logger
from sqlalchemy import (
    Column,
    DateTime,
    Float,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    create_engine,
    text,
)
from sqlalchemy.engine import Engine

metadata = MetaData()

daily_media_spend = Table(
    "daily_media_spend",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("date", DateTime, nullable=False),
    Column("channel_name", String(100), nullable=False),
    Column("spend", Float, nullable=False, default=0),
    Column("impressions", Float, nullable=True),
)

daily_kpi = Table(
    "daily_kpi",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("date", DateTime, nullable=False),
    Column("metric_name", String(100), nullable=False),
    Column("value", Float, nullable=True),
)

daily_external_factors = Table(
    "daily_external_factors",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("date", DateTime, nullable=False),
    Column("factor_name", String(100), nullable=False),
    Column("value", Float, nullable=True),
)

channel_config = Table(
    "channel_config",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("channel_name", String(100), nullable=False, unique=True),
    Column("channel_type", String(50), nullable=False),
    Column("has_impressions", Integer, default=0),
    Column("adstock_l_max_weeks", Integer),
    Column("adstock_decay_prior_mu", Float),
    Column("adstock_decay_prior_sigma", Float),
    Column("saturation_type", String(20)),
    Column("roi_prior_mu", Float),
    Column("roi_prior_sigma", Float),
    Column("min_budget_weekly", Float),
    Column("max_budget_weekly", Float),
)

sync_log = Table(
    "sync_log",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("timestamp", DateTime, nullable=False),
    Column("status", String(20), nullable=False),
    Column("rows_fetched", Integer),
    Column("validation_warnings", Text),
)


class PostgresStorage:
    """Read/write MMM data to PostgreSQL in long format."""

    def __init__(self, database_url: str) -> None:
        self._engine: Engine = create_engine(database_url)

    def create_tables(self) -> None:
        metadata.create_all(self._engine)
        logger.info("PostgreSQL tables created/verified")

    def upsert_media_spend(self, df: pd.DataFrame) -> int:
        """Upsert daily media spend from wide format DataFrame.

        Melts the wide DataFrame into long format (date, channel_name, spend, impressions)
        and upserts by (date, channel_name).
        """
        spend_cols = [c for c in df.columns if c.endswith("_spend")]
        rows = []
        for _, row in df.iterrows():
            date = row["date"]
            for col in spend_cols:
                channel = col.removesuffix("_spend")
                impression_col = f"{channel}_impressions"
                # Also check for alternative metric columns
                alt_cols = [f"{channel}_grps", f"{channel}_spots", f"{channel}_faces"]
                impressions = None
                if impression_col in df.columns:
                    val = row[impression_col]
                    impressions = float(val) if pd.notna(val) else None
                else:
                    for alt in alt_cols:
                        if alt in df.columns:
                            val = row[alt]
                            impressions = float(val) if pd.notna(val) else None
                            break

                rows.append({
                    "date": date,
                    "channel_name": channel,
                    "spend": float(row[col]),
                    "impressions": impressions,
                })

        if not rows:
            return 0

        with self._engine.begin() as conn:
            # Delete existing data for the date range, then insert
            dates = df["date"].unique()
            conn.execute(
                text("DELETE FROM daily_media_spend WHERE date = ANY(:dates)"),
                {"dates": list(dates)},
            )
            conn.execute(daily_media_spend.insert(), rows)

        logger.info(f"Upserted {len(rows)} media_spend rows")
        return len(rows)

    def upsert_kpi(self, df: pd.DataFrame) -> int:
        """Upsert daily KPIs from wide format to long format."""
        metric_cols = [c for c in df.columns if c != "date"]
        rows = []
        for _, row in df.iterrows():
            date = row["date"]
            for col in metric_cols:
                val = row[col]
                if pd.notna(val):
                    rows.append({
                        "date": date,
                        "metric_name": col,
                        "value": float(val),
                    })

        if not rows:
            return 0

        with self._engine.begin() as conn:
            dates = df["date"].unique()
            conn.execute(
                text("DELETE FROM daily_kpi WHERE date = ANY(:dates)"),
                {"dates": list(dates)},
            )
            conn.execute(daily_kpi.insert(), rows)

        logger.info(f"Upserted {len(rows)} kpi rows")
        return len(rows)

    def upsert_external_factors(self, df: pd.DataFrame) -> int:
        """Upsert daily external factors from wide format to long format."""
        factor_cols = [c for c in df.columns if c != "date"]
        rows = []
        for _, row in df.iterrows():
            date = row["date"]
            for col in factor_cols:
                val = row[col]
                if pd.notna(val):
                    rows.append({
                        "date": date,
                        "factor_name": col,
                        "value": float(val),
                    })

        if not rows:
            return 0

        with self._engine.begin() as conn:
            dates = df["date"].unique()
            conn.execute(
                text("DELETE FROM daily_external_factors WHERE date = ANY(:dates)"),
                {"dates": list(dates)},
            )
            conn.execute(daily_external_factors.insert(), rows)

        logger.info(f"Upserted {len(rows)} external_factors rows")
        return len(rows)

    def upsert_channel_config(self, df: pd.DataFrame) -> int:
        """Replace channel_config table with data from sheet."""
        with self._engine.begin() as conn:
            conn.execute(text("DELETE FROM channel_config"))
            records = df.to_dict("records")
            if records:
                conn.execute(channel_config.insert(), records)

        logger.info(f"Upserted {len(df)} channel_config rows")
        return len(df)

    def log_sync(self, status: str, rows_fetched: int, warnings: str = "") -> None:
        """Log a sync event."""
        from datetime import datetime

        with self._engine.begin() as conn:
            conn.execute(
                sync_log.insert().values(
                    timestamp=datetime.now(),
                    status=status,
                    rows_fetched=rows_fetched,
                    validation_warnings=warnings,
                )
            )
