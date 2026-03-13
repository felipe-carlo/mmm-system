"""Abstract base class for MMM model wrappers and standardized results."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

import arviz as az
import pandas as pd


@dataclass
class ModelResult:
    """Standardized output from any MMM model (PyMC-Marketing or Meridian)."""

    # Per-channel ROI: channel_name -> (mean, lower_ci, upper_ci)
    roi_by_channel: dict[str, tuple[float, float, float]]
    # Weekly contribution per channel (DataFrame: date_week x channels)
    channel_contributions: pd.DataFrame
    # Estimated adstock decay per channel
    adstock_params: dict[str, float]
    # Non-media baseline contribution
    baseline_contribution: float
    # Model fit metrics
    model_fit_metrics: dict[str, float]
    # Full posterior for advanced analysis
    inference_data: az.InferenceData | None = None
    # Additional metadata
    metadata: dict = field(default_factory=dict)


class BaseModelWrapper(ABC):
    """Abstract interface for MMM model wrappers."""

    @abstractmethod
    def fit(self, df: pd.DataFrame, target_col: str = "revenue", **kwargs) -> None:
        """Fit the model on weekly aggregated data."""

    @abstractmethod
    def get_results(self) -> ModelResult:
        """Extract standardized results from the fitted model."""

    @abstractmethod
    def get_channel_contributions(self) -> pd.DataFrame:
        """Get weekly contribution per channel."""

    @abstractmethod
    def get_roi(self) -> dict[str, tuple[float, float, float]]:
        """Get ROI per channel as (mean, lower_ci, upper_ci)."""

    @abstractmethod
    def optimize_budget(
        self, total_budget: float, budget_bounds: dict[str, tuple[float, float]] | None = None
    ) -> dict[str, float]:
        """Optimize budget allocation across channels."""
