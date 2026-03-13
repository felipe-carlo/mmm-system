"""Sync routes: trigger Google Sheets data sync."""

from __future__ import annotations

import os

from fastapi import APIRouter, HTTPException

from src.api.schemas.models import SyncResponse
from src.pipeline.connectors.sheets_connector import SheetsConnector
from src.pipeline.validators.data_validator import DataValidator

router = APIRouter(prefix="/api/sync", tags=["sync"])


@router.post("", response_model=SyncResponse)
def trigger_sync(spreadsheet_url: str | None = None):
    """Trigger a full sync from Google Sheets."""
    url = spreadsheet_url or os.getenv("GOOGLE_SHEETS_URL")
    creds = os.getenv("GOOGLE_SHEETS_CREDENTIALS_PATH")

    if not url or not creds:
        raise HTTPException(
            status_code=400,
            detail="GOOGLE_SHEETS_URL and GOOGLE_SHEETS_CREDENTIALS_PATH must be set",
        )

    try:
        connector = SheetsConnector(spreadsheet_url=url, credentials_path=creds)
        data = connector.fetch_all()
        channels = connector.discover_channels(data["media_spend"])

        # Validate
        validator = DataValidator()
        report = validator.validate_all(
            media_spend=data["media_spend"],
            kpi=data["kpi"],
            external_factors=data["external_factors"],
            channel_config=data["channel_config"],
        )

        if not report.is_valid:
            raise HTTPException(status_code=422, detail={"errors": report.errors})

        # Save snapshot
        connector.snapshot_to_parquet(data, "data/raw")

        total_rows = sum(len(df) for df in data.values())
        return SyncResponse(
            status="success",
            rows_fetched=total_rows,
            channels_discovered=channels,
            warnings=report.warnings,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
