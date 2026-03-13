"""Optimizer routes: budget allocation and scenario simulation."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from src.api.schemas.models import (
    BudgetAllocation,
    BudgetRequest,
    BudgetResponse,
    ForecastRequest,
    ForecastResponse,
    ScenarioRequest,
    ScenarioResponse,
)

router = APIRouter(prefix="/api/optimizer", tags=["optimizer"])


@router.post("/allocate", response_model=BudgetResponse)
def allocate_budget(request: BudgetRequest):
    """Optimize budget allocation across channels."""
    from src.api.routes.models import _model_results

    result = _model_results.get("pymc")
    if not result:
        raise HTTPException(status_code=404, detail="No model results. Train a model first.")

    roi = result.get("roi_by_channel", {})
    if not roi:
        raise HTTPException(status_code=404, detail="No ROI data available")

    # Simple proportional allocation based on ROI
    total_roi = sum(max(v[0], 0.01) for v in roi.values())
    allocations = []
    for channel, (roi_mean, roi_lower, roi_upper) in roi.items():
        weight = max(roi_mean, 0.01) / total_roi
        recommended = request.total_budget * weight
        current = request.total_budget / len(roi)  # assume equal distribution as baseline
        change = ((recommended - current) / current * 100) if current > 0 else 0

        allocations.append(
            BudgetAllocation(
                channel=channel,
                current_spend=round(current, 2),
                recommended_spend=round(recommended, 2),
                change_pct=round(change, 1),
            )
        )

    return BudgetResponse(
        allocations=allocations,
        total_budget=request.total_budget,
        expected_roi_lift_pct=None,
    )


@router.post("/scenario", response_model=ScenarioResponse)
def run_scenario(request: ScenarioRequest):
    """Run a what-if scenario: what happens if I change spend on channel X?"""
    from src.api.routes.models import _model_results

    result = _model_results.get("pymc")
    if not result:
        raise HTTPException(status_code=404, detail="No model results. Train a model first.")

    roi = result.get("roi_by_channel", {})
    baseline_revenue = result.get("model_fit_metrics", {}).get("total_revenue", 100000)

    channel_impacts = {}
    total_impact = 0.0
    for channel, new_spend in request.changes.items():
        if channel in roi:
            roi_mean = roi[channel][0]
            impact = new_spend * roi_mean
            channel_impacts[channel] = round(impact, 2)
            total_impact += impact

    projected = baseline_revenue + total_impact
    change_pct = ((projected - baseline_revenue) / baseline_revenue * 100) if baseline_revenue else 0

    return ScenarioResponse(
        baseline_revenue=round(baseline_revenue, 2),
        projected_revenue=round(projected, 2),
        revenue_change_pct=round(change_pct, 2),
        channel_impacts=channel_impacts,
    )


@router.post("/forecast", response_model=ForecastResponse)
def forecast_revenue(request: ForecastRequest):
    """Forecast revenue based on a media plan."""
    from src.api.routes.models import _model_results

    result = _model_results.get("pymc")
    if not result:
        raise HTTPException(status_code=404, detail="No model results. Train a model first.")

    roi = result.get("roi_by_channel", {})
    baseline_weekly = result.get("model_fit_metrics", {}).get("avg_weekly_revenue", 25000)

    weeks = []
    for w in range(1, request.num_weeks + 1):
        media_contribution = sum(
            request.media_plan.get(ch, 0) * roi.get(ch, (0,))[0]
            for ch in request.media_plan
        )
        base = baseline_weekly + media_contribution
        weeks.append({
            "week": w,
            "revenue_base": round(base, 2),
            "revenue_optimistic": round(base * 1.15, 2),
            "revenue_pessimistic": round(base * 0.85, 2),
        })

    total_base = sum(w["revenue_base"] for w in weeks)
    return ForecastResponse(
        weeks=weeks,
        total_revenue_base=round(total_base, 2),
        total_revenue_optimistic=round(total_base * 1.15, 2),
        total_revenue_pessimistic=round(total_base * 0.85, 2),
    )
