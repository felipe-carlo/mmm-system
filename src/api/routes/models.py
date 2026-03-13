"""Model routes: get results, compare models, trigger training."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from src.api.schemas.models import (
    ModelComparisonResponse,
    ModelResultResponse,
    ROIEntry,
)

router = APIRouter(prefix="/api/models", tags=["models"])

# In-memory store for latest model results (replaced by DB/MLflow in production)
_model_results: dict[str, dict] = {}


def store_model_result(model_type: str, result: dict) -> None:
    """Store model result (called after training)."""
    _model_results[model_type] = result


@router.get("/results/{model_type}", response_model=ModelResultResponse)
def get_model_results(model_type: str):
    """Get results from the latest model run."""
    if model_type not in ("pymc", "meridian"):
        raise HTTPException(status_code=400, detail="model_type must be 'pymc' or 'meridian'")

    result = _model_results.get(model_type)
    if not result:
        raise HTTPException(status_code=404, detail=f"No results for model '{model_type}'")

    roi_entries = [
        ROIEntry(channel=ch, roi_mean=v[0], roi_lower=v[1], roi_upper=v[2])
        for ch, v in result["roi_by_channel"].items()
    ]

    return ModelResultResponse(
        model_type=model_type,
        roi_by_channel=roi_entries,
        model_fit=result.get("model_fit_metrics", {}),
        adstock_params=result.get("adstock_params", {}),
    )


@router.get("/compare", response_model=ModelComparisonResponse)
def compare_models():
    """Compare PyMC-Marketing and Meridian results side by side."""
    response = ModelComparisonResponse()

    for model_type in ("pymc", "meridian"):
        result = _model_results.get(model_type)
        if result:
            roi_entries = [
                ROIEntry(channel=ch, roi_mean=v[0], roi_lower=v[1], roi_upper=v[2])
                for ch, v in result["roi_by_channel"].items()
            ]
            model_resp = ModelResultResponse(
                model_type=model_type,
                roi_by_channel=roi_entries,
                model_fit=result.get("model_fit_metrics", {}),
                adstock_params=result.get("adstock_params", {}),
            )
            if model_type == "pymc":
                response.pymc = model_resp
            else:
                response.meridian = model_resp

    # Calculate agreement if both models exist
    if response.pymc and response.meridian:
        pymc_roi = {r.channel: r.roi_mean for r in response.pymc.roi_by_channel}
        meridian_roi = {r.channel: r.roi_mean for r in response.meridian.roi_by_channel}
        common = set(pymc_roi) & set(meridian_roi)
        if common:
            # Spearman-like ranking correlation
            pymc_rank = sorted(common, key=lambda c: pymc_roi[c], reverse=True)
            meridian_rank = sorted(common, key=lambda c: meridian_roi[c], reverse=True)
            n = len(common)
            d_sq = sum(
                (pymc_rank.index(c) - meridian_rank.index(c)) ** 2 for c in common
            )
            response.ranking_correlation = 1 - (6 * d_sq) / (n * (n**2 - 1)) if n > 1 else 1.0

    return response
