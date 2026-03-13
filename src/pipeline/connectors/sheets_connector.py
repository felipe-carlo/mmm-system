"""Google Sheets connector for MMM data ingestion.

Single connector that replaces all API connectors (Google Ads, Meta, GA4, etc.).
Reads from a Google Sheets workbook with 4 tabs: media_spend, kpi, external_factors, channel_config.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
from loguru import logger

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
]

TAB_MEDIA_SPEND = "media_spend"
TAB_KPI = "kpi"
TAB_EXTERNAL_FACTORS = "external_factors"
TAB_CHANNEL_CONFIG = "channel_config"


class SheetsConnector:
    """Connects to a Google Sheets workbook and fetches MMM data."""

    def __init__(self, spreadsheet_url: str, credentials_path: str) -> None:
        self._spreadsheet_url = spreadsheet_url
        self._credentials_path = credentials_path
        self._client: gspread.Client | None = None
        self._spreadsheet: gspread.Spreadsheet | None = None

    def _connect(self) -> gspread.Spreadsheet:
        if self._spreadsheet is not None:
            return self._spreadsheet

        logger.info("Connecting to Google Sheets...")
        creds = Credentials.from_service_account_file(
            self._credentials_path, scopes=SCOPES
        )
        self._client = gspread.authorize(creds)
        self._spreadsheet = self._client.open_by_url(self._spreadsheet_url)
        logger.info(f"Connected to spreadsheet: {self._spreadsheet.title}")
        return self._spreadsheet

    def _fetch_tab(self, tab_name: str) -> pd.DataFrame:
        spreadsheet = self._connect()
        worksheet = spreadsheet.worksheet(tab_name)
        records = worksheet.get_all_records()
        if not records:
            raise ValueError(f"Tab '{tab_name}' is empty")
        df = pd.DataFrame(records)
        logger.info(f"Fetched {len(df)} rows from '{tab_name}'")
        return df

    def fetch_media_spend(self) -> pd.DataFrame:
        df = self._fetch_tab(TAB_MEDIA_SPEND)
        df["date"] = pd.to_datetime(df["date"], format="%Y-%m-%d")
        # Replace empty strings with NaN for non-spend columns
        spend_cols = [c for c in df.columns if c.endswith("_spend")]
        for col in spend_cols:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
        non_date_non_spend = [c for c in df.columns if c != "date" and c not in spend_cols]
        for col in non_date_non_spend:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        return df.sort_values("date").reset_index(drop=True)

    def fetch_kpi(self) -> pd.DataFrame:
        df = self._fetch_tab(TAB_KPI)
        df["date"] = pd.to_datetime(df["date"], format="%Y-%m-%d")
        numeric_cols = [c for c in df.columns if c != "date"]
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        return df.sort_values("date").reset_index(drop=True)

    def fetch_external_factors(self) -> pd.DataFrame:
        df = self._fetch_tab(TAB_EXTERNAL_FACTORS)
        df["date"] = pd.to_datetime(df["date"], format="%Y-%m-%d")
        numeric_cols = [c for c in df.columns if c != "date"]
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        return df.sort_values("date").reset_index(drop=True)

    def fetch_channel_config(self) -> pd.DataFrame:
        df = self._fetch_tab(TAB_CHANNEL_CONFIG)
        numeric_cols = [
            "adstock_l_max_weeks",
            "adstock_decay_prior_mu",
            "adstock_decay_prior_sigma",
            "roi_prior_mu",
            "roi_prior_sigma",
            "min_budget_weekly",
            "max_budget_weekly",
        ]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        bool_cols = ["has_impressions"]
        for col in bool_cols:
            if col in df.columns:
                df[col] = df[col].astype(str).str.upper().map({"TRUE": True, "FALSE": False})
        return df

    def discover_channels(self, media_spend_df: pd.DataFrame | None = None) -> list[str]:
        """Discover channel names by scanning *_spend columns."""
        if media_spend_df is None:
            media_spend_df = self.fetch_media_spend()
        spend_cols = [c for c in media_spend_df.columns if c.endswith("_spend")]
        channels = [c.removesuffix("_spend") for c in spend_cols]
        logger.info(f"Discovered {len(channels)} channels: {channels}")
        return channels

    def fetch_all(self) -> dict[str, pd.DataFrame]:
        """Fetch all 4 tabs and return as dict."""
        return {
            TAB_MEDIA_SPEND: self.fetch_media_spend(),
            TAB_KPI: self.fetch_kpi(),
            TAB_EXTERNAL_FACTORS: self.fetch_external_factors(),
            TAB_CHANNEL_CONFIG: self.fetch_channel_config(),
        }

    def snapshot_to_parquet(self, data: dict[str, pd.DataFrame], output_dir: str | Path) -> Path:
        """Save fetched data as timestamped Parquet snapshots for audit/recovery."""
        output_dir = Path(output_dir)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        snapshot_dir = output_dir / f"snapshot_{timestamp}"
        snapshot_dir.mkdir(parents=True, exist_ok=True)

        for tab_name, df in data.items():
            path = snapshot_dir / f"{tab_name}.parquet"
            df.to_parquet(path, index=False)
            logger.info(f"Saved snapshot: {path}")

        return snapshot_dir
