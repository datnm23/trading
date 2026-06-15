"""Pure parser functions for vnstock DataFrames — no network, no I/O.

These are extracted from VnstockSource so they can be unit-tested independently.
"""

from typing import Optional
import pandas as pd

from data.vn.models import FinancialStatement, Ratios

# Rows to skip when parsing ratio data (header/metadata rows)
_RATIO_SKIP_IDS = {"year", "quarter", "ratioTTMId", "ratioType", "ratioYearId"}


def parse_long_financials(
    df: Optional[pd.DataFrame],
    ticker: str,
    statement_type: str,
    period: str,
) -> FinancialStatement:
    """Convert vnstock long-format financial DataFrame → FinancialStatement.

    Long format columns: [item, item_en, item_id, <year cols>...]
    Year columns are labelled with year strings (e.g. '2024', '2023').
    """
    stmt = FinancialStatement(ticker=ticker, statement_type=statement_type, period=period)
    if df is None or df.empty:
        return stmt

    # Identify year-like columns (exclude item, item_en, item_id)
    meta_cols = {"item", "item_en", "item_id"}
    year_cols = [c for c in df.columns if c not in meta_cols]

    for _, row in df.iterrows():
        item_id = str(row.get("item_id", "")).strip()
        label = str(row.get("item", "")).strip()
        if not item_id:
            continue
        values: dict = {}
        for col in year_cols:
            val = row.get(col)
            try:
                fval = float(val)
                if pd.notna(fval):
                    values[str(col)] = fval
            except (TypeError, ValueError):
                pass
        if values:
            stmt.items[item_id] = values
            stmt.labels[item_id] = label

    return stmt


def parse_ratio_df(
    df: Optional[pd.DataFrame],
    ticker: str,
    period: str,
) -> Ratios:
    """Convert vnstock ratio DataFrame → Ratios.

    The ratio DataFrame is transposed:
      - Row 0: year values for each data column
      - Row 1: quarter values for each data column
      - Remaining rows: each row is a metric (item_id = machine key)
      - All data columns may share the same duplicate column name

    We build period labels as "YYYYqQ" (e.g. "2024q4") from rows 0-1.
    """
    ratios = Ratios(ticker=ticker, period=period)
    if df is None or df.empty:
        return ratios

    # Columns: [item, item_en, item_id, col3, col4, ...] (col3+ are data cols)
    # Access by integer position since data cols may have duplicate names.
    data_col_positions = list(range(3, len(df.columns)))
    if not data_col_positions:
        return ratios

    # Extract year/quarter from first two rows
    year_row = df.iloc[0]   # item_id = 'year'
    qtr_row = df.iloc[1]    # item_id = 'quarter'

    period_labels = []
    for pos in data_col_positions:
        yr = year_row.iloc[pos] if pos < len(year_row) else ""
        qtr = qtr_row.iloc[pos] if pos < len(qtr_row) else ""
        try:
            label = f"{int(yr)}q{int(qtr)}"
        except (ValueError, TypeError):
            label = f"col{pos}"
        period_labels.append(label)

    ratios.period_labels = period_labels

    # Parse metric rows (skip metadata rows)
    for _, row in df.iterrows():
        item_id = str(row.get("item_id", "")).strip()
        if not item_id or item_id in _RATIO_SKIP_IDS:
            continue
        values: dict = {}
        for i, pos in enumerate(data_col_positions):
            label = period_labels[i]
            val = row.iloc[pos]
            try:
                fval = float(val)
                if pd.notna(fval):
                    values[label] = fval
            except (TypeError, ValueError):
                pass
        if values:
            ratios.items[item_id] = values

    return ratios
