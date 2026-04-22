"""Trade journal and emotional logging system.

Persists every trade decision, reasoning, and optional emotional state
to a local SQLite database. Supports querying, daily summaries, and export.

Schema:
    trades      -> individual trade executions (entry + exit pairs)
    journal     -> free-form daily journal entries with emotion tags
    snapshots   -> periodic equity / position snapshots
"""

import sqlite3
import json
import csv
from dataclasses import dataclass, asdict, field
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict
from contextlib import contextmanager

from loguru import logger


@dataclass
class TradeRecord:
    """Complete record of a single round-trip trade."""
    id: Optional[int] = None
    timestamp: datetime = field(default_factory=datetime.now)
    symbol: str = ""
    strategy: str = ""
    side: str = ""            # 'long' or 'short'
    entry_price: float = 0.0
    exit_price: float = 0.0
    size: float = 0.0
    pnl: float = 0.0
    pnl_pct: float = 0.0
    holding_bars: int = 0
    exit_reason: str = ""     # 'signal', 'stop_loss', 'take_profit', 'manual', 'liquidation'
    stop_price: Optional[float] = None
    target_price: Optional[float] = None
    reasoning: str = ""       # why this trade was taken
    emotion_before: Optional[str] = None   # e.g. 'calm', 'fomo', 'fear', 'confident'
    emotion_after: Optional[str] = None    # reflection after close
    market_regime: Optional[str] = None    # e.g. 'trending', 'ranging'
    notes: str = ""
    tags: str = ""            # comma-separated tags
    raw_metadata: str = ""    # JSON string for extensibility


@dataclass
class JournalEntry:
    """Daily or ad-hoc journal entry."""
    id: Optional[int] = None
    date: str = ""            # YYYY-MM-DD
    timestamp: datetime = field(default_factory=datetime.now)
    entry_type: str = "daily" # 'daily', 'pre_session', 'post_session', 'review'
    content: str = ""
    emotion: Optional[str] = None
    focus_score: Optional[int] = None      # 1-10 self-rated focus
    discipline_score: Optional[int] = None # 1-10 self-rated discipline
    lessons: str = ""
    tags: str = ""


@dataclass
class EquitySnapshot:
    """Periodic snapshot of account state."""
    id: Optional[int] = None
    timestamp: datetime = field(default_factory=datetime.now)
    equity: float = 0.0
    cash: float = 0.0
    open_positions: int = 0
    open_exposure: float = 0.0
    drawdown_pct: float = 0.0
    daily_pnl: float = 0.0


