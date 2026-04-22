"""Feature selection: remove multicollinearity, low importance, high correlation."""

from typing import List, Tuple

import numpy as np
import pandas as pd
from loguru import logger


def compute_vif(df: pd.DataFrame, feature_cols: List[str]) -> pd.DataFrame:
    """Compute Variance Inflation Factor for each feature.
    
    VIF > 10 indicates high multicollinearity.
    """
    from sklearn.linear_model import LinearRegression

    vif_data = []
    for col in feature_cols:
        X = df[[c for c in feature_cols if c != col]].values
        y = df[col].values

        # Skip if any NaN
        mask = ~np.isnan(X).any(axis=1) & ~np.isnan(y)
        if mask.sum() < 10:
            vif_data.append({"feature": col, "vif": np.nan})
            continue

        X_clean = X[mask]
        y_clean = y[mask]

        if X_clean.shape[1] == 0:
            vif_data.append({"feature": col, "vif": 1.0})
            continue

        model = LinearRegression()
        model.fit(X_clean, y_clean)
        r2 = model.score(X_clean, y_clean)
        vif = 1.0 / (1.0 - r2 + 1e-10)
        vif_data.append({"feature": col, "vif": vif})

    return pd.DataFrame(vif_data)


def remove_high_vif(df: pd.DataFrame, feature_cols: List[str], threshold: float = 10.0) -> List[str]:
    """Iteratively remove features with highest VIF until all below threshold.
    
    Returns list of selected features.
    """
    selected = feature_cols.copy()

    while True:
        vif_df = compute_vif(df[selected].dropna(), selected)
        if vif_df["vif"].isna().all():
            logger.warning("All VIF values are NaN, stopping VIF selection")
            break
        max_vif = vif_df["vif"].max()
        max_feature = vif_df.loc[vif_df["vif"].idxmax(), "feature"]

        if max_vif <= threshold or pd.isna(max_vif):
            break

        logger.info(f"Removing {max_feature} (VIF={max_vif:.2f})")
        selected.remove(max_feature)

    logger.info(f"VIF selection: {len(feature_cols)} → {len(selected)} features")
    return selected


def remove_high_correlation(df: pd.DataFrame, feature_cols: List[str], threshold: float = 0.95) -> List[str]:
    """Remove one of each highly correlated pair.
    
    Returns list of selected features.
    """
    corr_matrix = df[feature_cols].corr().abs()
    upper = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))

    to_drop = set()
    for col in upper.columns:
        high_corr = upper[col][upper[col] > threshold].index.tolist()
        for other in high_corr:
            if other not in to_drop and col not in to_drop:
                to_drop.add(other)
                logger.info(f"Removing {other} (corr={upper.loc[col, other]:.3f} with {col})")

    selected = [c for c in feature_cols if c not in to_drop]
    logger.info(f"Correlation selection: {len(feature_cols)} → {len(selected)} features")
    return selected


def select_by_importance(
    feature_names: List[str],
    importances: np.ndarray,
    top_k: int = 30,
    min_importance: float = 0.005,
) -> List[str]:
    """Select top-k features by importance, filtering those below min_importance.
    
    Returns list of selected features.
    """
    fi = list(zip(feature_names, importances))
    fi_sorted = sorted(fi, key=lambda x: x[1], reverse=True)

    selected = []
    for name, score in fi_sorted[:top_k]:
        if score >= min_importance:
            selected.append(name)

    logger.info(f"Importance selection: {len(feature_names)} → {len(selected)} features (top_k={top_k}, min={min_importance})")
    return selected


def full_feature_selection(
    df: pd.DataFrame,
    feature_cols: List[str],
    vif_threshold: float = 10.0,
    corr_threshold: float = 0.95,
) -> List[str]:
    """Run full feature selection pipeline.
    
    Steps:
        1. Remove NaN rows
        2. Remove high correlation pairs
        3. Remove high VIF features
    
    Returns list of selected features.
    """
    # Step 1: Correlation filter
    selected = remove_high_correlation(df, feature_cols, threshold=corr_threshold)

    # Step 2: VIF filter
    selected = remove_high_vif(df, selected, threshold=vif_threshold)

    logger.info(f"Final selection: {len(feature_cols)} → {len(selected)} features")
    return selected
