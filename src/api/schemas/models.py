"""Pydantic schemas for API request/response models."""

from __future__ import annotations

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str


class SyncRequest(BaseModel):
    spreadsheet_url: str | None = None


class SyncResponse(BaseModel):
    status: str
    rows_fetched: int
    channels_discovered: list[str]
    warnings: list[str]


class ChannelInfo(BaseModel):
    name: str
    channel_type: str
    has_impressions: bool
    adstock_l_max_weeks: int
    adstock_decay_prior_mu: float
    roi_prior_mu: float
    min_budget_weekly: float
    max_budget_weekly: float


class ChannelListResponse(BaseModel):
    channels: list[ChannelInfo]
    total: int


class ROIEntry(BaseModel):
    channel: str
    roi_mean: float
    roi_lower: float
    roi_upper: float


class ModelResultResponse(BaseModel):
    model_type: str
    roi_by_channel: list[ROIEntry]
    model_fit: dict[str, float]
    adstock_params: dict[str, float]


class ModelComparisonResponse(BaseModel):
    pymc: ModelResultResponse | None = None
    meridian: ModelResultResponse | None = None
    agreement_score: float | None = None
    ranking_correlation: float | None = None


class BudgetRequest(BaseModel):
    total_budget: float
    num_periods: int = 4


class BudgetAllocation(BaseModel):
    channel: str
    current_spend: float
    recommended_spend: float
    change_pct: float


class BudgetResponse(BaseModel):
    allocations: list[BudgetAllocation]
    total_budget: float
    expected_roi_lift_pct: float | None = None


class ScenarioRequest(BaseModel):
    changes: dict[str, float]  # channel_name -> new_weekly_spend


class ScenarioResponse(BaseModel):
    baseline_revenue: float
    projected_revenue: float
    revenue_change_pct: float
    channel_impacts: dict[str, float]


class ForecastRequest(BaseModel):
    media_plan: dict[str, float]  # channel -> weekly spend
    num_weeks: int = 4


class ForecastResponse(BaseModel):
    weeks: list[dict[str, float]]  # [{week, revenue_base, revenue_optimistic, revenue_pessimistic}]
    total_revenue_base: float
    total_revenue_optimistic: float
    total_revenue_pessimistic: float


class InsightItem(BaseModel):
    type: str  # "recommendation" | "alert" | "opportunity"
    priority: int  # 1=high, 2=medium, 3=low
    title: str
    description: str
    channel: str | None = None
    impact_estimate: str | None = None


class WeeklyInsightsResponse(BaseModel):
    generated_at: str
    insights: list[InsightItem]
