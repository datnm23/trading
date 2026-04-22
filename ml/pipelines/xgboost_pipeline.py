"""ML model training pipeline using XGBoost classifier."""

from pathlib import Path
from typing import Optional, List

import numpy as np
import pandas as pd
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier
from loguru import logger

from ml.features.engineering import compute_features, prepare_train_data


def _get_classifier(n_estimators: int = 200, max_depth: int = 5, learning_rate: float = 0.05):
    """Get XGBoost classifier with sensible defaults."""
    return XGBClassifier(
        n_estimators=n_estimators,
        max_depth=max_depth,
        learning_rate=learning_rate,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        eval_metric="logloss",
    )


class MLClassifierPipeline:
    """Classifier for price direction prediction."""

    def __init__(self, n_splits: int = 5, threshold: float = 0.55, feature_whitelist: list = None, target_horizon: int = 5):
        self.n_splits = n_splits
        self.threshold = threshold  # probability threshold for signal generation
        self.feature_whitelist = feature_whitelist
        self.target_horizon = target_horizon
        self.model = None
        self.scaler = StandardScaler()
        self.feature_names = None
        self.metrics = {}

    def train(self, df: pd.DataFrame) -> dict:
        """Train with walk-forward cross-validation.

        Returns training metrics.
        """
        # Feature engineering
        features_df = compute_features(df)
        target_col = f"target_direction_{self.target_horizon}d" if self.target_horizon != 5 else "target_direction"
        target_return_col = f"target_return_{self.target_horizon}d" if self.target_horizon != 5 else "target_return_5d"
        X, y, self.feature_names, sample_weight = prepare_train_data(
            features_df,
            whitelist=self.feature_whitelist,
            target_col=target_col,
            target_return_col=target_return_col,
        )

        logger.info(f"Training data: {len(X)} samples, {len(self.feature_names)} features")

        # Walk-forward CV
        tscv = TimeSeriesSplit(n_splits=self.n_splits)
        fold_metrics = []

        for fold, (train_idx, val_idx) in enumerate(tscv.split(X)):
            X_train, X_val = X[train_idx], X[val_idx]
            y_train, y_val = y[train_idx], y[val_idx]
            w_train = sample_weight[train_idx]

            # Scale
            scaler = StandardScaler()
            X_train_s = scaler.fit_transform(X_train)
            X_val_s = scaler.transform(X_val)

            # Train
            model = _get_classifier()
            model.fit(X_train_s, y_train, sample_weight=w_train)

            # Evaluate
            y_pred = model.predict(X_val_s)
            y_proba = model.predict_proba(X_val_s)[:, 1]
            fold_metrics.append({
                "fold": fold + 1,
                "accuracy": accuracy_score(y_val, y_pred),
                "precision": precision_score(y_val, y_pred, zero_division=0),
                "recall": recall_score(y_val, y_pred, zero_division=0),
                "f1": f1_score(y_val, y_pred, zero_division=0),
                "val_size": len(y_val),
            })

        # Train final model on all data
        X_scaled = self.scaler.fit_transform(X)
        self.model = _get_classifier()
        self.model.fit(X_scaled, y, sample_weight=sample_weight)

        # Feature importance
        fi = {}
        if hasattr(self.model, "feature_importances_"):
            fi = dict(zip(self.feature_names, self.model.feature_importances_.tolist()))

        # Aggregate metrics
        self.metrics = {
            "mean_accuracy": np.mean([m["accuracy"] for m in fold_metrics]),
            "mean_precision": np.mean([m["precision"] for m in fold_metrics]),
            "mean_recall": np.mean([m["recall"] for m in fold_metrics]),
            "mean_f1": np.mean([m["f1"] for m in fold_metrics]),
            "folds": fold_metrics,
            "feature_importance": fi,
        }

        logger.info(f"Training complete. Mean accuracy: {self.metrics['mean_accuracy']:.3f}")
        return self.metrics

    def predict(self, df: pd.DataFrame) -> pd.DataFrame:
        """Predict direction for new data.
        
        Returns DataFrame with 'prediction_proba' and 'signal' columns.
        """
        if self.model is None:
            raise RuntimeError("Model not trained. Call train() first.")

        # Detect if model was trained with advanced features
        advanced_cols = {"nvt_ma7", "fed_rate", "social_volume_ma7", "fear_greed_ema7",
                         "exchange_inflow_ma7", "rate_change_30d", "active_addresses",
                         "dxy_index", "risk_off_proxy"}
        use_advanced = bool(advanced_cols.intersection(set(self.feature_names or [])))
        features_df = compute_features(df, advanced=use_advanced)
        feature_cols = self.feature_names or [c for c in features_df.columns if c not in [
            "open", "high", "low", "close", "volume",
            "target_return_5d", "target_direction",
            "target_return_20d", "target_direction_20d",
        ]]

        # Forward fill NaN for prediction
        X = features_df[feature_cols].ffill().bfill().values
        X_scaled = self.scaler.transform(X)

        if hasattr(self.model, "predict_proba"):
            proba = self.model.predict_proba(X_scaled)[:, 1]
        else:
            proba = self.model.predict(X_scaled).astype(float)

        features_df["prediction_proba"] = proba
        features_df["signal"] = np.where(
            proba > self.threshold, 1,
            np.where(proba < 1 - self.threshold, -1, 0)
        )
        return features_df

    def save(self, path: str):
        """Save model, scaler, and feature names."""
        import pickle
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "wb") as f:
            pickle.dump({
                "model": self.model,
                "scaler": self.scaler,
                "feature_names": self.feature_names,
                "threshold": self.threshold,
                "metrics": self.metrics,
            }, f)
        logger.info(f"Model saved to {path}")

    def load(self, path: str):
        """Load model, scaler, and feature names."""
        import pickle
        with open(path, "rb") as f:
            data = pickle.load(f)
        self.model = data["model"]
        self.scaler = data["scaler"]
        self.feature_names = data["feature_names"]
        self.threshold = data.get("threshold", 0.5)
        self.metrics = data.get("metrics", {})
        logger.info(f"Model loaded from {path}")


if __name__ == "__main__":
    # Quick test
    from data.feed import DataFeed
    feed = DataFeed()
    df = feed.fetch("BTC/USDT", timeframe="1d", limit=1000)

    pipeline = MLClassifierPipeline()
    metrics = pipeline.train(df)
    print(f"Accuracy: {metrics['mean_accuracy']:.3f}")
    print(f"F1: {metrics['mean_f1']:.3f}")

    # Top 10 features
    fi = metrics.get("feature_importance", {})
    if fi:
        top = sorted(fi.items(), key=lambda x: x[1], reverse=True)[:10]
        print("\nTop 10 features:")
        for name, score in top:
            print(f"  {name}: {score:.4f}")
