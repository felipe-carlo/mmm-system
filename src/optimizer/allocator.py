"""Budget allocation engine using saturation curves and ROI data."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from loguru import logger

from src.models.base import ModelResult


@dataclass
class AllocationResult:
    """Result of budget optimization."""

    allocations: dict[str, float]  # channel -> recommended weekly spend
    expected_total_contribution: float
    marginal_roi: dict[str, float]  # channel -> marginal ROI at recommended spend


def optimize_budget_allocation(
    result: ModelResult,
    total_budget: float,
    constraints: dict[str, dict[str, float]] | None = None,
    current_allocation: dict[str, float] | None = None,
) -> AllocationResult:
    """Optimize budget allocation based on model results.

    Uses a simple ROI-proportional allocation with constraints,
    then adjusts for diminishing returns using the adstock parameters.

    Args:
        result: Model results with ROI and adstock params.
        total_budget: Total weekly budget to allocate.
        constraints: Per-channel {min, max} constraints.
        current_allocation: Current spend per channel (for comparison).
    """
    roi = result.roi_by_channel
    channels = list(roi.keys())
    n = len(channels)

    if not channels:
        raise ValueError("No channels in model results")

    constraints = constraints or {}

    # Step 1: Initial allocation proportional to ROI
    roi_means = {ch: max(v[0], 0.01) for ch, v in roi.items()}
    total_roi = sum(roi_means.values())
    initial = {ch: total_budget * (roi_means[ch] / total_roi) for ch in channels}

    # Step 2: Apply constraints
    allocation = {}
    remaining = total_budget
    constrained_channels = set()

    for ch in channels:
        ch_constraints = constraints.get(ch, {})
        min_budget = ch_constraints.get("min", 0)
        max_budget = ch_constraints.get("max", float("inf"))

        if initial[ch] < min_budget:
            allocation[ch] = min_budget
            constrained_channels.add(ch)
            remaining -= min_budget
        elif initial[ch] > max_budget:
            allocation[ch] = max_budget
            constrained_channels.add(ch)
            remaining -= max_budget

    # Distribute remaining budget among unconstrained channels
    unconstrained = [ch for ch in channels if ch not in constrained_channels]
    if unconstrained:
        unc_total_roi = sum(roi_means[ch] for ch in unconstrained)
        for ch in unconstrained:
            allocation[ch] = remaining * (roi_means[ch] / unc_total_roi)

    # Step 3: Calculate marginal ROI (simple approximation)
    # Higher adstock decay = faster diminishing returns
    adstock = result.adstock_params
    marginal_roi = {}
    for ch in channels:
        base_roi = roi_means[ch]
        decay = adstock.get(ch, 0.5)
        # Diminishing returns factor: higher decay = less diminishing
        diminishing = 1 / (1 + allocation[ch] / (total_budget / n))
        marginal_roi[ch] = round(base_roi * diminishing, 4)

    # Expected total contribution
    expected_contribution = sum(allocation[ch] * roi_means[ch] for ch in channels)

    logger.info(
        f"Budget optimization: {total_budget:.0f} across {n} channels, "
        f"expected contribution: {expected_contribution:.0f}"
    )

    return AllocationResult(
        allocations={ch: round(v, 2) for ch, v in allocation.items()},
        expected_total_contribution=round(expected_contribution, 2),
        marginal_roi=marginal_roi,
    )