class TradeLogger:
    """SQLite-based trade journal and logger.

    Usage:
        logger = TradeLogger()
        logger.log_trade(TradeRecord(symbol="BTC/USDT", ...))
        logger.log_journal(JournalEntry(date="2026-04-21", content="..."))
        logger.snapshot(EquitySnapshot(equity=105000, ...))
    """

    def __init__(self, db_path: str = "./data/journal.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_tables()

    @contextmanager
    def _connect(self):
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _init_tables(self):
        with self._connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    strategy TEXT,
                    side TEXT,
                    entry_price REAL,
                    exit_price REAL,
                    size REAL,
                    pnl REAL,
                    pnl_pct REAL,
                    holding_bars INTEGER,
                    exit_reason TEXT,
                    stop_price REAL,
                    target_price REAL,
                    reasoning TEXT,
                    emotion_before TEXT,
                    emotion_after TEXT,
                    market_regime TEXT,
                    notes TEXT,
                    tags TEXT,
                    raw_metadata TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS journal (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    entry_type TEXT,
                    content TEXT,
                    emotion TEXT,
                    focus_score INTEGER,
                    discipline_score INTEGER,
                    lessons TEXT,
                    tags TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    equity REAL,
                    cash REAL,
                    open_positions INTEGER,
                    open_exposure REAL,
                    drawdown_pct REAL,
                    daily_pnl REAL
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades(symbol)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_trades_date ON trades(timestamp)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_journal_date ON journal(date)
            """)
            conn.commit()
            logger.info(f"Trade journal initialized at {self.db_path}")

    # ------------------------------------------------------------------
    # Trade logging
    # ------------------------------------------------------------------
    def log_trade(self, record: TradeRecord) -> int:
        """Insert a trade record and return its ID."""
        with self._connect() as conn:
            cur = conn.execute("""
                INSERT INTO trades (
                    timestamp, symbol, strategy, side, entry_price, exit_price,
                    size, pnl, pnl_pct, holding_bars, exit_reason, stop_price,
                    target_price, reasoning, emotion_before, emotion_after,
                    market_regime, notes, tags, raw_metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record.timestamp.isoformat(),
                record.symbol,
                record.strategy,
                record.side,
                record.entry_price,
                record.exit_price,
                record.size,
                record.pnl,
                record.pnl_pct,
                record.holding_bars,
                record.exit_reason,
                record.stop_price,
                record.target_price,
                record.reasoning,
                record.emotion_before,
                record.emotion_after,
                record.market_regime,
                record.notes,
                record.tags,
                record.raw_metadata,
            ))
            conn.commit()
            record_id = cur.lastrowid
            logger.info(
                f"Trade logged [{record_id}] {record.symbol} {record.side} "
                f"P&L=${record.pnl:.2f} ({record.pnl_pct:.2%})"
            )
            return record_id

    def get_trades(
        self,
        symbol: Optional[str] = None,
        strategy: Optional[str] = None,
        start: Optional[str] = None,
        end: Optional[str] = None,
        limit: int = 1000,
    ) -> List[TradeRecord]:
        """Query trades with optional filters."""
        query = "SELECT * FROM trades WHERE 1=1"
        params: List = []
        if symbol:
            query += " AND symbol = ?"
            params.append(symbol)
        if strategy:
            query += " AND strategy = ?"
            params.append(strategy)
        if start:
            query += " AND timestamp >= ?"
            params.append(start)
        if end:
            query += " AND timestamp <= ?"
            params.append(end)
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
            return [self._row_to_trade(r) for r in rows]

    def _row_to_trade(self, row: sqlite3.Row) -> TradeRecord:
        return TradeRecord(
            id=row["id"],
            timestamp=datetime.fromisoformat(row["timestamp"]),
            symbol=row["symbol"],
            strategy=row["strategy"] or "",
            side=row["side"] or "",
            entry_price=row["entry_price"] or 0.0,
            exit_price=row["exit_price"] or 0.0,
            size=row["size"] or 0.0,
            pnl=row["pnl"] or 0.0,
            pnl_pct=row["pnl_pct"] or 0.0,
            holding_bars=row["holding_bars"] or 0,
            exit_reason=row["exit_reason"] or "",
            stop_price=row["stop_price"],
            target_price=row["target_price"],
            reasoning=row["reasoning"] or "",
            emotion_before=row["emotion_before"],
            emotion_after=row["emotion_after"],
            market_regime=row["market_regime"],
            notes=row["notes"] or "",
            tags=row["tags"] or "",
            raw_metadata=row["raw_metadata"] or "",
        )

    # ------------------------------------------------------------------
    # Journal entries
    # ------------------------------------------------------------------
    def log_journal(self, entry: JournalEntry) -> int:
        """Insert a journal entry and return its ID."""
        with self._connect() as conn:
            cur = conn.execute("""
                INSERT INTO journal (
                    date, timestamp, entry_type, content, emotion,
                    focus_score, discipline_score, lessons, tags
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                entry.date,
                entry.timestamp.isoformat(),
                entry.entry_type,
                entry.content,
                entry.emotion,
                entry.focus_score,
                entry.discipline_score,
                entry.lessons,
                entry.tags,
            ))
            conn.commit()
            return cur.lastrowid

    def get_journal(self, date: Optional[str] = None, limit: int = 100) -> List[JournalEntry]:
        query = "SELECT * FROM journal WHERE 1=1"
        params: List = []
        if date:
            query += " AND date = ?"
            params.append(date)
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
            return [self._row_to_journal(r) for r in rows]

    def _row_to_journal(self, row: sqlite3.Row) -> JournalEntry:
        return JournalEntry(
            id=row["id"],
            date=row["date"],
            timestamp=datetime.fromisoformat(row["timestamp"]),
            entry_type=row["entry_type"] or "daily",
            content=row["content"] or "",
            emotion=row["emotion"],
            focus_score=row["focus_score"],
            discipline_score=row["discipline_score"],
            lessons=row["lessons"] or "",
            tags=row["tags"] or "",
        )

    # ------------------------------------------------------------------
    # Equity snapshots
    # ------------------------------------------------------------------
    def snapshot(self, snap: EquitySnapshot) -> int:
        """Record an equity snapshot."""
        with self._connect() as conn:
            cur = conn.execute("""
                INSERT INTO snapshots (
                    timestamp, equity, cash, open_positions, open_exposure,
                    drawdown_pct, daily_pnl
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                snap.timestamp.isoformat(),
                snap.equity,
                snap.cash,
                snap.open_positions,
                snap.open_exposure,
                snap.drawdown_pct,
                snap.daily_pnl,
            ))
            conn.commit()
            return cur.lastrowid

    def get_snapshots(self, limit: int = 1000) -> List[EquitySnapshot]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM snapshots ORDER BY timestamp DESC LIMIT ?", (limit,)
            ).fetchall()
            return [self._row_to_snapshot(r) for r in rows]

    def _row_to_snapshot(self, row: sqlite3.Row) -> EquitySnapshot:
        return EquitySnapshot(
            id=row["id"],
            timestamp=datetime.fromisoformat(row["timestamp"]),
            equity=row["equity"] or 0.0,
            cash=row["cash"] or 0.0,
            open_positions=row["open_positions"] or 0,
            open_exposure=row["open_exposure"] or 0.0,
            drawdown_pct=row["drawdown_pct"] or 0.0,
            daily_pnl=row["daily_pnl"] or 0.0,
        )

    # ------------------------------------------------------------------
    # Summary & analytics
    # ------------------------------------------------------------------
    def trade_summary(self, symbol: Optional[str] = None, strategy: Optional[str] = None) -> dict:
        """Compute summary statistics over logged trades."""
        query = "SELECT * FROM trades WHERE 1=1"
        params: List = []
        if symbol:
            query += " AND symbol = ?"
            params.append(symbol)
        if strategy:
            query += " AND strategy = ?"
            params.append(strategy)

        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()

        if not rows:
            return {"count": 0}

        pnls = [r["pnl"] for r in rows]
        wins = [p for p in pnls if p > 0]
        losses = [p for p in pnls if p <= 0]

        return {
            "count": len(rows),
            "total_pnl": sum(pnls),
            "avg_pnl": sum(pnls) / len(pnls),
            "winrate": len(wins) / len(pnls) if pnls else 0,
            "profit_factor": abs(sum(wins) / sum(losses)) if losses and sum(losses) != 0 else float("inf"),
            "avg_win": sum(wins) / len(wins) if wins else 0,
            "avg_loss": sum(losses) / len(losses) if losses else 0,
            "max_win": max(wins) if wins else 0,
            "max_loss": min(losses) if losses else 0,
        }

    def emotion_distribution(self) -> Dict[str, int]:
        """Count frequency of emotions recorded before trades."""
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT emotion_before, COUNT(*) as cnt FROM trades WHERE emotion_before IS NOT NULL GROUP BY emotion_before"
            ).fetchall()
            return {r["emotion_before"]: r["cnt"] for r in rows}

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------
    def export_trades_csv(self, path: str, symbol: Optional[str] = None):
        """Export trades to CSV."""
        trades = self.get_trades(symbol=symbol, limit=100000)
        if not trades:
            logger.warning("No trades to export")
            return

        fieldnames = [
            "timestamp", "symbol", "strategy", "side", "entry_price",
            "exit_price", "size", "pnl", "pnl_pct", "holding_bars",
            "exit_reason", "reasoning", "emotion_before", "emotion_after",
            "market_regime", "notes", "tags",
        ]
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for t in trades:
                writer.writerow({
                    "timestamp": t.timestamp.isoformat(),
                    "symbol": t.symbol,
                    "strategy": t.strategy,
                    "side": t.side,
                    "entry_price": t.entry_price,
                    "exit_price": t.exit_price,
                    "size": t.size,
                    "pnl": t.pnl,
                    "pnl_pct": t.pnl_pct,
                    "holding_bars": t.holding_bars,
                    "exit_reason": t.exit_reason,
                    "reasoning": t.reasoning,
                    "emotion_before": t.emotion_before,
                    "emotion_after": t.emotion_after,
                    "market_regime": t.market_regime,
                    "notes": t.notes,
                    "tags": t.tags,
                })
        logger.info(f"Exported {len(trades)} trades to {path}")

    def export_journal_json(self, path: str):
        """Export journal entries to JSON."""
        entries = self.get_journal(limit=100000)
        with open(path, "w", encoding="utf-8") as f:
            json.dump([asdict(e) for e in entries], f, ensure_ascii=False, indent=2, default=str)
        logger.info(f"Exported {len(entries)} journal entries to {path}")
