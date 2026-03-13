"""Geo-lift test framework for model calibration.

Manages experiment design, results tracking, and prior updates
based on incrementality test outcomes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from loguru import logger


@dataclass
class GeoLiftExperiment:
    """A geo-lift test configuration and results."""

    id: str
    channel: str
    test_regions: list[str]
    control_regions: list[str]
    start_date: str
    end_date: str
    budget_change_pct: float  # +20% = increase, -100% = blackout
    status: str = "planned"  # planned | running | completed | cancelled
    # Results (filled after experiment)
    incremental_revenue: float | None = None
    incremental_roas: float | None = None
    confidence_level: float | None = None
    notes: str = ""


@dataclass
class CalibrationHistory:
    """Tracks all calibration experiments and their impact on model priors."""

    experiments: list[GeoLiftExperiment] = field(default_factory=list)
    prior_updates: list[dict] = field(default_factory=list)

    def add_experiment(self, experiment: GeoLiftExperiment) -> None:
        self.experiments.append(experiment)
        logger.info(f"Added experiment '{experiment.id}' for channel '{experiment.channel}'")

    def complete_experiment(
        self,
        experiment_id: str,
        incremental_revenue: float,
        incremental_roas: float,
        confidence_level: float,
    ) -> GeoLiftExperiment:
        """Record experiment results and suggest prior updates."""
        exp = next((e for e in self.experiments if e.id == experiment_id), None)
        if not exp:
            raise KeyError(f"Experiment '{experiment_id}' not found")

        exp.status = "completed"
        exp.incremental_revenue = incremental_revenue
        exp.incremental_roas = incremental_roas
        exp.confidence_level = confidence_level

        logger.info(
            f"Experiment '{experiment_id}' completed: "
            f"iROAS={incremental_roas:.2f}, confidence={confidence_level:.0%}"
        )
        return exp

    def get_prior_update_suggestion(
        self, channel: str, current_roi_prior_mu: float
    ) -> dict | None:
        """Suggest a prior update based on completed experiments for a channel."""
        completed = [
            e for e in self.experiments
            if e.channel == channel and e.status == "completed" and e.confidence_level
        ]

        if not completed:
            return None

        # Weighted average of experiment results (by confidence)
        total_weight = sum(e.confidence_level for e in completed)
        weighted_roas = sum(
            e.incremental_roas * e.confidence_level for e in completed
        ) / total_weight

        # Blend experiment result with current prior (50/50 by default)
        blend_weight = 0.5
        new_mu = current_roi_prior_mu * (1 - blend_weight) + weighted_roas * blend_weight

        suggestion = {
            "channel": channel,
            "current_prior_mu": current_roi_prior_mu,
            "experiment_roas": round(weighted_roas, 3),
            "suggested_prior_mu": round(new_mu, 3),
            "n_experiments": len(completed),
            "avg_confidence": round(total_weight / len(completed), 2),
            "timestamp": datetime.now().isoformat(),
        }

        self.prior_updates.append(suggestion)
        logger.info(
            f"Prior update suggestion for '{channel}': "
            f"{current_roi_prior_mu:.3f} -> {new_mu:.3f}"
        )
        return suggestion

    def get_audit_trail(self) -> list[dict]:
        """Return full audit trail of experiments and prior updates."""
        trail = []
        for exp in self.experiments:
            trail.append({
                "type": "experiment",
                "id": exp.id,
                "channel": exp.channel,
                "status": exp.status,
                "incremental_roas": exp.incremental_roas,
                "dates": f"{exp.start_date} to {exp.end_date}",
            })
        for update in self.prior_updates:
            trail.append({
                "type": "prior_update",
                "channel": update["channel"],
                "old_prior": update["current_prior_mu"],
                "new_prior": update["suggested_prior_mu"],
                "timestamp": update["timestamp"],
            })
        return sorted(trail, key=lambda x: x.get("timestamp", x.get("dates", "")))
