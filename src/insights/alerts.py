"""Anomaly and opportunity alerts for real-time monitoring."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
from loguru import logger


@dataclass
class Alert:
    level: str  # "critical" | "warning" | "info"
    title: str
    message: str
    channel: str | None = None


def check_spend_anomalies(
    daily_spend: pd.DataFrame,
    lookback_days: int = 30,
    threshold_std: float = 2.5,
) -> list[Alert]:
    """Check for anomalous spend patterns in recent data."""
    alerts = []
    spend_cols = [c for c in daily_spend.columns if c.endswith("_spend")]

    if len(daily_spend) < lookback_days:
        return alerts

    recent = daily_spend.tail(lookback_days)

    for col in spend_cols:
        channel = col.removesuffix("_spend")
        mean = recent[col].mean()
        std = recent[col].std()

        if std == 0:
            continue

        latest = daily_spend[col].iloc[-1]
        z_score = (latest - mean) / std

        if abs(z_score) > threshold_std:
            direction = "acima" if z_score > 0 else "abaixo"
            alerts.append(Alert(
                level="warning",
                title=f"Spend anomalo: {channel}",
                message=(
                    f"Spend de {channel} hoje (R${latest:,.0f}) esta {abs(z_score):.1f} "
                    f"desvios padrao {direction} da media dos ultimos {lookback_days} dias "
                    f"(media: R${mean:,.0f})."
                ),
                channel=channel,
            ))

    # Check for channels with zero spend for 3+ consecutive days
    for col in spend_cols:
        channel = col.removesuffix("_spend")
        last_3 = daily_spend[col].tail(3)
        if (last_3 == 0).all():
            alerts.append(Alert(
                level="critical",
                title=f"Canal parado: {channel}",
                message=f"{channel} esta com zero spend ha 3+ dias consecutivos.",
                channel=channel,
            ))

    logger.info(f"Spend anomaly check: {len(alerts)} alert(s)")
    return alerts


def check_revenue_anomalies(
    daily_kpi: pd.DataFrame,
    lookback_days: int = 30,
    threshold_pct: float = 0.2,
) -> list[Alert]:
    """Check for anomalous revenue drops."""
    alerts = []

    if "revenue" not in daily_kpi.columns or len(daily_kpi) < lookback_days:
        return alerts

    recent_avg = daily_kpi["revenue"].tail(lookback_days).mean()
    last_7_avg = daily_kpi["revenue"].tail(7).mean()

    if recent_avg > 0:
        change_pct = (last_7_avg - recent_avg) / recent_avg

        if change_pct < -threshold_pct:
            alerts.append(Alert(
                level="critical",
                title="Queda de receita",
                message=(
                    f"Receita media dos ultimos 7 dias (R${last_7_avg:,.0f}) caiu "
                    f"{abs(change_pct)*100:.0f}% vs media de {lookback_days} dias "
                    f"(R${recent_avg:,.0f})."
                ),
            ))
        elif change_pct > threshold_pct:
            alerts.append(Alert(
                level="info",
                title="Aumento de receita",
                message=(
                    f"Receita media dos ultimos 7 dias (R${last_7_avg:,.0f}) subiu "
                    f"{change_pct*100:.0f}% vs media de {lookback_days} dias."
                ),
            ))

    return alerts
