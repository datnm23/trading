"""Model drift detection for ML trading strategies.

Monitors prediction confidence, feature distributions, and error rates
to detect when a model is losing its edge and needs retraining.

Concepts applied:
    - non_stationarity: markets change, models degrade
    - overfit_vao_qua_khu: detect when model no longer fits current regime
    - walk_forward: continuous validation on recent data
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from loguru import logger
from scipy import stats


@dataclass
class DriftReport:
    """Report of drift analysis."""

    timestamp: datetime
    is_drifted: bool
    confidence_drift_score: float
    feature_drift_score: float
    error_rate_drift: float
    overall_drift_score: float
    recommendation: str
    details: dict = field(default_factory=dict)


class PredictionDriftDetector:
    """Detect drift in model prediction confidence distribution.

    Compares recent prediction probabilities against baseline (training)
    using Kolmogorov-Smirnov test and confidence mean shift.
    """

    def __init__(self, window_size: int = 30, ks_threshold: float = 0.15):
        self.window_size = window_size
        self.ks_threshold = ks_threshold
        self.baseline_confidences: np.ndarray | None = None
        self.confidence_history: list[float] = []

    def set_baseline(self, confidences: np.ndarray):
        """Set baseline from training/validation predictions."""
        self.baseline_confidences = confidences.copy()
        logger.info(f"Drift baseline set: {len(confidences)} predictions")

    def update(self, confidence: float):
        """Log a new prediction confidence (probability of predicted class)."""
        self.confidence_history.append(confidence)
        # Keep only recent window
        if len(self.confidence_history) > self.window_size * 3:
            self.confidence_history = self.confidence_history[-self.window_size * 3 :]

    def detect(self) -> dict:
        """Detect confidence drift.

        Returns:
            dict with keys: drifted, ks_stat, p_value, mean_shift, score
        """
        if (
            self.baseline_confidences is None
            or len(self.confidence_history) < self.window_size
        ):
            return {
                "drifted": False,
                "ks_stat": 0.0,
                "p_value": 1.0,
                "mean_shift": 0.0,
                "score": 0.0,
            }

        recent = np.array(self.confidence_history[-self.window_size :])

        # KS test
        ks_stat, p_value = stats.ks_2samp(self.baseline_confidences, recent)

        # Mean shift (normalized by baseline std)
        baseline_mean = float(np.mean(self.baseline_confidences))
        baseline_std = float(np.std(self.baseline_confidences))
        recent_mean = float(np.mean(recent))
        mean_shift = abs(recent_mean - baseline_mean) / max(baseline_std, 0.01)

        # Drift score: combination of KS and mean shift
        score = min(1.0, (float(ks_stat) / self.ks_threshold) * 0.5 + mean_shift * 0.5)
        drifted = bool(score > 1.0 or ks_stat > self.ks_threshold)

        return {
            "drifted": drifted,
            "ks_stat": float(ks_stat),
            "p_value": float(p_value),
            "mean_shift": float(mean_shift),
            "score": float(score),
            "baseline_mean": baseline_mean,
            "recent_mean": recent_mean,
        }


class FeatureDriftDetector:
    """Detect drift in feature distributions using PSI (Population Stability Index).

    PSI < 0.1: no drift
    PSI 0.1 - 0.25: moderate drift
    PSI > 0.25: significant drift
    """

    def __init__(self, psi_threshold: float = 0.2, n_bins: int = 10):
        self.psi_threshold = psi_threshold
        self.n_bins = n_bins
        self.baseline_features: pd.DataFrame | None = None
        self.bin_edges: dict[str, np.ndarray] = {}

    def set_baseline(self, features_df: pd.DataFrame):
        """Set baseline feature distributions."""
        self.baseline_features = features_df.copy()
        self.bin_edges = {}
        for col in features_df.columns:
            edges = np.histogram_bin_edges(features_df[col].dropna(), bins=self.n_bins)
            self.bin_edges[col] = edges
        logger.info(f"Feature drift baseline set: {len(features_df.columns)} features")

    def compute_psi(
        self, expected: np.ndarray, actual: np.ndarray, epsilon: float = 1e-10
    ) -> float:
        """Compute PSI between two distributions."""
        expected_pct = expected / np.sum(expected)
        actual_pct = actual / np.sum(actual)
        psi = np.sum(
            (expected_pct - actual_pct)
            * np.log((expected_pct + epsilon) / (actual_pct + epsilon))
        )
        return psi

    def detect(self, recent_features: pd.DataFrame) -> dict:
        """Detect feature drift.

        Returns:
            dict with keys: drifted, psi_scores, avg_psi, max_psi_feature
        """
        if self.baseline_features is None:
            return {
                "drifted": False,
                "psi_scores": {},
                "avg_psi": 0.0,
                "max_psi_feature": None,
            }

        psi_scores = {}
        for col in self.baseline_features.columns:
            if col not in recent_features.columns:
                continue
            edges = self.bin_edges.get(col)
            if edges is None:
                continue

            expected_counts, _ = np.histogram(
                self.baseline_features[col].dropna(), bins=edges
            )
            actual_counts, _ = np.histogram(recent_features[col].dropna(), bins=edges)

            # Add small constant to avoid division by zero
            expected_counts = expected_counts + 1
            actual_counts = actual_counts + 1

            psi = self.compute_psi(expected_counts, actual_counts)
            psi_scores[col] = psi

        if not psi_scores:
            return {
                "drifted": False,
                "psi_scores": {},
                "avg_psi": 0.0,
                "max_psi_feature": None,
            }

        avg_psi = float(np.mean(list(psi_scores.values())))
        max_feature = max(psi_scores, key=psi_scores.get)
        drifted = bool(avg_psi > self.psi_threshold)

        return {
            "drifted": drifted,
            "psi_scores": {k: float(v) for k, v in psi_scores.items()},
            "avg_psi": avg_psi,
            "max_psi_feature": max_feature,
            "max_psi": float(psi_scores[max_feature]),
        }


class ErrorRateDriftDetector:
    """Detect drift via error rate on recent labeled data.

    Requires periodic ground truth labels (e.g., after 5 bars).
    """

    def __init__(self, window_size: int = 50, threshold: float = 0.55):
        self.window_size = window_size
        self.threshold = threshold  # error rate above this triggers drift
        self.baseline_error: float | None = None
        self.recent_errors: list[int] = []  # 1 = error, 0 = correct

    def set_baseline(self, error_rate: float):
        """Set baseline error rate from validation."""
        self.baseline_error = error_rate
        logger.info(f"Error rate baseline: {error_rate:.3f}")

    def log_prediction(self, predicted: int, actual: int):
        """Log whether a prediction was correct."""
        self.recent_errors.append(0 if predicted == actual else 1)
        if len(self.recent_errors) > self.window_size * 2:
            self.recent_errors = self.recent_errors[-self.window_size * 2 :]

    def detect(self) -> dict:
        """Detect error rate drift."""
        if self.baseline_error is None or len(self.recent_errors) < self.window_size:
            return {
                "drifted": False,
                "recent_error_rate": 0.0,
                "relative_increase": 0.0,
            }

        recent = self.recent_errors[-self.window_size :]
        recent_error_rate = float(np.mean(recent))
        relative = recent_error_rate / max(self.baseline_error, 0.01)

        return {
            "drifted": bool(recent_error_rate > self.threshold),
            "recent_error_rate": recent_error_rate,
            "baseline_error": float(self.baseline_error),
            "relative_increase": float(relative),
        }


class ModelDriftMonitor:
    """Orchestrates all drift detectors and produces unified reports.

    Usage:
        monitor = ModelDriftMonitor()
        monitor.set_baseline(pipeline)  # From trained pipeline

        # Each prediction cycle:
        monitor.log_prediction(features, proba, predicted, actual)

        # Periodic check:
        report = monitor.check()
        if report.is_drifted:
            trigger_retrain()
    """

    def __init__(
        self,
        confidence_window: int = 30,
        psi_threshold: float = 0.2,
        error_threshold: float = 0.55,
        drift_cooldown_days: int = 7,
    ):
        self.confidence_detector = PredictionDriftDetector(
            window_size=confidence_window
        )
        self.feature_detector = FeatureDriftDetector(psi_threshold=psi_threshold)
        self.error_detector = ErrorRateDriftDetector(threshold=error_threshold)
        self.drift_cooldown_days = drift_cooldown_days

        self.last_drift_time: datetime | None = None
        self.reports: list[DriftReport] = []
        self._feature_buffer: list[pd.DataFrame] = []

    def set_baseline(self, pipeline):
        """Set baselines from a trained MLClassifierPipeline."""
        # Confidence baseline from training CV
        if hasattr(pipeline, "metrics") and "folds" in pipeline.metrics:
            # Use per-fold validation accuracies as confidence proxy
            fold_accuracies = np.array(
                [f["accuracy"] for f in pipeline.metrics["folds"]]
            )
            # Repeat to get ~100 samples for PSI calculation
            repeated = np.tile(fold_accuracies, 100 // len(fold_accuracies) + 1)[:100]
            self.confidence_detector.set_baseline(repeated)
            logger.info(f"Drift baselines set from {len(fold_accuracies)} CV folds")
        else:
            logger.warning(
                "No CV fold metrics found — using default confidence baseline"
            )
            self.confidence_detector.set_baseline(np.array([0.7] * 100))

        # Feature baseline would need training features stored
        logger.info("Drift monitor baselines set")

    def set_baseline_manual(
        self,
        confidences: np.ndarray,
        features: pd.DataFrame,
        error_rate: float,
    ):
        """Set baselines manually."""
        self.confidence_detector.set_baseline(confidences)
        self.feature_detector.set_baseline(features)
        self.error_detector.set_baseline(error_rate)

    def log_prediction(
        self,
        features: pd.Series,
        confidence: float,
        predicted: int,
        actual: int | None = None,
    ):
        """Log a single prediction for drift tracking."""
        self.confidence_detector.update(confidence)
        self._feature_buffer.append(features.to_frame().T)
        if len(self._feature_buffer) > 100:
            self._feature_buffer = self._feature_buffer[-50:]
        if actual is not None:
            self.error_detector.log_prediction(predicted, actual)

    def check(self) -> DriftReport:
        """Run all drift checks and return unified report."""
        conf_result = self.confidence_detector.detect()
        feature_result = self.feature_detector.detect(
            pd.concat(self._feature_buffer, ignore_index=True)
            if self._feature_buffer
            else pd.DataFrame()
        )
        error_result = self.error_detector.detect()

        # Overall drift score: weighted combination
        overall = float(
            conf_result.get("score", 0) * 0.4
            + min(1.0, feature_result.get("avg_psi", 0) / 0.25) * 0.3
            + error_result.get("recent_error_rate", 0) * 0.3
        )

        # Determine if drifted
        is_drifted = bool(
            conf_result.get("drifted", False)
            or feature_result.get("drifted", False)
            or error_result.get("drifted", False)
            or overall > 0.7
        )

        # Cooldown check
        if is_drifted and self.last_drift_time:
            days_since = (datetime.now() - self.last_drift_time).days
            if days_since < self.drift_cooldown_days:
                is_drifted = False  # Still in cooldown

        if is_drifted:
            self.last_drift_time = datetime.now()

        # Recommendation
        if is_drifted:
            recommendation = (
                "RETRAIN: Significant drift detected. Schedule model retraining."
            )
        elif overall > 0.4:
            recommendation = "WATCH: Elevated drift indicators. Monitor closely."
        else:
            recommendation = "OK: No significant drift."

        report = DriftReport(
            timestamp=datetime.now(),
            is_drifted=is_drifted,
            confidence_drift_score=conf_result.get("score", 0),
            feature_drift_score=feature_result.get("avg_psi", 0),
            error_rate_drift=error_result.get("recent_error_rate", 0),
            overall_drift_score=overall,
            recommendation=recommendation,
            details={
                "confidence": conf_result,
                "feature": feature_result,
                "error": error_result,
            },
        )
        self.reports.append(report)
        return report

    def get_summary(self) -> dict:
        """Return summary of drift history."""
        if not self.reports:
            return {}
        drifted_count = sum(1 for r in self.reports if r.is_drifted)
        return {
            "total_checks": len(self.reports),
            "drifted_count": drifted_count,
            "last_drift": (
                self.last_drift_time.isoformat() if self.last_drift_time else None
            ),
            "avg_overall_score": np.mean([r.overall_drift_score for r in self.reports]),
        }

    def save(self, path: str):
        """Save drift history to JSON."""

        def _convert(obj):
            if isinstance(obj, (np.bool_, bool)):
                return bool(obj)
            if isinstance(obj, (np.integer,)):
                return int(obj)
            if isinstance(obj, (np.floating, float)):
                return float(obj)
            if isinstance(obj, dict):
                return {k: _convert(v) for k, v in obj.items()}
            if isinstance(obj, list):
                return [_convert(v) for v in obj]
            return obj

        data = {
            "reports": [
                {
                    "timestamp": r.timestamp.isoformat(),
                    "is_drifted": bool(r.is_drifted),
                    "overall_score": float(r.overall_drift_score),
                    "recommendation": r.recommendation,
                }
                for r in self.reports
            ],
            "summary": _convert(self.get_summary()),
        }
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(data, f, indent=2)


if __name__ == "__main__":
    # Demo
    monitor = ModelDriftMonitor()
    monitor.set_baseline_manual(
        confidences=np.random.beta(7, 3, 500),  # High confidence baseline
        features=pd.DataFrame(
            np.random.randn(500, 5), columns=[f"f{i}" for i in range(5)]
        ),
        error_rate=0.35,
    )

    # Simulate normal predictions
    for _ in range(30):
        monitor.log_prediction(
            features=pd.Series(np.random.randn(5)),
            confidence=np.random.beta(7, 3),
            predicted=1,
            actual=1,
        )

    report = monitor.check()
    print(
        f"Normal period: drift={report.is_drifted}, score={report.overall_drift_score:.3f}"
    )

    # Simulate degraded predictions (lower confidence, higher errors)
    for _ in range(30):
        monitor.log_prediction(
            features=pd.Series(np.random.randn(5) + 2),  # Shifted features
            confidence=np.random.beta(4, 4),  # Lower confidence
            predicted=1,
            actual=0,  # Wrong
        )

    report2 = monitor.check()
    print(
        f"Degraded period: drift={report2.is_drifted}, score={report2.overall_drift_score:.3f}"
    )
    print(f"Recommendation: {report2.recommendation}")
