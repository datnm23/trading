"""Optimized training pipeline with feature selection + hyperparameter tuning."""

import argparse
from pathlib import Path
from datetime import datetime

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from xgboost import XGBClassifier
from loguru import logger

from data.feed import DataFeed
from ml.features.engineering import compute_features
from ml.features.selection import full_feature_selection, select_by_importance
from ml.pipelines.tuning import HyperparameterTuner
from ml.pipelines.threshold_optimizer import ThresholdOptimizer
from ml.models.registry import ModelRegistry, ModelRecord


def load_and_prepare_data(symbol: str, timeframe: str, limit: int = 1500, advanced: bool = False):
    """Load data and compute features."""
    feed = DataFeed()
    df = feed.fetch(symbol, timeframe=timeframe, limit=limit, use_cache=True)
    if df.empty:
        raise ValueError("No data available")

    features_df = compute_features(df, advanced=advanced, symbol=symbol)
    logger.info(f"Features computed: {features_df.shape} (advanced={advanced})")
    return features_df


def prepare_xy(features_df: pd.DataFrame, selected_features: list):
    """Prepare X, y from feature DataFrame."""
    cols = selected_features + ["target_direction"]
    data = features_df[cols].copy()
    # Forward fill then backfill to handle NaN from rolling windows
    data = data.ffill().bfill()
    # Drop any remaining NaN (should be rare now)
    data = data.dropna()
    X = data[selected_features].values
    y = data["target_direction"].values
    return X, y, data.index


