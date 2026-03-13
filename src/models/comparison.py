"""Model comparison framework: side-by-side analysis of PyMC-Marketing and Meridian."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from loguru import logger

from src.models.base import ModelResult


@dataclass
class ComparisonResult:
    """Result of comparing two MMM models."""

    # Per-channel ROI comparison
    roi_comparison: pd.DataFrame  # columns: channel, pymc_roi, meridian_roi, diff, agreement
    # Ranking correlation (Spearman)
    ranking_correlation: float
    # Channels where models disagree significantly
    disagreement_channels: list[str]
    # Ensemble ROI (weighted average by model quality)
    ensemble_roi: dict[str, tuple[float, float, float]]
    # Model quality scores
    model_scores: dict[str, float]
    # Overall agreement level
    agreement_level: str  # "high", "moderate", "low"


def compare_models(
    pymc_result: ModelResult,
    meridian_result: ModelResult,
    quality_weight: float = 0.7,
) -> ComparisonResult:
    """Compare PyMC-Marketing and Meridian model results.

    Args:
        pymc_result: Results from PyMC-Marketing model.
        meridian_result: Results from Meridian model.
        quality_weight: Weight given to better-fitting model in ensemble (0.5-1.0).
    """
    pymc_roi = pymc_result.roi_by_channel
    meridian_roi = meridian_result.roi_by_channel
    common_channels = sorted(set(pymc_roi) & set(meridian_roi))

    if not common_channels:
        raise ValueError("No common channels between models")

    # Build comparison DataFrame
    rows = []
    for ch in common_channels:
        p_mean, p_lo, p_hi = pymc_roi[ch]
        m_mean, m_lo, m_hi = meridian_roi[ch]
        diff = abs(p_mean - m_mean)
        # Agreement: do confidence intervals overlap?
        overlap = min(p_hi, m_hi) > max(p_lo, m_lo)
        rows.append({
            "channel": ch,
            "pymc_roi": round(p_mean, 3),
            "pymc_ci": f"[{p_lo:.3f}, {p_hi:.3f}]",
            "meridian_roi": round(m_mean, 3),
            "meridian_ci": f"[{m_lo:.3f}, {m_hi:.3f}]",
            "diff": round(diff, 3),
            "ci_overlap": overlap,
        })

    comparison_df = pd.DataFrame(rows)

    # Spearman ranking correlation
    pymc_rank = sorted(common_channels, key=lambda c: pymc_roi[c][0], reverse=True)
    meridian_rank = sorted(common_channels, key=lambda c: meridian_roi[c][0], reverse=True)
    n = len(common_channels)
    d_sq = sum((pymc_rank.index(c) - meridian_rank.index(c)) ** 2 for c in common_channels)
    spearman = 1 - (6 * d_sq) / (n * (n**2 - 1)) if n > 1 else 1.0

    # Disagreement: channels where ranking differs by 2+ positions
    disagreements = []
    for ch in common_channels:
        rank_diff = abs(pymc_rank.index(ch) - meridian_rank.index(ch))
        if rank_diff >= 2:
            disagreements.append(ch)

    # Model quality scores (based on R² and MAPE)
    pymc_r2 = pymc_result.model_fit_metrics.get("r_squared", 0)
    meridian_r2 = meridian_result.model_fit_metrics.get("r_squared", 0)
    pymc_mape = pymc_result.model_fit_metrics.get("mape", 100)
    meridian_mape = meridian_result.model_fit_metrics.get("mape", 100)

    # Composite score: higher R² is better, lower MAPE is better
    pymc_score = pymc_r2 * 100 - pymc_mape
    meridian_score = meridian_r2 * 100 - meridian_mape

    total_score = abs(pymc_score) + abs(meridian_score)
    if total_score > 0:
        pymc_weight = (pymc_score / total_score) * quality_weight + (1 - quality_weight) * 0.5
        meridian_weight = 1 - pymc_weight
    else:
        pymc_weight = meridian_weight = 0.5

    # Clamp weights
    pymc_weight = max(0.2, min(0.8, pymc_weight))
    meridian_weight = 1 - pymc_weight

    # Ensemble ROI
    ensemble = {}
    for ch in common_channels:
        p_mean, p_lo, p_hi = pymc_roi[ch]
        m_mean, m_lo, m_hi = meridian_roi[ch]
        e_mean = p_mean * pymc_weight + m_mean * meridian_weight
        e_lo = p_lo * pymc_weight + m_lo * meridian_weight
        e_hi = p_hi * pymc_weight + m_hi * meridian_weight
        ensemble[ch] = (round(e_mean, 3), round(e_lo, 3), round(e_hi, 3))

    # Agreement level
    if spearman >= 0.8 and len(disagreements) == 0:
        agreement = "high"
    elif spearman >= 0.5:
        agreement = "moderate"
    else:
        agreement = "low"

    logger.info(
        f"Model comparison: spearman={spearman:.2f}, agreement={agreement}, "
        f"disagreements={disagreements}"
    )

    return ComparisonResult(
        roi_comparison=comparison_df,
        ranking_correlation=round(spearman, 3),
        disagreement_channels=disagreements,
        ensemble_roi=ensemble,
        model_scores={"pymc": round(pymc_score, 2), "meridian": round(meridian_score, 2)},
        agreement_level=agreement,
    )
