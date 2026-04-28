"""Pydantic models for FastAPI gateway."""

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field


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
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    meta: dict[str, Any] | None = None


class Position(BaseModel):
    symbol: str
    side: str
    entry_price: float
    size: float
    current_price: float | None = None
    unrealized_pnl: float | None = None
    stop_price: float | None = None
    strategy: str = ""
    entry_time: str | None = None
    meta: dict[str, Any] | None = None


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


class PartialExitState(BaseModel):
    symbol: str
    entry: float
    initial_size: float
    remaining: float
    executed_count: int


class Alert(BaseModel):
    level: str  # info, warning, error
    message: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
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
    strategies: list[StrategyState]
    positions: list[Position]
    trailing_stops: list[TrailingStopState]
    slippage: list[SlippageSummary]
    alerts: list[Alert]
