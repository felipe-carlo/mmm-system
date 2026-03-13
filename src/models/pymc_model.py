"""PyMC-Marketing MMM wrapper.

Uses the multidimensional MMM class (recommended, future-proof) with dims=None
for single-market modeling. Builds per-channel priors dynamically from ChannelRegistry.
"""

from __future__ import annotations

import arviz as az
import numpy as np
import pandas as pd
import xarray as xr
from loguru import logger
from pymc_extras.prior import Prior
from pymc_marketing.mmm import GeometricAdstock, LogisticSaturation
from pymc_marketing.mmm.multidimensional import MMM

from src.models.base import BaseModelWrapper, ModelResult
from src.models.channel_registry import ChannelRegistry


class PyMCModelWrapper(BaseModelWrapper):
    """Wrapper around PyMC-Marketing's multidimensional MMM."""

    def __init__(self, registry: ChannelRegistry, yearly_seasonality: int = 2) -> None:
        self._registry = registry
        self._yearly_seasonality = yearly_seasonality
        self._mmm: MMM | None = None
        self._df: pd.DataFrame | None = None
        self._target_col: str = "revenue"

    def _build_adstock(self) -> GeometricAdstock:
        """Build GeometricAdstock with per-channel decay priors from registry."""
        l_max = self._registry.get_max_adstock_l_max()
        priors = self._registry.get_pymc_adstock_priors()

        adstock = GeometricAdstock(
            l_max=l_max,
            priors={
                "alpha": Prior(
                    "Beta",
                    alpha=priors["alpha"],
                    beta=priors["beta"],
                    dims="channel",
                ),
            },
        )
        logger.info(f"Built GeometricAdstock with l_max={l_max}")
        return adstock

    def _build_saturation(self) -> LogisticSaturation:
        """Build LogisticSaturation with per-channel priors from registry."""
        sat_priors = self._registry.get_pymc_saturation_priors()

        saturation = LogisticSaturation(
            priors={
                "lam": Prior("Gamma", alpha=3, beta=1, dims="channel"),
                "beta": Prior(
                    "LogNormal",
                    mu=sat_priors["mu"],
                    sigma=sat_priors["sigma"],
                    dims="channel",
                ),
            },
        )
        logger.info("Built LogisticSaturation with per-channel ROI priors")
        return saturation

    def _build_model_config(self) -> dict:
        """Build model_config dict for intercept, controls, likelihood."""
        return {
            "intercept": Prior("Normal", mu=0, sigma=1),
            "gamma_control": Prior("Normal", mu=0, sigma=0.5, dims="control"),
            "gamma_fourier": Prior("Laplace", mu=0, b=0.2, dims="fourier_mode"),
            "likelihood": Prior("Normal", sigma=Prior("HalfNormal", sigma=1.5)),
        }

    def _get_control_columns(self, df: pd.DataFrame) -> list[str]:
        """Identify control columns (non-spend, non-target, non-date, non-trend)."""
        spend_cols = set(self._registry.get_spend_columns())
        impression_cols = set(self._registry.get_impression_columns())
        exclude = spend_cols | impression_cols | {"date_week", "trend", self._target_col}
        # Also exclude Fourier features (handled by yearly_seasonality)
        exclude |= {c for c in df.columns if c.startswith("sin_") or c.startswith("cos_")}

        controls = [c for c in df.columns if c not in exclude and df[c].notna().sum() > 0]
        return controls

    def fit(self, df: pd.DataFrame, target_col: str = "revenue", **kwargs) -> None:
        """Fit PyMC-Marketing MMM on weekly aggregated data.

        Args:
            df: Weekly aggregated DataFrame with date_week, spend cols, target, controls.
            target_col: Name of the target/KPI column.
            **kwargs: Passed to mmm.fit() (e.g., chains, draws, tune, target_accept).
        """
        self._df = df.copy()
        self._target_col = target_col

        channel_cols = self._registry.get_spend_columns()
        # Filter to channels that actually exist in the data
        channel_cols = [c for c in channel_cols if c in df.columns]
        control_cols = self._get_control_columns(df)

        logger.info(f"Channels: {channel_cols}")
        logger.info(f"Controls: {control_cols}")
        logger.info(f"Target: {target_col}")

        adstock = self._build_adstock()
        saturation = self._build_saturation()
        model_config = self._build_model_config()

        self._mmm = MMM(
            date_column="date_week",
            target_column=target_col,
            channel_columns=channel_cols,
            control_columns=control_cols if control_cols else None,
            adstock=adstock,
            saturation=saturation,
            yearly_seasonality=self._yearly_seasonality,
            model_config=model_config,
            dims=None,
        )

        # Prepare X (features) and y (target)
        X = df.drop(columns=[target_col])
        y = df[target_col]

        # Fit defaults
        fit_kwargs = {
            "chains": 4,
            "draws": 1000,
            "tune": 1500,
            "target_accept": 0.85,
            "random_seed": 42,
        }
        fit_kwargs.update(kwargs)

        logger.info("Starting MCMC sampling...")
        self._mmm.fit(X=X, y=y, **fit_kwargs)
        logger.info("MCMC sampling complete")

        # Sample posterior predictive
        self._mmm.sample_posterior_predictive(X, extend_idata=True, combined=True)

    def get_channel_contributions(self) -> pd.DataFrame:
        """Get weekly contribution per channel in original scale."""
        if self._mmm is None:
            raise RuntimeError("Model not fitted yet")

        self._mmm.add_original_scale_contribution_variable(
            var=["channel_contribution"]
        )

        contrib = self._mmm.idata["posterior"]["channel_contribution_original_scale"]
        # Mean across chains and draws: shape (date, channel)
        contrib_mean = contrib.mean(dim=["chain", "draw"]).to_dataframe().reset_index()

        # Pivot to wide format
        contrib_wide = contrib_mean.pivot(
            index="date", columns="channel", values="channel_contribution_original_scale"
        ).reset_index()
        contrib_wide.columns.name = None

        if self._df is not None:
            contrib_wide.insert(0, "date_week", self._df["date_week"].values[: len(contrib_wide)])

        return contrib_wide

    def get_roi(self) -> dict[str, tuple[float, float, float]]:
        """Get ROAS per channel as (mean, lower_5%, upper_95%)."""
        if self._mmm is None or self._df is None:
            raise RuntimeError("Model not fitted yet")

        self._mmm.add_original_scale_contribution_variable(
            var=["channel_contribution"]
        )

        contrib = self._mmm.idata["posterior"]["channel_contribution_original_scale"]
        # Sum over dates: shape (chain, draw, channel)
        total_contrib = contrib.sum(dim="date")

        channel_cols = [c for c in self._registry.get_spend_columns() if c in self._df.columns]
        actual_spend = self._df[channel_cols].sum(axis=0)
        channel_names = [c.removesuffix("_spend") for c in channel_cols]
        spend_xr = xr.DataArray(
            actual_spend.values,
            dims=["channel"],
            coords={"channel": channel_names},
        )

        roas_posterior = total_contrib / spend_xr

        roi_dict = {}
        for ch in channel_names:
            ch_roas = roas_posterior.sel(channel=ch).values.flatten()
            roi_dict[ch] = (
                float(np.mean(ch_roas)),
                float(np.percentile(ch_roas, 5)),
                float(np.percentile(ch_roas, 95)),
            )

        return roi_dict

    def get_results(self) -> ModelResult:
        """Extract full standardized results."""
        if self._mmm is None:
            raise RuntimeError("Model not fitted yet")

        roi = self.get_roi()
        contributions = self.get_channel_contributions()

        # Extract adstock params (mean alpha per channel)
        alpha = self._mmm.idata["posterior"]["adstock_alpha"]
        adstock_params = {
            ch: float(alpha.sel(channel=ch).mean().values)
            for ch in alpha.coords["channel"].values
        }

        # Model fit metrics
        idata = self._mmm.idata
        y_pred = idata["posterior_predictive"]["y"].mean(dim=["chain", "draw"]).values
        y_true = self._df[self._target_col].values[: len(y_pred)]
        mape = float(np.mean(np.abs((y_true - y_pred) / y_true)) * 100)
        ss_res = np.sum((y_true - y_pred) ** 2)
        ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
        r_squared = float(1 - ss_res / ss_tot) if ss_tot > 0 else 0.0

        return ModelResult(
            roi_by_channel=roi,
            channel_contributions=contributions,
            adstock_params=adstock_params,
            baseline_contribution=0.0,  # TODO: extract from intercept
            model_fit_metrics={"mape": mape, "r_squared": r_squared},
            inference_data=idata,
            metadata={"model": "pymc-marketing", "n_channels": len(roi)},
        )

    def optimize_budget(
        self,
        total_budget: float,
        budget_bounds: dict[str, tuple[float, float]] | None = None,
    ) -> dict[str, float]:
        """Optimize budget allocation using PyMC-Marketing's built-in optimizer."""
        if self._mmm is None:
            raise RuntimeError("Model not fitted yet")

        if budget_bounds is None:
            constraints = self._registry.get_optimizer_constraints()
            budget_bounds = {
                f"{ch}_spend": (v["min"], v["max"])
                for ch, v in constraints.items()
            }

        allocation, _ = self._mmm.optimize_budget(
            budget=total_budget,
            num_periods=4,
            budget_bounds=budget_bounds,
        )

        return {
            col.removesuffix("_spend"): float(val)
            for col, val in allocation.items()
        }
