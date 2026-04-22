"""Pydantic models for FastAPI gateway."""

from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel


class StrategyState(BaseModel):
    name: str
    port: int
    equity: float
    capital: float
    open_positions: int
    running: bool
    mode: str = "paper"
    return_pct: float = 0.0
    daily_pnl: float = 0.0
    strategy_type: str = ""
    timestamp: datetime = datetime.utcnow()


class Position(BaseModel):
    symbol: str
    side: str
    entry_price: float
    size: float
    current_price: Optional[float] = None
    unrealized_pnl: Optional[float] = None
    stop_price: Optional[float] = None
    strategy: str = ""


class TrailingStopState(BaseModel):
    symbol: str
    entry_price: float
    peak_price: float
    current_stop: float
    activated: bool
    profit_pct: float


class SlippageSummary(BaseModel):
    symbol: str
    trades: int
    avg_slippage_pct: float
    max_slippage_pct: float
    total_cost: float


class Alert(BaseModel):
    level: str  # info, warning, error
    message: str
    timestamp: datetime = datetime.utcnow()
    source: str = ""


class DailyReport(BaseModel):
    date: str
    total_trades: int
    wins: int
    losses: int
    total_pnl: float
    winrate: float
    return_pct: float
    equity_start: float
    equity_end: float


class SystemState(BaseModel):
    timestamp: datetime
    strategies: List[StrategyState]
    positions: List[Position]
    trailing_stops: List[TrailingStopState]
    slippage: List[SlippageSummary]
    alerts: List[Alert]
