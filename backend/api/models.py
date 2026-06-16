"""Pydantic models for VN Stock Advisory API."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel

DISCLAIMER = "Chỉ mang tính tham khảo, không phải lời khuyên đầu tư."


class CriterionDetail(BaseModel):
    key: str
    label: str
    passed: bool
    value: Optional[float] = None
    weight: float


class ScreenerItem(BaseModel):
    ticker: str
    score: float
    rank: int
    passed_count: int
    criteria: List[CriterionDetail] = []


class ScreenerResponse(BaseModel):
    items: List[ScreenerItem]
    count: int
    disclaimer: str = DISCLAIMER


class PriceSummary(BaseModel):
    current_price: float           # VND absolute
    market_cap: float
    issue_share: float
    free_float_pct: Optional[float] = None
    foreigner_pct: Optional[float] = None


class FinancialSummary(BaseModel):
    """Key ratios snapshot — latest available period."""
    pe_ratio: Optional[float] = None
    pb_ratio: Optional[float] = None
    roe: Optional[float] = None
    net_margin: Optional[float] = None
    debt_to_equity: Optional[float] = None
    eps: Optional[float] = None


class CompanySummary(BaseModel):
    name: str
    short_name: str
    sector: str
    is_bank: bool
    listing_date: str


class StockDetail(BaseModel):
    ticker: str
    company: CompanySummary
    price: PriceSummary
    financials: FinancialSummary
    disclaimer: str = DISCLAIMER


class FinancialLineItem(BaseModel):
    item_id: str
    label: str                                  # Vietnamese label
    values: Dict[str, Optional[float]]          # period_label -> value


class FinancialStatementView(BaseModel):
    statement_type: str                         # balance_sheet | income_statement | cash_flow
    periods: List[str]                          # period labels, newest first
    rows: List[FinancialLineItem]


class FinancialsResponse(BaseModel):
    ticker: str
    period_type: str                            # year | quarter
    statements: List[FinancialStatementView]
    disclaimer: str = DISCLAIMER


class ValuationResponse(BaseModel):
    ticker: str
    current_price: float
    target_price: Optional[float] = None
    intrinsic_value: Optional[float] = None
    upside_pct: Optional[float] = None
    score: int
    recommendation: str            # BUY | HOLD | SELL
    f_score: Optional[int] = None
    f_score_applicable: int = 9
    z_score: Optional[float] = None
    dcf_applicable: bool = True
    reasons: List[str] = []
    disclaimer: str = DISCLAIMER


class RecommendationRead(BaseModel):
    id: int
    ticker: str
    date: str
    recommendation: str
    target_price: Optional[float] = None
    current_price: Optional[float] = None
    score: Optional[int] = None
    upside_pct: Optional[float] = None
    reasons: List[str] = []
    created_at: str


class PaperPositionRead(BaseModel):
    id: int
    ticker: str
    entry_date: str
    entry_price: float
    shares: float
    recommendation_id: Optional[int] = None
    status: str                    # open | closed
    exit_date: Optional[str] = None
    exit_price: Optional[float] = None
    pnl: Optional[float] = None
