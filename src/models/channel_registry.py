"""Channel Registry: bridge between Google Sheets channel_config and model engines.

Reads the channel_config tab and produces configuration dicts for
PyMC-Marketing and Google Meridian.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from loguru import logger

VALID_CHANNEL_TYPES = {
    "digital",
    "offline_tv",
    "offline_radio",
    "offline_ooh",
    "influencer",
    "events",
    "sponsorship",
    "trade",
}

# Default adstock priors by channel type (mu, sigma)
DEFAULT_ADSTOCK = {
    "digital": {"l_max": 4, "decay_mu": 0.30, "decay_sigma": 0.10},
    "offline_tv": {"l_max": 8, "decay_mu": 0.60, "decay_sigma": 0.15},
    "offline_radio": {"l_max": 6, "decay_mu": 0.50, "decay_sigma": 0.12},
    "offline_ooh": {"l_max": 8, "decay_mu": 0.55, "decay_sigma": 0.15},
    "influencer": {"l_max": 4, "decay_mu": 0.35, "decay_sigma": 0.15},
    "events": {"l_max": 2, "decay_mu": 0.20, "decay_sigma": 0.10},
    "sponsorship": {"l_max": 6, "decay_mu": 0.45, "decay_sigma": 0.15},
    "trade": {"l_max": 2, "decay_mu": 0.15, "decay_sigma": 0.10},
}


@dataclass
class ChannelSpec:
    """Specification for a single media channel."""

    name: str
    channel_type: str
    has_impressions: bool
    adstock_l_max: int
    adstock_decay_mu: float
    adstock_decay_sigma: float
    saturation_type: str
    roi_prior_mu: float
    roi_prior_sigma: float
    min_budget_weekly: float
    max_budget_weekly: float


class ChannelRegistry:
    """Registry that reads channel_config and produces model configurations."""

    def __init__(self, config_df: pd.DataFrame) -> None:
        self._channels: list[ChannelSpec] = []
        self._parse(config_df)

    def _parse(self, df: pd.DataFrame) -> None:
        for _, row in df.iterrows():
            channel_type = str(row.get("channel_type", "digital"))
            defaults = DEFAULT_ADSTOCK.get(channel_type, DEFAULT_ADSTOCK["digital"])

            spec = ChannelSpec(
                name=str(row["channel_name"]),
                channel_type=channel_type,
                has_impressions=bool(row.get("has_impressions", False)),
                adstock_l_max=int(row.get("adstock_l_max_weeks", defaults["l_max"])),
                adstock_decay_mu=float(row.get("adstock_decay_prior_mu", defaults["decay_mu"])),
                adstock_decay_sigma=float(
                    row.get("adstock_decay_prior_sigma", defaults["decay_sigma"])
                ),
                saturation_type=str(row.get("saturation_type", "logistic")),
                roi_prior_mu=float(row.get("roi_prior_mu", 1.0)),
                roi_prior_sigma=float(row.get("roi_prior_sigma", 1.0)),
                min_budget_weekly=float(row.get("min_budget_weekly", 0)),
                max_budget_weekly=float(row.get("max_budget_weekly", float("inf"))),
            )
            self._channels.append(spec)

        logger.info(f"ChannelRegistry loaded {len(self._channels)} channels")

    @property
    def channels(self) -> list[ChannelSpec]:
        return list(self._channels)

    def get_channel(self, name: str) -> ChannelSpec:
        for ch in self._channels:
            if ch.name == name:
                return ch
        raise KeyError(f"Channel '{name}' not found in registry")

    def get_spend_columns(self) -> list[str]:
        return [f"{ch.name}_spend" for ch in self._channels]

    def get_impression_columns(self) -> list[str]:
        """Return impression columns for channels that have them."""
        cols = []
        for ch in self._channels:
            if ch.has_impressions:
                cols.append(f"{ch.name}_impressions")
        return cols

    def get_max_adstock_l_max(self) -> int:
        """Max l_max across all channels (used as global l_max in PyMC-Marketing)."""
        return max(ch.adstock_l_max for ch in self._channels)

    def get_pymc_adstock_priors(self) -> dict[str, np.ndarray]:
        """Build per-channel adstock decay prior arrays for PyMC-Marketing.

        Returns alpha/beta parameters for Beta distribution priors on decay rate.
        Uses the mean-precision parameterization: alpha = mu * precision, beta = (1-mu) * precision.
        Precision is derived from sigma: precision ≈ mu*(1-mu)/sigma^2 - 1.
        """
        mus = np.array([ch.adstock_decay_mu for ch in self._channels])
        sigmas = np.array([ch.adstock_decay_sigma for ch in self._channels])

        # Beta distribution from mean and sigma
        # precision = mu*(1-mu)/sigma^2 - 1, clamped to minimum of 2
        precision = np.clip(mus * (1 - mus) / (sigmas**2) - 1, 2, None)
        alphas = mus * precision
        betas = (1 - mus) * precision

        return {"alpha": alphas, "beta": betas}

    def get_pymc_saturation_priors(self) -> dict[str, np.ndarray]:
        """Build per-channel ROI prior arrays for PyMC-Marketing saturation."""
        roi_mus = np.array([ch.roi_prior_mu for ch in self._channels])
        roi_sigmas = np.array([ch.roi_prior_sigma for ch in self._channels])
        return {
            "mu": np.log(roi_mus),
            "sigma": roi_sigmas,
        }

    def get_optimizer_constraints(self) -> dict[str, dict[str, float]]:
        """Return min/max budget constraints per channel for the optimizer."""
        return {
            ch.name: {
                "min": ch.min_budget_weekly,
                "max": ch.max_budget_weekly,
            }
            for ch in self._channels
        }
