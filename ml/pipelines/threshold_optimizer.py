"""Threshold optimizer for precision/recall trade-off."""

import numpy as np
import pandas as pd
from sklearn.metrics import precision_score, recall_score, f1_score, accuracy_score
from loguru import logger


class ThresholdOptimizer:
    """Find optimal probability threshold for classification."""

    def __init__(self, thresholds: np.ndarray = None):
        self.thresholds = thresholds if thresholds is not None else np.arange(0.30, 0.81, 0.02)
        self.results = []
        self.best_threshold = 0.5

    def optimize(self, y_true: np.ndarray, y_proba: np.ndarray, metric: str = "f1") -> dict:
        """Grid search thresholds and return best.
        
        Args:
            y_true: True labels (0/1)
            y_proba: Predicted probabilities for positive class
            metric: Metric to optimize ('f1', 'precision', 'recall', 'accuracy')
        
        Returns:
            dict with best_threshold, best_score, and full results DataFrame
        """
        self.results = []

        for thresh in self.thresholds:
            y_pred = (y_proba >= thresh).astype(int)

            # Handle edge case: all predictions same class
            if len(np.unique(y_pred)) < 2:
                prec = rec = f1 = acc = 0.0
            else:
                prec = precision_score(y_true, y_pred, zero_division=0)
                rec = recall_score(y_true, y_pred, zero_division=0)
                f1 = f1_score(y_true, y_pred, zero_division=0)
                acc = accuracy_score(y_true, y_pred)

            self.results.append({
                "threshold": thresh,
                "precision": prec,
                "recall": rec,
                "f1": f1,
                "accuracy": acc,
                "tp_rate": rec,  # recall = TP rate
                "fp_rate": 1 - rec if prec == 0 else (1 - prec) * (sum(y_true == 0) / sum(y_true == 1)) if sum(y_true == 1) > 0 else 0,
            })

        df = pd.DataFrame(self.results)

        # Find best by primary metric
        best_idx = df[metric].idxmax()
        self.best_threshold = df.loc[best_idx, "threshold"]
        best_score = df.loc[best_idx, metric]

        # Also find threshold for target precision/recall
        target_precision = df[df["precision"] >= 0.60]
        target_recall = df[df["recall"] >= 0.70]

        logger.info(f"Threshold optimization complete | Best {metric}={best_score:.4f} @ threshold={self.best_threshold:.2f}")

        return {
            "best_threshold": float(self.best_threshold),
            "best_score": float(best_score),
            "metric": metric,
            "results": df,
            "target_precision_60": target_precision["threshold"].min() if not target_precision.empty else None,
            "target_recall_70": target_recall["threshold"].max() if not target_recall.empty else None,
        }

    def get_threshold_for_precision(self, target: float = 0.60) -> float:
        """Get minimum threshold that achieves target precision."""
        df = pd.DataFrame(self.results)
        valid = df[df["precision"] >= target]
        if valid.empty:
            logger.warning(f"No threshold achieves precision >= {target}")
            return 0.5
        return float(valid.loc[valid["threshold"].idxmin(), "threshold"])

    def get_threshold_for_recall(self, target: float = 0.70) -> float:
        """Get maximum threshold that achieves target recall."""
        df = pd.DataFrame(self.results)
        valid = df[df["recall"] >= target]
        if valid.empty:
            logger.warning(f"No threshold achieves recall >= {target}")
            return 0.5
        return float(valid.loc[valid["threshold"].idxmax(), "threshold"])
