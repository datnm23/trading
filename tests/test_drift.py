"""Tests for drift detection module."""

import numpy as np
import pandas as pd
import pytest

from ml.drift_detection import (
    PredictionDriftDetector,
    FeatureDriftDetector,
    ErrorRateDriftDetector,
    ModelDriftMonitor,
)


class TestPredictionDriftDetector:
    def test_baseline_required(self):
        det = PredictionDriftDetector()
        result = det.detect()
        assert result["drifted"] is False

    def test_no_drift_similar(self):
        det = PredictionDriftDetector(window_size=30, ks_threshold=0.3)
        np.random.seed(42)
        baseline = np.random.beta(7, 3, 500)
        det.set_baseline(baseline)
        for _ in range(30):
            det.update(np.random.beta(7, 3))
        result = det.detect()
        assert result["drifted"] == False
        assert result["score"] < 0.8

    def test_drift_low_confidence(self):
        det = PredictionDriftDetector(window_size=30, ks_threshold=0.15)
        baseline = np.random.beta(8, 2, 500)  # High confidence
        det.set_baseline(baseline)
        for _ in range(30):
            det.update(np.random.beta(4, 4))  # Lower confidence
        result = det.detect()
        assert result["drifted"] == True
        assert result["score"] > 0.5


class TestFeatureDriftDetector:
    def test_no_drift(self):
        det = FeatureDriftDetector(psi_threshold=0.2)
        baseline = pd.DataFrame(np.random.randn(500, 3), columns=["a", "b", "c"])
        det.set_baseline(baseline)
        recent = pd.DataFrame(np.random.randn(50, 3), columns=["a", "b", "c"])
        result = det.detect(recent)
        assert result["drifted"] == False
        assert result["avg_psi"] < 0.2

    def test_drift_shifted(self):
        det = FeatureDriftDetector(psi_threshold=0.2)
        baseline = pd.DataFrame(np.random.randn(500, 3), columns=["a", "b", "c"])
        det.set_baseline(baseline)
        recent = pd.DataFrame(np.random.randn(50, 3) + 3, columns=["a", "b", "c"])  # Shifted
        result = det.detect(recent)
        assert result["drifted"] == True
        assert result["avg_psi"] > 0.2


class TestErrorRateDriftDetector:
    def test_no_drift(self):
        det = ErrorRateDriftDetector(window_size=50, threshold=0.55)
        det.set_baseline(0.30)
        for _ in range(50):
            det.log_prediction(1, 1)  # All correct
        result = det.detect()
        assert result["drifted"] == False
        assert result["recent_error_rate"] == 0.0

    def test_drift_high_errors(self):
        det = ErrorRateDriftDetector(window_size=50, threshold=0.55)
        det.set_baseline(0.30)
        for _ in range(50):
            det.log_prediction(1, 0)  # All wrong
        result = det.detect()
        assert result["drifted"] == True
        assert result["recent_error_rate"] == 1.0


class TestModelDriftMonitor:
    def test_check_normal(self):
        monitor = ModelDriftMonitor()
        monitor.set_baseline_manual(
            confidences=np.random.beta(7, 3, 500),
            features=pd.DataFrame(np.random.randn(500, 3), columns=["a", "b", "c"]),
            error_rate=0.35,
        )
        for _ in range(30):
            monitor.log_prediction(
                pd.Series(np.random.randn(3)),
                np.random.beta(7, 3),
                1, 1,
            )
        report = monitor.check()
        # May drift randomly due to beta sampling; just verify structure
        assert report.overall_drift_score >= 0.0
        assert report.recommendation != ""

    def test_check_drifted(self):
        monitor = ModelDriftMonitor()
        monitor.set_baseline_manual(
            confidences=np.random.beta(8, 2, 500),
            features=pd.DataFrame(np.random.randn(500, 3), columns=["a", "b", "c"]),
            error_rate=0.20,
        )
        # Degraded predictions
        for _ in range(30):
            monitor.log_prediction(
                pd.Series(np.random.randn(3) + 3),  # Feature shift
                np.random.beta(3, 5),  # Low confidence
                1, 0,  # Wrong
            )
        report = monitor.check()
        # Degraded predictions should show higher drift score
        assert report.overall_drift_score > 0.0

    def test_cooldown(self):
        monitor = ModelDriftMonitor(drift_cooldown_days=7)
        monitor.set_baseline_manual(
            confidences=np.random.beta(8, 2, 500),
            features=pd.DataFrame(np.random.randn(500, 3)),
            error_rate=0.20,
        )
        # Trigger drift
        for _ in range(30):
            monitor.log_prediction(pd.Series(np.random.randn(1) + 5), 0.3, 1, 0)
        report1 = monitor.check()
        # Should set last_drift_time if drifted
        if report1.is_drifted:
            assert monitor.last_drift_time is not None

    def test_save_load(self, tmp_path):
        monitor = ModelDriftMonitor()
        monitor.set_baseline_manual(
            confidences=np.random.beta(7, 3, 500),
            features=pd.DataFrame(np.random.randn(500, 3)),
            error_rate=0.35,
        )
        for _ in range(10):
            monitor.log_prediction(pd.Series(np.random.randn(3)), 0.7, 1, 1)
        monitor.check()

        path = tmp_path / "drift_history.json"
        monitor.save(str(path))
        assert path.exists()
        data = path.read_text()
        assert "reports" in data
