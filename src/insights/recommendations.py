"""Actionable recommendations engine based on model results and alerts."""

from __future__ import annotations

from src.models.base import ModelResult
from src.optimizer.allocator import AllocationResult


def generate_recommendations(
    result: ModelResult,
    allocation: AllocationResult | None = None,
    current_spend: dict[str, float] | None = None,
) -> list[dict]:
    """Generate prioritized recommendations for the marketing team."""
    recs = []
    roi = result.roi_by_channel
    current_spend = current_spend or {}

    # 1. Reallocate from low-ROI to high-ROI channels
    sorted_by_roi = sorted(roi.items(), key=lambda x: x[1][0], reverse=True)
    if len(sorted_by_roi) >= 2:
        best_ch = sorted_by_roi[0][0]
        worst_ch = sorted_by_roi[-1][0]
        best_roi = sorted_by_roi[0][1][0]
        worst_roi = sorted_by_roi[-1][1][0]

        if best_roi > worst_roi * 2:
            recs.append({
                "action": "realocar",
                "priority": 1,
                "summary": f"Mover budget de {worst_ch} para {best_ch}",
                "detail": (
                    f"{best_ch} (ROI {best_roi:.2f}x) rende {best_roi/max(worst_roi,0.01):.1f}x "
                    f"mais que {worst_ch} (ROI {worst_roi:.2f}x). "
                    f"Realocar gradualmente."
                ),
                "channels": [best_ch, worst_ch],
            })

    # 2. Increase spend on high-ROI unsaturated channels
    if allocation:
        for ch, recommended in allocation.allocations.items():
            current = current_spend.get(ch, 0)
            if recommended > current * 1.2 and ch in roi and roi[ch][0] > 1.0:
                recs.append({
                    "action": "aumentar",
                    "priority": 2,
                    "summary": f"Aumentar {ch} em {((recommended-current)/max(current,1))*100:.0f}%",
                    "detail": (
                        f"Otimizador sugere R${recommended:,.0f}/semana vs "
                        f"R${current:,.0f} atual. ROI de {roi[ch][0]:.2f}x."
                    ),
                    "channels": [ch],
                })

    # 3. Test variation on uncertain channels
    for ch, (mean, lo, hi) in roi.items():
        ci_width = hi - lo
        if ci_width > mean and mean > 0:
            recs.append({
                "action": "testar",
                "priority": 3,
                "summary": f"Testar variacao de spend em {ch}",
                "detail": (
                    f"Alta incerteza no ROI de {ch} (IC: [{lo:.2f}, {hi:.2f}]). "
                    f"Variar spend em +/-30% por 4 semanas para calibrar o modelo."
                ),
                "channels": [ch],
            })

    recs.sort(key=lambda x: x["priority"])
    return recs
