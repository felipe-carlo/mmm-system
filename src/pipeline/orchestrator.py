"""Prefect orchestration flows for automated MMM pipeline.

Flows:
- daily_sync: Fetch data from Google Sheets and validate
- monthly_retrain: Full model retrain + optimization
- weekly_insights: Generate insights report from latest model
"""

from __future__ import annotations

import os

from loguru import logger
from prefect import flow, task


@task(name="fetch_sheets_data", retries=2, retry_delay_seconds=30)
def fetch_sheets_data() -> dict:
    """Fetch all data from Google Sheets."""
    from src.pipeline.connectors.sheets_connector import SheetsConnector

    url = os.getenv("GOOGLE_SHEETS_URL", "")
    creds = os.getenv("GOOGLE_SHEETS_CREDENTIALS_PATH", "")

    connector = SheetsConnector(spreadsheet_url=url, credentials_path=creds)
    data = connector.fetch_all()
    connector.snapshot_to_parquet(data, "data/raw")
    return data


@task(name="validate_data")
def validate_data(data: dict) -> bool:
    """Validate fetched data."""
    from src.pipeline.validators.data_validator import DataValidator

    validator = DataValidator()
    report = validator.validate_all(
        media_spend=data["media_spend"],
        kpi=data["kpi"],
        external_factors=data["external_factors"],
        channel_config=data["channel_config"],
    )
    return report.is_valid


@task(name="aggregate_to_weekly")
def aggregate_to_weekly(data: dict):
    """Aggregate daily data to weekly."""
    from src.pipeline.transformers.aggregator import (
        aggregate_external_factors,
        aggregate_kpi,
        aggregate_media_spend,
        build_model_dataframe,
    )

    media_weekly = aggregate_media_spend(data["media_spend"])
    kpi_weekly = aggregate_kpi(data["kpi"])
    external_weekly = aggregate_external_factors(data["external_factors"])
    model_df = build_model_dataframe(media_weekly, kpi_weekly, external_weekly)
    return model_df


@task(name="store_weekly_data")
def store_weekly_data(model_df):
    """Store weekly data in DuckDB."""
    from src.pipeline.storage.duckdb_analytics import DuckDBAnalytics

    db_path = os.getenv("DUCKDB_PATH", "data/mmm_analytics.duckdb")
    analytics = DuckDBAnalytics(db_path)
    analytics.store_weekly_data(model_df)
    analytics.save_to_parquet()
    analytics.close()


@task(name="train_pymc_model")
def train_pymc_model(model_df, channel_config):
    """Train PyMC-Marketing model."""
    from src.models.channel_registry import ChannelRegistry
    from src.models.pymc_model import PyMCModelWrapper

    registry = ChannelRegistry(channel_config)
    wrapper = PyMCModelWrapper(registry)
    wrapper.fit(model_df, target_col="revenue", chains=4, draws=1000, tune=1500)
    return wrapper.get_results()


@task(name="generate_insights")
def generate_insights_task(result):
    """Generate weekly insights from model results."""
    from src.insights.weekly_report import generate_weekly_insights

    return generate_weekly_insights(result)


# --- FLOWS ---


@flow(name="daily_sync", log_prints=True)
def daily_sync_flow():
    """Daily: fetch data from Sheets, validate, store snapshot."""
    logger.info("Starting daily sync...")
    data = fetch_sheets_data()
    is_valid = validate_data(data)

    if not is_valid:
        logger.error("Data validation failed! Check errors.")
        return {"status": "failed", "reason": "validation_error"}

    logger.info("Daily sync complete")
    return {"status": "success"}


@flow(name="monthly_retrain", log_prints=True)
def monthly_retrain_flow():
    """Monthly: full pipeline - fetch, validate, aggregate, train, optimize."""
    logger.info("Starting monthly retrain...")

    data = fetch_sheets_data()
    is_valid = validate_data(data)
    if not is_valid:
        logger.error("Data validation failed!")
        return {"status": "failed"}

    model_df = aggregate_to_weekly(data)
    store_weekly_data(model_df)

    result = train_pymc_model(model_df, data["channel_config"])

    # Store results for API
    from src.api.routes.models import store_model_result

    store_model_result("pymc", {
        "roi_by_channel": result.roi_by_channel,
        "model_fit_metrics": result.model_fit_metrics,
        "adstock_params": result.adstock_params,
    })

    insights = generate_insights_task(result)
    logger.info(f"Monthly retrain complete. {len(insights)} insights generated.")
    return {"status": "success", "insights_count": len(insights)}


@flow(name="weekly_insights", log_prints=True)
def weekly_insights_flow():
    """Weekly: generate insights report from latest model."""
    from src.api.routes.models import _model_results

    result_data = _model_results.get("pymc")
    if not result_data:
        logger.warning("No model results available. Run monthly_retrain first.")
        return {"status": "skipped", "reason": "no_model"}

    from src.models.base import ModelResult

    result = ModelResult(
        roi_by_channel=result_data["roi_by_channel"],
        channel_contributions=None,
        adstock_params=result_data.get("adstock_params", {}),
        baseline_contribution=0,
        model_fit_metrics=result_data.get("model_fit_metrics", {}),
    )

    insights = generate_insights_task(result)
    logger.info(f"Weekly insights: {len(insights)} generated")
    return {"status": "success", "insights_count": len(insights)}