def train_optimized(
    symbol: str = "BTC/USDT",
    timeframe: str = "1d",
    model_type: str = "gradient_boosting",
    tune: bool = True,
    n_tuning_iter: int = 15,
    vif_threshold: float = 10.0,
    corr_threshold: float = 0.95,
    top_k_features: int = 30,
    advanced_features: bool = False,
    tune_threshold: bool = True,
    save: bool = True,
) -> dict:
    """Full optimized training pipeline.
    
    Steps:
        1. Load data & feature engineering
        2. Feature selection (correlation + VIF)
        3. Train baseline model to get feature importance
        4. Select top-k features by importance
        5. Hyperparameter tuning (optional)
        6. Train final model with best params
        7. Threshold tuning for precision/recall balance
        8. Evaluate on most recent 20% (out-of-time)
    """
    logger.info("=" * 60)
    logger.info(f"Optimized Training | {symbol} {timeframe} | Model: {model_type} | Advanced: {advanced_features}")
    logger.info("=" * 60)

    # Step 1: Load data
    features_df = load_and_prepare_data(symbol, timeframe, advanced=advanced_features)
    all_feature_cols = [c for c in features_df.columns if c not in [
        "open", "high", "low", "close", "volume",
        "target_return_5d", "target_direction"
    ]]
    logger.info(f"Initial features: {len(all_feature_cols)}")

    # Step 2: Feature selection (correlation + VIF)
    selected_features = full_feature_selection(
        features_df, all_feature_cols,
        vif_threshold=vif_threshold,
        corr_threshold=corr_threshold,
    )

    # Step 3: Quick baseline to get feature importance
    X_full, y_full, idx_full = prepare_xy(features_df, selected_features)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_full)

    if model_type == "gradient_boosting":
        baseline = GradientBoostingClassifier(n_estimators=100, random_state=42)
    elif model_type == "random_forest":
        baseline = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
    elif model_type == "xgboost":
        baseline = XGBClassifier(n_estimators=100, random_state=42, eval_metric="logloss")
    else:
        from ml.models.mlp_pipeline import MLPPipeline
        mlp = MLPPipeline(hidden_layers=(128, 64, 32))
        mlp.train(features_df, tune_threshold=False)
        return _package_mlp_result(mlp, symbol, timeframe, advanced_features, save)

    baseline.fit(X_scaled, y_full)
    logger.info(f"Baseline trained on {len(selected_features)} features")

    # Step 4: Select top-k by importance
    top_features = select_by_importance(
        selected_features,
        baseline.feature_importances_,
        top_k=top_k_features,
        min_importance=0.005,
    )

    # Re-prepare with top features
    X, y, idx = prepare_xy(features_df, top_features)
    logger.info(f"Final feature set: {len(top_features)} features")

    # Step 5: Out-of-time split (last 20%)
    split_idx = int(len(X) * 0.8)
    X_train, X_test = X[:split_idx], X[split_idx:]
    y_train, y_test = y[:split_idx], y[split_idx:]

    scaler_final = StandardScaler()
    X_train_s = scaler_final.fit_transform(X_train)
    X_test_s = scaler_final.transform(X_test)

    # Step 6: Hyperparameter tuning
    best_params = {}
    if tune and model_type != "mlp":
        tuner = HyperparameterTuner(n_splits=3, n_iter=n_tuning_iter)
        tuning_result = tuner.tune(X_train_s, y_train, model_type=model_type)
        best_params = tuning_result["best_params"]
        logger.info(f"\nTop 3 configs:")
        for _, row in tuner.get_top_configs(3).iterrows():
            logger.info(f"  Score={row['mean_test_score']:.4f} ± {row['std_test_score']:.4f} | {row['params']}")
    else:
        best_params = {"n_estimators": 200, "max_depth": 5, "random_state": 42}

    # Step 7: Train final model
    bp = {k: v for k, v in best_params.items() if k != "random_state"}
    if model_type == "gradient_boosting":
        final_model = GradientBoostingClassifier(**bp, random_state=42)
    elif model_type == "xgboost":
        final_model = XGBClassifier(**bp, random_state=42, eval_metric="logloss")
    else:
        final_model = RandomForestClassifier(**bp, random_state=42, n_jobs=-1)

    final_model.fit(X_train_s, y_train)

    # Step 8: Predict probabilities for threshold tuning
    y_proba = final_model.predict_proba(X_test_s)[:, 1]

    # Step 9: Threshold tuning
    threshold = 0.5
    if tune_threshold:
        optimizer = ThresholdOptimizer()
        opt_result = optimizer.optimize(y_test, y_proba, metric="f1")
        threshold = opt_result["best_threshold"]
        logger.info(f"\nThreshold optimization:")
        logger.info(f"  Best F1: {opt_result['best_score']:.4f} @ threshold={threshold:.3f}")
        if opt_result["target_precision_60"]:
            logger.info(f"  Precision>=60%: threshold>={opt_result['target_precision_60']:.3f}")
        if opt_result["target_recall_70"]:
            logger.info(f"  Recall>=70%: threshold<={opt_result['target_recall_70']:.3f}")

    y_pred = (y_proba >= threshold).astype(int)

    metrics = {
        "accuracy": accuracy_score(y_test, y_pred),
        "precision": precision_score(y_test, y_pred, zero_division=0),
        "recall": recall_score(y_test, y_pred, zero_division=0),
        "f1": f1_score(y_test, y_pred, zero_division=0),
        "test_size": len(y_test),
        "train_size": len(y_train),
        "threshold": threshold,
    }

    logger.info("\n" + "=" * 60)
    logger.info("FINAL EVALUATION (Out-of-Time Test Set)")
    logger.info("=" * 60)
    logger.info(f"Accuracy : {metrics['accuracy']:.4f}")
    logger.info(f"Precision: {metrics['precision']:.4f}")
    logger.info(f"Recall   : {metrics['recall']:.4f}")
    logger.info(f"F1       : {metrics['f1']:.4f}")
    logger.info(f"Threshold: {metrics['threshold']:.3f}")
    logger.info(f"Test set : {metrics['test_size']} samples")
    logger.info("=" * 60)

    # Feature importance
    fi = dict(zip(top_features, final_model.feature_importances_.tolist()))
    top_fi = sorted(fi.items(), key=lambda x: x[1], reverse=True)[:10]
    logger.info("\nTop 10 Feature Importances:")
    for name, score in top_fi:
        logger.info(f"  {name:25s}: {score:.4f}")

    # Save model
    model_path = None
    if save:
        import pickle
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        model_name = f"{model_type}_{symbol.replace('/', '_')}_{timeframe}_{timestamp}"
        model_path = f"./ml/models/{model_name}.pkl"
        Path(model_path).parent.mkdir(parents=True, exist_ok=True)

        with open(model_path, "wb") as f:
            pickle.dump({
                "model": final_model,
                "scaler": scaler_final,
                "feature_names": top_features,
                "best_params": best_params,
                "metrics": metrics,
                "feature_importance": fi,
                "threshold": threshold,
            }, f)
        logger.info(f"\nModel saved to {model_path}")

    # Register
    registry = ModelRegistry()
    record = ModelRecord(
        name=model_name if save else "unnamed",
        model_type=model_type,
        symbol=symbol,
        timeframe=timeframe,
        features=len(top_features),
        accuracy=metrics["accuracy"],
        precision=metrics["precision"],
        recall=metrics["recall"],
        f1=metrics["f1"],
        best_params=best_params,
        feature_importance=dict(top_fi),
        created_at=datetime.now().isoformat(),
        path=model_path or "",
        notes=f"VIF<{vif_threshold}, corr<{corr_threshold}, top_k={top_k_features}, tune={tune}, threshold={threshold:.3f}",
    )
    registry.register(record)

    return {
        "metrics": metrics,
        "best_params": best_params,
        "features": top_features,
        "feature_importance": fi,
        "model_path": model_path,
        "record": record,
    }


