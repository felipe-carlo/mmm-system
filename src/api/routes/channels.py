"""Channel routes: list discovered channels and their configuration."""

from __future__ import annotations

import os

from fastapi import APIRouter, HTTPException

from src.api.schemas.models import ChannelInfo, ChannelListResponse
from src.pipeline.connectors.sheets_connector import SheetsConnector
from src.models.channel_registry import ChannelRegistry

router = APIRouter(prefix="/api/channels", tags=["channels"])


@router.get("", response_model=ChannelListResponse)
def list_channels():
    """List all configured channels from the Google Sheet."""
    url = os.getenv("GOOGLE_SHEETS_URL")
    creds = os.getenv("GOOGLE_SHEETS_CREDENTIALS_PATH")

    if not url or not creds:
        raise HTTPException(
            status_code=400,
            detail="GOOGLE_SHEETS_URL and GOOGLE_SHEETS_CREDENTIALS_PATH must be set",
        )

    try:
        connector = SheetsConnector(spreadsheet_url=url, credentials_path=creds)
        config_df = connector.fetch_channel_config()
        registry = ChannelRegistry(config_df)

        channels = [
            ChannelInfo(
                name=ch.name,
                channel_type=ch.channel_type,
                has_impressions=ch.has_impressions,
                adstock_l_max_weeks=ch.adstock_l_max,
                adstock_decay_prior_mu=ch.adstock_decay_mu,
                roi_prior_mu=ch.roi_prior_mu,
                min_budget_weekly=ch.min_budget_weekly,
                max_budget_weekly=ch.max_budget_weekly,
            )
            for ch in registry.channels
        ]

        return ChannelListResponse(channels=channels, total=len(channels))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
