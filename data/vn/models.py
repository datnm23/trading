"""Data models for VN Stock Advisory.

All price values from vnstock OHLCV are in THOUSANDS of VND (e.g. 48.82 = 48,820đ).
Financial statement values are absolute VND floats.
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, Optional, Any


@dataclass
class FinancialStatement:
    """Normalized financial statement (balance_sheet | income_statement | cash_flow).

    items: dict[item_id -> dict[period_label -> float]]
        e.g. {"current_assets": {"2024": 1.2e12, "2023": 1.1e12}}
    labels: dict[item_id -> str]  (Vietnamese label)
    period: "year" | "quarter"
    """
    ticker: str
    statement_type: str   # 'balance_sheet' | 'income_statement' | 'cash_flow'
    period: str           # 'year' | 'quarter'
    items: Dict[str, Dict[str, float]] = field(default_factory=dict)
    labels: Dict[str, str] = field(default_factory=dict)

    def get(self, item_id: str, period_label: str) -> Optional[float]:
        """Return value for item_id at period_label, or None if missing."""
        return self.items.get(item_id, {}).get(period_label)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "FinancialStatement":
        return cls(
            ticker=d["ticker"],
            statement_type=d["statement_type"],
            period=d["period"],
            items=d.get("items", {}),
            labels=d.get("labels", {}),
        )


@dataclass
class Ratios:
    """Financial ratios for a ticker.

    items: dict[item_id -> dict[period_label -> float]]
        e.g. {"pe_ratio": {"2024Q4": 12.5, "2024Q3": 11.8}}
    period_labels: ordered list of period labels
    """
    ticker: str
    period: str   # 'year' | 'quarter'
    items: Dict[str, Dict[str, float]] = field(default_factory=dict)
    period_labels: list = field(default_factory=list)

    def get(self, item_id: str, period_label: str) -> Optional[float]:
        return self.items.get(item_id, {}).get(period_label)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Ratios":
        return cls(
            ticker=d["ticker"],
            period=d["period"],
            items=d.get("items", {}),
            period_labels=d.get("period_labels", []),
        )


@dataclass
class CompanyInfo:
    """Key company metadata from vnstock company.overview().

    Note: market_cap and current_price are in VND absolute values.
    """
    ticker: str
    organ_name: str = ""
    organ_short_name: str = ""
    sector: str = ""
    icb_code: str = ""          # icb_code_lv4 preferred
    com_group_code: str = ""
    market_cap: float = 0.0
    current_price: float = 0.0
    issue_share: float = 0.0
    target_price: Optional[float] = None
    upside_to_target_pct: Optional[float] = None
    dividend_per_share_tsr: Optional[float] = None
    free_float_pct: Optional[float] = None
    foreigner_pct: Optional[float] = None
    is_bank: bool = False
    listing_date: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "CompanyInfo":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})
