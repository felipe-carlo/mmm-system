"""DuckDB analytics layer for fast analytical queries and model input generation."""

from __future__ import annotations

from pathlib import Path

import duckdb
import pandas as pd
from loguru import logger


class DuckDBAnalytics:
    """DuckDB-based analytics engine for MMM data."""

    def __init__(self, db_path: str | Path = ":memory:") -> None:
        self._db_path = str(db_path)
        self._conn: duckdb.DuckDBPyConnection | None = None

    def _connect(self) -> duckdb.DuckDBPyConnection:
        if self._conn is None:
            self._conn = duckdb.connect(self._db_path)
        return self._conn

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def store_weekly_data(self, df: pd.DataFrame, table_name: str = "weekly_model_data") -> None:
        """Store a weekly aggregated DataFrame as a DuckDB table."""
        conn = self._connect()
        conn.execute(f"DROP TABLE IF EXISTS {table_name}")
        conn.execute(f"CREATE TABLE {table_name} AS SELECT * FROM df")
        logger.info(f"Stored {len(df)} rows in DuckDB table '{table_name}'")

    def get_weekly_data(self, table_name: str = "weekly_model_data") -> pd.DataFrame:
        """Retrieve weekly data as a pandas DataFrame."""
        conn = self._connect()
        return conn.execute(f"SELECT * FROM {table_name} ORDER BY date_week").fetchdf()

    def get_channel_summary(self, table_name: str = "weekly_model_data") -> pd.DataFrame:
        """Get summary statistics per channel (total spend, avg weekly spend, weeks active)."""
        conn = self._connect()
        # Dynamically find spend columns
        columns = conn.execute(
            f"SELECT column_name FROM information_schema.columns "
            f"WHERE table_name = '{table_name}' AND column_name LIKE '%_spend'"
        ).fetchdf()

        if columns.empty:
            return pd.DataFrame()

        spend_cols = columns["column_name"].tolist()
        summaries = []
        for col in spend_cols:
            channel = col.removesuffix("_spend")
            result = conn.execute(f"""
                SELECT
                    '{channel}' as channel,
                    SUM({col}) as total_spend,
                    AVG({col}) as avg_weekly_spend,
                    COUNT(CASE WHEN {col} > 0 THEN 1 END) as weeks_active,
                    COUNT(*) as total_weeks
                FROM {table_name}
            """).fetchdf()
            summaries.append(result)

        return pd.concat(summaries, ignore_index=True)

    def save_to_parquet(
        self, table_name: str = "weekly_model_data", output_path: str | Path = "data/processed"
    ) -> Path:
        """Export a DuckDB table to Parquet file."""
        output_path = Path(output_path)
        output_path.mkdir(parents=True, exist_ok=True)
        file_path = output_path / f"{table_name}.parquet"
        conn = self._connect()
        conn.execute(f"COPY {table_name} TO '{file_path}' (FORMAT PARQUET)")
        logger.info(f"Exported '{table_name}' to {file_path}")
        return file_path
