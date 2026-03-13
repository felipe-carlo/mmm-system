"""Sync routes: trigger Google Sheets data sync."""

from __future__ import annotations

import os
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from src.api.schemas.models import (
    ChannelSyncResponse,
    SyncResponse,
    SyncStatusResponse,
    TabSyncResponse,
)
from src.pipeline.connectors.sheets_connector import SheetsConnector
from src.pipeline.validators.data_validator import DataValidator

router = APIRouter(prefix="/api/sync", tags=["sync"])

VALID_TABS = {"media_spend", "kpi", "external_factors", "channel_config"}

# In-memory sync status tracking (replace with DB/Redis in production)
_sync_status: dict[str, dict] = {
    "tabs": {},  # tab_name -> {"last_synced": str, "rows": int, "status": str}
    "channels": {},  # channel_name -> {"last_synced": str, "rows": int, "status": str}
}


def _get_connector() -> tuple[SheetsConnector, str, str]:
    """Create a SheetsConnector from env vars, raising 400 if not configured."""
    url = os.getenv("GOOGLE_SHEETS_URL", "")
    creds = os.getenv("GOOGLE_SHEETS_CREDENTIALS_PATH", "")
    if not url or not creds:
        raise HTTPException(
            status_code=400,
            detail="GOOGLE_SHEETS_URL and GOOGLE_SHEETS_CREDENTIALS_PATH must be set",
        )
    return SheetsConnector(spreadsheet_url=url, credentials_path=creds), url, creds


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


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

        # Update sync status for all tabs and channels
        now = _now_iso()
        for tab_name, df in data.items():
            _sync_status["tabs"][tab_name] = {
                "last_synced": now,
                "rows": len(df),
                "status": "success",
            }
        for ch in channels:
            spend_col = f"{ch}_spend"
            rows = int(data["media_spend"][spend_col].notna().sum())
            _sync_status["channels"][ch] = {
                "last_synced": now,
                "rows": rows,
                "status": "success",
            }

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


@router.get("/status", response_model=SyncStatusResponse)
def get_sync_status():
    """Return current sync status for all tabs and channels."""
    connector, *_ = _get_connector()

    connected = False
    title = None
    try:
        spreadsheet = connector._connect()
        connected = True
        title = spreadsheet.title
    except Exception:
        pass

    return SyncStatusResponse(
        spreadsheet_connected=connected,
        spreadsheet_title=title,
        tabs=_sync_status.get("tabs", {}),
        channels=_sync_status.get("channels", {}),
    )


@router.post("/tab/{tab_name}", response_model=TabSyncResponse)
def sync_tab(tab_name: str):
    """Sync a specific Google Sheets tab."""
    if tab_name not in VALID_TABS:
        raise HTTPException(
            status_code=404,
            detail=f"Tab '{tab_name}' not found. Valid tabs: {sorted(VALID_TABS)}",
        )

    connector, *_ = _get_connector()

    fetch_dispatch = {
        "media_spend": connector.fetch_media_spend,
        "kpi": connector.fetch_kpi,
        "external_factors": connector.fetch_external_factors,
        "channel_config": connector.fetch_channel_config,
    }

    try:
        df = fetch_dispatch[tab_name]()
        now = _now_iso()

        # Save single-tab snapshot
        connector.snapshot_to_parquet({tab_name: df}, "data/raw")

        # Update sync status
        _sync_status["tabs"][tab_name] = {
            "last_synced": now,
            "rows": len(df),
            "status": "success",
        }

        # If media_spend, also update channel statuses
        warnings: list[str] = []
        if tab_name == "media_spend":
            channels = connector.discover_channels(df)
            for ch in channels:
                spend_col = f"{ch}_spend"
                rows = int(df[spend_col].notna().sum())
                _sync_status["channels"][ch] = {
                    "last_synced": now,
                    "rows": rows,
                    "status": "success",
                }

        return TabSyncResponse(
            status="success",
            tab_name=tab_name,
            rows_fetched=len(df),
            last_synced=now,
            warnings=warnings,
        )
    except HTTPException:
        raise
    except Exception as e:
        _sync_status["tabs"][tab_name] = {
            "last_synced": _sync_status.get("tabs", {}).get(tab_name, {}).get("last_synced"),
            "rows": _sync_status.get("tabs", {}).get(tab_name, {}).get("rows"),
            "status": "error",
        }
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/channel/{channel_name}", response_model=ChannelSyncResponse)
def sync_channel(channel_name: str):
    """Sync data for a specific channel from the media_spend tab."""
    connector, *_ = _get_connector()

    try:
        df = connector.fetch_media_spend()
        spend_col = f"{channel_name}_spend"

        if spend_col not in df.columns:
            available = connector.discover_channels(df)
            raise HTTPException(
                status_code=404,
                detail=f"Channel '{channel_name}' not found. Available: {available}",
            )

        # Extract channel-specific data
        cols = ["date", spend_col]
        impressions_col = f"{channel_name}_impressions"
        if impressions_col in df.columns:
            cols.append(impressions_col)

        channel_df = df[cols].dropna(subset=[spend_col])
        now = _now_iso()

        date_range = {
            "start": str(channel_df["date"].min().date()),
            "end": str(channel_df["date"].max().date()),
        }

        # Update sync status
        _sync_status["channels"][channel_name] = {
            "last_synced": now,
            "rows": len(channel_df),
            "status": "success",
        }

        return ChannelSyncResponse(
            status="success",
            channel_name=channel_name,
            rows_fetched=len(channel_df),
            date_range=date_range,
            last_synced=now,
            warnings=[],
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