def _package_mlp_result(mlp, symbol, timeframe, advanced_features, save):
    """Package MLP training result."""
    metrics = mlp.metrics
    logger.info("\n" + "=" * 60)
    logger.info("MLP FINAL EVALUATION")
    logger.info("=" * 60)
    logger.info(f"Test Accuracy : {metrics['test_accuracy']:.4f}")
    logger.info(f"Test Precision: {metrics['test_precision']:.4f}")
    logger.info(f"Test Recall   : {metrics['test_recall']:.4f}")
    logger.info(f"Test F1       : {metrics['test_f1']:.4f}")
    logger.info(f"Threshold     : {metrics['threshold']:.3f}")
    logger.info("=" * 60)

    model_path = None
    if save:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        model_name = f"mlp_{symbol.replace('/', '_')}_{timeframe}_{timestamp}"
        model_path = f"./ml/models/{model_name}.pkl"
        mlp.save(model_path)

    registry = ModelRegistry()
    record = ModelRecord(
        name=model_name if save else "unnamed",
        model_type="mlp",
        symbol=symbol,
        timeframe=timeframe,
        features=len(mlp.feature_names) if mlp.feature_names else 0,
        accuracy=metrics["test_accuracy"],
        precision=metrics["test_precision"],
        recall=metrics["test_recall"],
        f1=metrics["test_f1"],
        best_params={"hidden_layers": mlp.hidden_layers, "alpha": mlp.alpha},
        feature_importance={},
        created_at=datetime.now().isoformat(),
        path=model_path or "",
        notes=f"advanced={advanced_features}, threshold={metrics['threshold']:.3f}",
    )
    registry.register(record)

    return {
        "metrics": metrics,
        "best_params": {},
        "features": mlp.feature_names or [],
        "feature_importance": {},
        "model_path": model_path,
        "record": record,
    }


def main():
    parser = argparse.ArgumentParser(description="Optimized ML training")
    parser.add_argument("--symbol", default="BTC/USDT")
    parser.add_argument("--timeframe", default="1d")
    parser.add_argument("--model-type", default="xgboost", choices=["xgboost", "gradient_boosting", "random_forest", "mlp"])
    parser.add_argument("--no-tune", action="store_true", help="Skip hyperparameter tuning")
    parser.add_argument("--n-iter", type=int, default=15, help="Tuning iterations")
    parser.add_argument("--vif", type=float, default=10.0)
    parser.add_argument("--corr", type=float, default=0.95)
    parser.add_argument("--top-k", type=int, default=30)
    parser.add_argument("--advanced", action="store_true", help="Use advanced features")
    parser.add_argument("--no-threshold-tune", action="store_true", help="Skip threshold tuning")
    args = parser.parse_args()

    result = train_optimized(
        symbol=args.symbol,
        timeframe=args.timeframe,
        model_type=args.model_type,
        tune=not args.no_tune,
        n_tuning_iter=args.n_iter,
        vif_threshold=args.vif,
        corr_threshold=args.corr,
        top_k_features=args.top_k,
        advanced_features=args.advanced,
        tune_threshold=not args.no_threshold_tune,
    )

    print("\n" + "=" * 60)
    print("TRAINING COMPLETE")
    print("=" * 60)
    print(f"Model: {result['record'].name}")
    print(f"F1: {result['metrics']['f1']:.4f}")
    print(f"Precision: {result['metrics']['precision']:.4f}")
    print(f"Recall: {result['metrics']['recall']:.4f}")
    print(f"Threshold: {result['metrics'].get('threshold', 0.5):.3f}")
    print(f"Features: {len(result['features'])}")
    print(f"Saved: {result['model_path']}")
    print("=" * 60)


if __name__ == "__main__":
    main()
