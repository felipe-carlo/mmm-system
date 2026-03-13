"""What-if scenario engine for budget simulation."""

from __future__ import annotations

from dataclasses import dataclass

from loguru import logger

from src.models.base import ModelResult


@dataclass
class ScenarioResult:
    """Result of a what-if scenario simulation."""

    baseline_revenue: float
    projected_revenue: float
    revenue_change: float
    revenue_change_pct: float
    channel_impacts: dict[str, float]


def run_scenario(
    result: ModelResult,
    changes: dict[str, float],
    baseline_revenue: float,
    current_spend: dict[str, float] | None = None,
) -> ScenarioResult:
    """Simulate impact of changing spend on specific channels.

    Args:
        result: Model results with ROI data.
        changes: channel_name -> new weekly spend.
        baseline_revenue: Current baseline weekly revenue.
        current_spend: Current spend per channel (for delta calculation).
    """
    roi = result.roi_by_channel
    current_spend = current_spend or {}

    channel_impacts = {}
    total_impact = 0.0

    for channel, new_spend in changes.items():
        if channel not in roi:
            logger.warning(f"Channel '{channel}' not in model, skipping")
            continue

        roi_mean = roi[channel][0]
        old_spend = current_spend.get(channel, 0)
        delta_spend = new_spend - old_spend
        impact = delta_spend * roi_mean
        channel_impacts[channel] = round(impact, 2)
        total_impact += impact

    projected = baseline_revenue + total_impact
    change_pct = (total_impact / baseline_revenue * 100) if baseline_revenue else 0

    logger.info(
        f"Scenario: {len(changes)} channel changes, "
        f"projected impact: {total_impact:+.0f} ({change_pct:+.1f}%)"
    )

    return ScenarioResult(
        baseline_revenue=round(baseline_revenue, 2),
        projected_revenue=round(projected, 2),
        revenue_change=round(total_impact, 2),
        revenue_change_pct=round(change_pct, 2),
        channel_impacts=channel_impacts,
    )
