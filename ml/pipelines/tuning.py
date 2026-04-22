"""Hyperparameter tuning with randomized search and walk-forward CV."""

from typing import Dict, Any, Optional
import time

import numpy as np
import pandas as pd
from sklearn.model_selection import TimeSeriesSplit, RandomizedSearchCV
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.metrics import make_scorer, f1_score
from xgboost import XGBClassifier
from loguru import logger

from ml.features.engineering import compute_features, prepare_train_data


class HyperparameterTuner:
    """Tune hyperparameters with randomized search + walk-forward CV."""

    def __init__(self, n_splits: int = 3, n_iter: int = 20, random_state: int = 42):
        self.n_splits = n_splits
        self.n_iter = n_iter
        self.random_state = random_state
        self.best_params = {}
        self.best_score = 0.0
        self.cv_results = None

    def _get_param_distributions(self, model_type: str = "xgboost") -> Dict[str, Any]:
        """Get hyperparameter distributions for each model type."""
        if model_type == "xgboost":
            return {
                "n_estimators": [100, 200, 300, 500],
                "max_depth": [3, 5, 7, 10],
                "learning_rate": [0.01, 0.05, 0.1, 0.2],
                "subsample": [0.6, 0.8, 1.0],
                "colsample_bytree": [0.6, 0.8, 1.0],
                "min_child_weight": [1, 3, 5],
                "gamma": [0, 0.1, 0.2],
            }
        elif model_type == "gradient_boosting":
            return {
                "n_estimators": [100, 200, 300, 500],
                "max_depth": [3, 5, 7, 10],
                "learning_rate": [0.01, 0.05, 0.1, 0.2],
                "subsample": [0.6, 0.8, 1.0],
                "min_samples_split": [2, 5, 10],
                "min_samples_leaf": [1, 2, 4],
            }
        elif model_type == "random_forest":
            return {
                "n_estimators": [100, 200, 300, 500],
                "max_depth": [5, 10, 15, 20, None],
                "min_samples_split": [2, 5, 10],
                "min_samples_leaf": [1, 2, 4],
                "max_features": ["sqrt", "log2", None],
            }
        else:
            raise ValueError(f"Unknown model_type: {model_type}")

    def tune(
        self,
        X: np.ndarray,
        y: np.ndarray,
        model_type: str = "gradient_boosting",
        scoring: str = "f1",
    ) -> Dict[str, Any]:
        """Run randomized search with time series CV.
        
        Returns best parameters and CV results.
        """
        param_distributions = self._get_param_distributions(model_type)

        if model_type == "xgboost":
            base_model = XGBClassifier(random_state=self.random_state, eval_metric="logloss")
        elif model_type == "gradient_boosting":
            base_model = GradientBoostingClassifier(random_state=self.random_state)
        elif model_type == "random_forest":
            base_model = RandomForestClassifier(random_state=self.random_state, n_jobs=-1)
        else:
            raise ValueError(f"Unknown model_type: {model_type}")

        tscv = TimeSeriesSplit(n_splits=self.n_splits)
        scorer = make_scorer(f1_score) if scoring == "f1" else scoring

        logger.info(f"Starting randomized search: {self.n_iter} iterations, {self.n_splits}-fold TS CV")
        start = time.time()

        search = RandomizedSearchCV(
            estimator=base_model,
            param_distributions=param_distributions,
            n_iter=self.n_iter,
            cv=tscv,
            scoring=scorer,
            random_state=self.random_state,
            n_jobs=-1,
            verbose=1,
        )
        search.fit(X, y)

        elapsed = time.time() - start
        self.best_params = search.best_params_
        self.best_score = search.best_score_
        self.cv_results = search.cv_results_

        logger.info(f"Tuning complete in {elapsed:.1f}s | Best {scoring}: {self.best_score:.4f}")
        logger.info(f"Best params: {self.best_params}")

        return {
            "best_params": self.best_params,
            "best_score": self.best_score,
            "cv_results": self.cv_results,
            "elapsed_seconds": elapsed,
        }

    def get_top_configs(self, n: int = 5) -> pd.DataFrame:
        """Return top N configurations from CV results."""
        if self.cv_results is None:
            raise RuntimeError("No CV results. Call tune() first.")

        results = pd.DataFrame(self.cv_results)
        results = results.sort_values("mean_test_score", ascending=False)
        return results[["rank_test_score", "mean_test_score", "std_test_score", "params"]].head(n)
