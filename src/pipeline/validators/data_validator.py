"""Data validation for MMM pipeline.

Validates schema, data quality, and cross-tab consistency of data
fetched from Google Sheets before it enters storage/models.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd
from loguru import logger


@dataclass
class ValidationReport:
    """Result of data validation. Errors are blocking, warnings are logged."""

    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0

    def log(self) -> None:
        for w in self.warnings:
            logger.warning(f"[VALIDATION WARNING] {w}")
        for e in self.errors:
            logger.error(f"[VALIDATION ERROR] {e}")
        if self.is_valid:
            logger.info("Validation passed")
        else:
            logger.error(f"Validation failed with {len(self.errors)} error(s)")


class DataValidator:
    """Validates MMM data from Google Sheets."""

    def validate_all(
        self,
        media_spend: pd.DataFrame,
        kpi: pd.DataFrame,
        external_factors: pd.DataFrame,
        channel_config: pd.DataFrame,
    ) -> ValidationReport:
        report = ValidationReport()

        self._validate_media_spend(media_spend, report)
        self._validate_kpi(kpi, report)
        self._validate_external_factors(external_factors, report)
        self._validate_channel_config(channel_config, report)
        self._validate_cross_tab(media_spend, kpi, external_factors, report)
        self._validate_cross_ref(media_spend, channel_config, report)

        report.log()
        return report

    def _validate_media_spend(self, df: pd.DataFrame, report: ValidationReport) -> None:
        if "date" not in df.columns:
            report.errors.append("media_spend: missing 'date' column")
            return

        spend_cols = [c for c in df.columns if c.endswith("_spend")]
        if not spend_cols:
            report.errors.append("media_spend: no '*_spend' columns found")
            return

        # Check for duplicate dates
        dupes = df["date"].duplicated()
        if dupes.any():
            n = dupes.sum()
            report.errors.append(f"media_spend: {n} duplicate date(s) found")

        # Check spend columns are non-negative
        for col in spend_cols:
            if (df[col] < 0).any():
                report.errors.append(f"media_spend: negative values in '{col}'")

        # Warn on date gaps
        if len(df) > 1:
            dates = df["date"].sort_values()
            gaps = dates.diff().dt.days
            big_gaps = gaps[gaps > 1].dropna()
            if len(big_gaps) > 0:
                report.warnings.append(
                    f"media_spend: {len(big_gaps)} gap(s) in dates "
                    f"(max gap: {int(big_gaps.max())} days)"
                )

        # Warn on channels with too many consecutive zeros
        for col in spend_cols:
            consecutive_zeros = self._max_consecutive_zeros(df[col])
            if consecutive_zeros > 7:
                channel = col.removesuffix("_spend")
                report.warnings.append(
                    f"media_spend: '{channel}' has {consecutive_zeros} consecutive days of zero spend"
                )

        # Warn on outliers (> 3 std from mean) for active channels
        for col in spend_cols:
            nonzero = df[col][df[col] > 0]
            if len(nonzero) > 10:
                mean = nonzero.mean()
                std = nonzero.std()
                if std > 0:
                    outliers = nonzero[abs(nonzero - mean) > 3 * std]
                    if len(outliers) > 0:
                        channel = col.removesuffix("_spend")
                        report.warnings.append(
                            f"media_spend: '{channel}' has {len(outliers)} outlier value(s) (>3 std)"
                        )

    def _validate_kpi(self, df: pd.DataFrame, report: ValidationReport) -> None:
        if "date" not in df.columns:
            report.errors.append("kpi: missing 'date' column")
            return

        if "revenue" not in df.columns:
            report.errors.append("kpi: missing 'revenue' column")
            return

        dupes = df["date"].duplicated()
        if dupes.any():
            report.errors.append(f"kpi: {dupes.sum()} duplicate date(s) found")

        # Warn if revenue has too many consecutive zeros
        consecutive_zeros = self._max_consecutive_zeros(df["revenue"].fillna(0))
        if consecutive_zeros > 3:
            report.warnings.append(
                f"kpi: revenue has {consecutive_zeros} consecutive days of zero/null"
            )

    def _validate_external_factors(self, df: pd.DataFrame, report: ValidationReport) -> None:
        if "date" not in df.columns:
            report.errors.append("external_factors: missing 'date' column")
            return

        dupes = df["date"].duplicated()
        if dupes.any():
            report.errors.append(f"external_factors: {dupes.sum()} duplicate date(s) found")

    def _validate_channel_config(self, df: pd.DataFrame, report: ValidationReport) -> None:
        required_cols = ["channel_name", "channel_type"]
        for col in required_cols:
            if col not in df.columns:
                report.errors.append(f"channel_config: missing '{col}' column")
                return

        dupes = df["channel_name"].duplicated()
        if dupes.any():
            report.errors.append(
                f"channel_config: duplicate channel_name(s): "
                f"{df['channel_name'][dupes].tolist()}"
            )

        valid_types = {
            "digital", "offline_tv", "offline_radio", "offline_ooh",
            "influencer", "events", "sponsorship", "trade",
        }
        invalid = df[~df["channel_type"].isin(valid_types)]
        if len(invalid) > 0:
            report.errors.append(
                f"channel_config: invalid channel_type(s): "
                f"{invalid['channel_type'].tolist()}"
            )

    def _validate_cross_tab(
        self,
        media_spend: pd.DataFrame,
        kpi: pd.DataFrame,
        external_factors: pd.DataFrame,
        report: ValidationReport,
    ) -> None:
        """Check that date ranges align across the 3 time-series tabs."""
        tabs = {
            "media_spend": media_spend,
            "kpi": kpi,
            "external_factors": external_factors,
        }

        date_ranges = {}
        for name, df in tabs.items():
            if "date" in df.columns and len(df) > 0:
                date_ranges[name] = (df["date"].min(), df["date"].max())

        if len(date_ranges) < 2:
            return

        starts = {name: r[0] for name, r in date_ranges.items()}
        ends = {name: r[1] for name, r in date_ranges.items()}

        # Warn if start dates differ by more than 7 days
        start_vals = list(starts.values())
        if (max(start_vals) - min(start_vals)).days > 7:
            report.warnings.append(
                f"Cross-tab: start dates differ significantly: {starts}"
            )

        # Warn if end dates differ by more than 7 days
        end_vals = list(ends.values())
        if (max(end_vals) - min(end_vals)).days > 7:
            report.warnings.append(
                f"Cross-tab: end dates differ significantly: {ends}"
            )

        # Warn if less than 2 years of data
        if "media_spend" in date_ranges:
            date_range = date_ranges["media_spend"]
            total_weeks = (date_range[1] - date_range[0]).days / 7
            if total_weeks < 104:
                report.warnings.append(
                    f"media_spend: only {total_weeks:.0f} weeks of data "
                    f"(recommended: 104+ weeks / 2 years)"
                )

    def _validate_cross_ref(
        self,
        media_spend: pd.DataFrame,
        channel_config: pd.DataFrame,
        report: ValidationReport,
    ) -> None:
        """Check that every *_spend column has a matching channel_config entry."""
        spend_channels = {
            c.removesuffix("_spend")
            for c in media_spend.columns
            if c.endswith("_spend")
        }

        if "channel_name" not in channel_config.columns:
            return

        config_channels = set(channel_config["channel_name"].astype(str))

        missing_config = spend_channels - config_channels
        if missing_config:
            report.errors.append(
                f"Cross-ref: channels in media_spend without channel_config entry: {missing_config}"
            )

        extra_config = config_channels - spend_channels
        if extra_config:
            report.warnings.append(
                f"Cross-ref: channels in channel_config without media_spend data: {extra_config}"
            )

    @staticmethod
    def _max_consecutive_zeros(series: pd.Series) -> int:
        """Return the max consecutive count of zeros in a series."""
        if len(series) == 0:
            return 0
        is_zero = (series == 0) | series.isna()
        groups = (~is_zero).cumsum()
        if not is_zero.any():
            return 0
        return int(is_zero.groupby(groups).sum().max())
