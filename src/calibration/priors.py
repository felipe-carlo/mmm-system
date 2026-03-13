"""Prior management: update model priors based on experiment results."""

from __future__ import annotations

import pandas as pd
from loguru import logger

from src.calibration.geo_lift import CalibrationHistory
from src.models.channel_registry import ChannelRegistry


def update_channel_config_with_experiments(
    config_df: pd.DataFrame,
    calibration: CalibrationHistory,
) -> pd.DataFrame:
    """Update channel_config DataFrame with prior suggestions from experiments.

    Returns a new DataFrame with updated roi_prior_mu values based on
    completed geo-lift experiments.
    """
    updated = config_df.copy()

    for _, row in updated.iterrows():
        channel = row["channel_name"]
        current_mu = row.get("roi_prior_mu", 1.0)

        suggestion = calibration.get_prior_update_suggestion(channel, current_mu)
        if suggestion:
            idx = updated.index[updated["channel_name"] == channel]
            updated.loc[idx, "roi_prior_mu"] = suggestion["suggested_prior_mu"]
            logger.info(
                f"Updated prior for '{channel}': "
                f"{current_mu:.3f} -> {suggestion['suggested_prior_mu']:.3f}"
            )

    return updated
