"""Weekly insights report generator.

Generates top actionable recommendations from the latest model results.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from loguru import logger

from src.models.base import ModelResult


@dataclass
class Insight:
    type: str  # "recommendation" | "alert" | "opportunity"
    priority: int  # 1=high, 2=medium, 3=low
    title: str
    description: str
    channel: str | None = None
    impact_estimate: str | None = None


def generate_weekly_insights(
    result: ModelResult,
    total_budget: float | None = None,
) -> list[Insight]:
    """Generate actionable insights from model results.

    Analyzes ROI, saturation, and budget allocation to produce
    top recommendations for the marketing team.
    """
    insights: list[Insight] = []
    roi = result.roi_by_channel
    adstock = result.adstock_params

    if not roi:
        return insights

    # Sort channels by ROI
    sorted_channels = sorted(roi.items(), key=lambda x: x[1][0], reverse=True)

    # 1. Top performing channel
    best_ch, (best_roi, best_lo, best_hi) = sorted_channels[0]
    insights.append(Insight(
        type="recommendation",
        priority=1,
        title=f"Canal com maior ROI: {best_ch}",
        description=(
            f"{best_ch} tem o maior retorno (ROI: {best_roi:.2f}, "
            f"IC 90%: [{best_lo:.2f}, {best_hi:.2f}]). "
            f"Considere aumentar investimento neste canal."
        ),
        channel=best_ch,
        impact_estimate=f"ROI {best_roi:.2f}x",
    ))

    # 2. Worst performing channel
    worst_ch, (worst_roi, worst_lo, worst_hi) = sorted_channels[-1]
    if worst_roi < 0.5:
        insights.append(Insight(
            type="alert",
            priority=1,
            title=f"Canal com baixo retorno: {worst_ch}",
            description=(
                f"{worst_ch} tem ROI de apenas {worst_roi:.2f}. "
                f"Considere reduzir investimento ou revisar estrategia criativa."
            ),
            channel=worst_ch,
            impact_estimate=f"ROI {worst_roi:.2f}x",
        ))

    # 3. High uncertainty channels (wide confidence intervals)
    for ch, (mean, lo, hi) in roi.items():
        ci_width = hi - lo
        if ci_width > mean * 2 and mean > 0:
            insights.append(Insight(
                type="alert",
                priority=2,
                title=f"Alta incerteza: {ch}",
                description=(
                    f"O intervalo de confianca de {ch} e muito amplo "
                    f"([{lo:.2f}, {hi:.2f}]). "
                    f"Recomendamos testes controlados para validar o ROI."
                ),
                channel=ch,
            ))

    # 4. Underused levers (high ROI but potentially low spend)
    if len(sorted_channels) >= 3:
        top_3 = sorted_channels[:3]
        for ch, (roi_mean, _, _) in top_3[1:]:
            if roi_mean > 1.5:
                insights.append(Insight(
                    type="opportunity",
                    priority=2,
                    title=f"Canal subutilizado: {ch}",
                    description=(
                        f"{ch} tem ROI alto ({roi_mean:.2f}x) e pode estar abaixo do "
                        f"ponto de saturacao. Aumente investimento gradualmente."
                    ),
                    channel=ch,
                    impact_estimate=f"ROI {roi_mean:.2f}x",
                ))

    # 5. Adstock insights (channels with very fast or slow decay)
    for ch, decay in adstock.items():
        if decay > 0.7:
            insights.append(Insight(
                type="recommendation",
                priority=3,
                title=f"Efeito de longo prazo: {ch}",
                description=(
                    f"{ch} tem alto carryover (decay: {decay:.2f}). "
                    f"Investimentos geram retorno por varias semanas."
                ),
                channel=ch,
            ))
        elif decay < 0.15:
            insights.append(Insight(
                type="recommendation",
                priority=3,
                title=f"Efeito imediato: {ch}",
                description=(
                    f"{ch} tem decay rapido ({decay:.2f}). "
                    f"Ideal para campanhas taticas de curto prazo."
                ),
                channel=ch,
            ))

    # Sort by priority
    insights.sort(key=lambda x: x.priority)

    logger.info(f"Generated {len(insights)} weekly insights")
    return insights
