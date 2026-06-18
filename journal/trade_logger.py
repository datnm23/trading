"""Trade journal and emotional logging system.

Supports both SQLite (local file) and PostgreSQL (Docker/cloud).
Auto-detects backend from connection string.

Usage:
    # SQLite (default)
    logger = TradeLogger(db_path="./data/journal.db")

    # PostgreSQL
    logger = TradeLogger(
        db_url="postgresql://trader:trading123@localhost:5432/trading_journal"
    )

Schema:
    trades      -> individual trade executions (entry + exit pairs)
    journal     -> free-form daily journal entries with emotion tags
    snapshots   -> periodic equity / position snapshots
    equity_snapshots -> equity curve points
"""

import csv
import json
import sqlite3
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from loguru import logger

try:
    import psycopg2

    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False


@dataclass
class TradeRecord:
    """Complete record of a single round-trip trade."""

    id: int | None = None
    timestamp: datetime = field(default_factory=datetime.now)
    symbol: str = ""
    strategy: str = ""
    side: str = ""  # 'long' or 'short'
    entry_price: float = 0.0
    exit_price: float = 0.0
    size: float = 0.0
    pnl: float = 0.0
    pnl_pct: float = 0.0
    holding_bars: int = 0
    exit_reason: str = (
        ""  # 'signal', 'stop_loss', 'take_profit', 'manual', 'liquidation'
    )
    stop_price: float | None = None
    target_price: float | None = None
    reasoning: str = ""  # why this trade was taken
    emotion_before: str | None = None  # e.g. 'calm', 'fomo', 'fear', 'confident'
    emotion_after: str | None = None  # reflection after close
    market_regime: str | None = None  # e.g. 'trending', 'ranging'
    notes: str = ""
    tags: str = ""  # comma-separated tags
    raw_metadata: str = ""  # JSON string for extensibility


@dataclass
class JournalEntry:
    """Daily or ad-hoc journal entry."""

    id: int | None = None
    date: str = ""  # YYYY-MM-DD
    timestamp: datetime = field(default_factory=datetime.now)
    entry_type: str = "daily"  # 'daily', 'pre_session', 'post_session', 'review'
    content: str = ""
    emotion: str | None = None
    focus_score: int | None = None  # 1-10 self-rated focus
    discipline_score: int | None = None  # 1-10 self-rated discipline
    lessons: str = ""
    tags: str = ""


@dataclass
class EquitySnapshot:
    """Periodic snapshot of account state."""

    id: int | None = None
    timestamp: datetime = field(default_factory=datetime.now)
    equity: float = 0.0
    cash: float = 0.0
    open_positions: int = 0
    open_exposure: float = 0.0
    drawdown_pct: float = 0.0
    daily_pnl: float = 0.0


class TradeLogger:
    """Trade journal supporting SQLite and PostgreSQL backends.

    Usage:
        logger = TradeLogger()
        logger.log_trade(TradeRecord(symbol="BTC/USDT", ...))
        logger.log_journal(JournalEntry(date="2026-04-21", content="..."))
        logger.snapshot(EquitySnapshot(equity=105000, ...))
    """

    def __init__(
        self,
        db_path: str = "./data/journal.db",
        db_url: str | None = None,
    ):
        self.db_url = db_url
        self.db_path = Path(db_path) if db_path else None
        self.backend = (
            "postgres" if (db_url and db_url.startswith("postgresql://")) else "sqlite"
        )

        if self.backend == "postgres":
            if not POSTGRES_AVAILABLE:
                raise ImportError(
                    "psycopg2-binary required for PostgreSQL. Run: pip install psycopg2-binary"
                )
            parsed = urlparse(db_url)
            self.pg_config = {
                "host": parsed.hostname or "localhost",
                "port": parsed.port or 5432,
                "dbname": parsed.path.lstrip("/") if parsed.path else "trading_journal",
                "user": parsed.username or "trader",
                "password": parsed.password or "",
            }
            self._init_tables_pg()
        else:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            self._init_tables_sqlite()

    @contextmanager
    def _connect(self):
        if self.backend == "postgres":
            conn = psycopg2.connect(**self.pg_config)
            try:
                yield conn
            finally:
                conn.close()
        else:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            try:
                yield conn
            finally:
                conn.close()

    def _ph(self) -> str:
        """Return parameter placeholder for current backend."""
        return "%s" if self.backend == "postgres" else "?"

    def _exec(self, conn, sql: str, params: tuple = ()):
        """Execute SQL and return cursor."""
        cur = conn.cursor()
        cur.execute(sql, params)
        return cur

    def _fetchall(self, cur) -> list[dict[str, Any]]:
        """Fetch all rows as dicts (uniform for both backends)."""
        if self.backend == "postgres":
            rows = cur.fetchall()
            if not rows:
                return []
            cols = [desc[0] for desc in cur.description]
            return [dict(zip(cols, row)) for row in rows]
        else:
            rows = cur.fetchall()
            return [dict(r) for r in rows]

    def _fetchone(self, cur) -> dict[str, Any] | None:
        """Fetch one row as dict."""
        rows = self._fetchall(cur)
        return rows[0] if rows else None

    def _dt(self, dt: datetime) -> Any:
        """Serialize datetime for current backend."""
        if self.backend == "postgres":
            return dt
        return dt.isoformat()

    def _lastrowid(self, cur) -> int:
        """Get last inserted ID."""
        if self.backend == "postgres":
            row = cur.fetchone()
            return row[0] if row else 0
        return cur.lastrowid

    # ------------------------------------------------------------------
    # Table init
    # ------------------------------------------------------------------
    def _init_tables_sqlite(self):
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
                CREATE TABLE IF NOT EXISTS equity_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    equity REAL,
                    cash REAL,
                    open_positions INTEGER,
                    drawdown_pct REAL
                )
            """)
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades(symbol)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_trades_date ON trades(timestamp)"
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_journal_date ON journal(date)")
            conn.execute("""
                CREATE TABLE IF NOT EXISTS wiki_feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    regime TEXT,
                    side TEXT,
                    strategy TEXT,
                    wiki_action TEXT,
                    alignment_score REAL,
                    min_alignment REAL,
                    outcome TEXT,
                    pnl REAL,
                    pnl_pct REAL,
                    top_concepts TEXT,
                    context_summary TEXT
                )
            """)
            conn.commit()
            logger.info(f"Trade journal initialized at {self.db_path}")

    def _init_tables_pg(self):
        with self._connect() as conn:
            cur = conn.cursor()
            # Tables (use IF NOT EXISTS to be safe)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS trades (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    symbol VARCHAR(20) NOT NULL,
                    strategy VARCHAR(50),
                    side VARCHAR(10),
                    entry_price NUMERIC(20, 8),
                    exit_price NUMERIC(20, 8),
                    size NUMERIC(20, 8),
                    pnl NUMERIC(20, 2),
                    pnl_pct NUMERIC(10, 4),
                    holding_bars INTEGER,
                    exit_reason VARCHAR(50),
                    stop_price NUMERIC(20, 8),
                    target_price NUMERIC(20, 8),
                    reasoning TEXT,
                    emotion_before VARCHAR(20),
                    emotion_after VARCHAR(20),
                    market_regime VARCHAR(20),
                    notes TEXT,
                    tags VARCHAR(255),
                    raw_metadata JSONB
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS journal (
                    id SERIAL PRIMARY KEY,
                    date DATE NOT NULL,
                    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    entry_type VARCHAR(30),
                    content TEXT,
                    emotion VARCHAR(20),
                    focus_score INTEGER,
                    discipline_score INTEGER,
                    lessons TEXT,
                    tags VARCHAR(255)
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS snapshots (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    equity NUMERIC(20, 2),
                    cash NUMERIC(20, 2),
                    open_positions INTEGER,
                    open_exposure NUMERIC(20, 2),
                    drawdown_pct NUMERIC(10, 4),
                    daily_pnl NUMERIC(20, 2)
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS equity_snapshots (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    equity NUMERIC(20, 2),
                    cash NUMERIC(20, 2),
                    open_positions INTEGER,
                    drawdown_pct NUMERIC(10, 4)
                )
            """)
            # Indexes
            cur.execute(
                "CREATE INDEX IF NOT EXISTS idx_trades_timestamp ON trades(timestamp)"
            )
            cur.execute(
                "CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades(symbol)"
            )
            cur.execute("CREATE INDEX IF NOT EXISTS idx_journal_date ON journal(date)")
            cur.execute(
                "CREATE INDEX IF NOT EXISTS idx_snapshots_timestamp ON snapshots(timestamp)"
            )
            cur.execute(
                "CREATE INDEX IF NOT EXISTS idx_equity_timestamp ON equity_snapshots(timestamp)"
            )
            # Wiki feedback table for learning loop
            cur.execute("""
                CREATE TABLE IF NOT EXISTS wiki_feedback (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    symbol VARCHAR(20) NOT NULL,
                    regime VARCHAR(20),
                    side VARCHAR(10),
                    strategy VARCHAR(50),
                    wiki_action VARCHAR(20),      -- 'blocked', 'accepted', 'downgraded'
                    alignment_score NUMERIC(5, 4),
                    min_alignment NUMERIC(5, 4),
                    outcome VARCHAR(10),          -- 'win', 'loss', 'pending'
                    pnl NUMERIC(20, 2),
                    pnl_pct NUMERIC(10, 4),
                    top_concepts TEXT,
                    context_summary TEXT
                )
            """)
            cur.execute(
                "CREATE INDEX IF NOT EXISTS idx_wiki_outcome ON wiki_feedback(outcome)"
            )
            cur.execute(
                "CREATE INDEX IF NOT EXISTS idx_wiki_symbol ON wiki_feedback(symbol)"
            )
            conn.commit()
            logger.info(
                f"Trade journal initialized at PostgreSQL "
                f"{self.pg_config['host']}:{self.pg_config['port']}/{self.pg_config['dbname']}"
            )

    # ------------------------------------------------------------------
    # Trade logging
    # ------------------------------------------------------------------
    def log_trade(self, record: TradeRecord) -> int:
        """Insert a trade record and return its ID."""
        ph = self._ph()
        if self.backend == "postgres":
            sql = f"""
                INSERT INTO trades (
                    timestamp, symbol, strategy, side, entry_price, exit_price,
                    size, pnl, pnl_pct, holding_bars, exit_reason, stop_price,
                    target_price, reasoning, emotion_before, emotion_after,
                    market_regime, notes, tags, raw_metadata
                ) VALUES ({', '.join([ph]*20)})
                RETURNING id
            """
        else:
            sql = f"""
                INSERT INTO trades (
                    timestamp, symbol, strategy, side, entry_price, exit_price,
                    size, pnl, pnl_pct, holding_bars, exit_reason, stop_price,
                    target_price, reasoning, emotion_before, emotion_after,
                    market_regime, notes, tags, raw_metadata
                ) VALUES ({', '.join([ph]*20)})
            """
        params = (
            self._dt(record.timestamp),
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
        )
        with self._connect() as conn:
            cur = self._exec(conn, sql, params)
            conn.commit()
            record_id = self._lastrowid(cur)
            logger.info(
                f"Trade logged [{record_id}] {record.symbol} {record.side} "
                f"P&L=${record.pnl:.2f} ({record.pnl_pct:.2%})"
            )
            return record_id

    def get_trades(
        self,
        symbol: str | None = None,
        strategy: str | None = None,
        start: str | None = None,
        end: str | None = None,
        limit: int = 1000,
    ) -> list[TradeRecord]:
        """Query trades with optional filters."""
        ph = self._ph()
        query = "SELECT * FROM trades WHERE 1=1"
        params: list = []
        if symbol:
            query += f" AND symbol = {ph}"
            params.append(symbol)
        if strategy:
            query += f" AND strategy = {ph}"
            params.append(strategy)
        if start:
            query += f" AND timestamp >= {ph}"
            params.append(start)
        if end:
            query += f" AND timestamp <= {ph}"
            params.append(end)
        limit = max(1, int(limit))
        query += f" ORDER BY timestamp DESC LIMIT {ph}"
        params.append(limit)

        with self._connect() as conn:
            cur = self._exec(conn, query, tuple(params))
            rows = self._fetchall(cur)
            return [self._row_to_trade(r) for r in rows]

    def _row_to_trade(self, row: dict[str, Any]) -> TradeRecord:
        ts = row["timestamp"]
        if isinstance(ts, str):
            ts = datetime.fromisoformat(ts)
        return TradeRecord(
            id=row["id"],
            timestamp=ts,
            symbol=row["symbol"] or "",
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
        ph = self._ph()
        if self.backend == "postgres":
            sql = f"""
                INSERT INTO journal (
                    date, timestamp, entry_type, content, emotion,
                    focus_score, discipline_score, lessons, tags
                ) VALUES ({', '.join([ph]*9)})
                RETURNING id
            """
        else:
            sql = f"""
                INSERT INTO journal (
                    date, timestamp, entry_type, content, emotion,
                    focus_score, discipline_score, lessons, tags
                ) VALUES ({', '.join([ph]*9)})
            """
        params = (
            entry.date,
            self._dt(entry.timestamp),
            entry.entry_type,
            entry.content,
            entry.emotion,
            entry.focus_score,
            entry.discipline_score,
            entry.lessons,
            entry.tags,
        )
        with self._connect() as conn:
            cur = self._exec(conn, sql, params)
            conn.commit()
            return self._lastrowid(cur)

    def get_journal(
        self, date: str | None = None, limit: int = 100
    ) -> list[JournalEntry]:
        ph = self._ph()
        query = "SELECT * FROM journal WHERE 1=1"
        params: list = []
        if date:
            query += f" AND date = {ph}"
            params.append(date)
        query += f" ORDER BY timestamp DESC LIMIT {ph}"
        params.append(limit)

        with self._connect() as conn:
            cur = self._exec(conn, query, tuple(params))
            rows = self._fetchall(cur)
            return [self._row_to_journal(r) for r in rows]

    def _row_to_journal(self, row: dict[str, Any]) -> JournalEntry:
        ts = row["timestamp"]
        if isinstance(ts, str):
            ts = datetime.fromisoformat(ts)
        return JournalEntry(
            id=row["id"],
            date=row["date"],
            timestamp=ts,
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
        ph = self._ph()
        if self.backend == "postgres":
            sql = f"""
                INSERT INTO snapshots (
                    timestamp, equity, cash, open_positions, open_exposure,
                    drawdown_pct, daily_pnl
                ) VALUES ({', '.join([ph]*7)})
                RETURNING id
            """
        else:
            sql = f"""
                INSERT INTO snapshots (
                    timestamp, equity, cash, open_positions, open_exposure,
                    drawdown_pct, daily_pnl
                ) VALUES ({', '.join([ph]*7)})
            """
        params = (
            self._dt(snap.timestamp),
            snap.equity,
            snap.cash,
            snap.open_positions,
            snap.open_exposure,
            snap.drawdown_pct,
            snap.daily_pnl,
        )
        with self._connect() as conn:
            cur = self._exec(conn, sql, params)
            conn.commit()
            return self._lastrowid(cur)

    def get_snapshots(self, limit: int = 1000) -> list[EquitySnapshot]:
        ph = self._ph()
        with self._connect() as conn:
            cur = self._exec(
                conn,
                f"SELECT * FROM snapshots ORDER BY timestamp DESC LIMIT {ph}",
                (limit,),
            )
            rows = self._fetchall(cur)
            return [self._row_to_snapshot(r) for r in rows]

    def _row_to_snapshot(self, row: dict[str, Any]) -> EquitySnapshot:
        ts = row["timestamp"]
        if isinstance(ts, str):
            ts = datetime.fromisoformat(ts)
        return EquitySnapshot(
            id=row["id"],
            timestamp=ts,
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
    def trade_summary(
        self, symbol: str | None = None, strategy: str | None = None
    ) -> dict:
        """Compute summary statistics over logged trades."""
        ph = self._ph()
        query = "SELECT * FROM trades WHERE 1=1"
        params: list = []
        if symbol:
            query += f" AND symbol = {ph}"
            params.append(symbol)
        if strategy:
            query += f" AND strategy = {ph}"
            params.append(strategy)

        with self._connect() as conn:
            cur = self._exec(conn, query, tuple(params))
            rows = self._fetchall(cur)

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
            "profit_factor": (
                abs(sum(wins) / sum(losses))
                if losses and sum(losses) != 0
                else float("inf")
            ),
            "avg_win": sum(wins) / len(wins) if wins else 0,
            "avg_loss": sum(losses) / len(losses) if losses else 0,
            "max_win": max(wins) if wins else 0,
            "max_loss": min(losses) if losses else 0,
        }

    def emotion_distribution(self) -> dict[str, int]:
        """Count frequency of emotions recorded before trades."""
        with self._connect() as conn:
            cur = self._exec(
                conn,
                (
                    "SELECT emotion_before, COUNT(*) as cnt FROM trades "
                    "WHERE emotion_before IS NOT NULL GROUP BY emotion_before"
                ),
                (),
            )
            rows = self._fetchall(cur)
            return {r["emotion_before"]: r["cnt"] for r in rows}

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------
    def export_trades_csv(self, path: str, symbol: str | None = None):
        """Export trades to CSV."""
        trades = self.get_trades(symbol=symbol, limit=100000)
        if not trades:
            logger.warning("No trades to export")
            return

        fieldnames = [
            "timestamp",
            "symbol",
            "strategy",
            "side",
            "entry_price",
            "exit_price",
            "size",
            "pnl",
            "pnl_pct",
            "holding_bars",
            "exit_reason",
            "reasoning",
            "emotion_before",
            "emotion_after",
            "market_regime",
            "notes",
            "tags",
        ]
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for t in trades:
                writer.writerow(
                    {
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
                    }
                )
        logger.info(f"Exported {len(trades)} trades to {path}")

    def export_journal_json(self, path: str):
        """Export journal entries to JSON."""
        entries = self.get_journal(limit=100000)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(
                [asdict(e) for e in entries],
                f,
                ensure_ascii=False,
                indent=2,
                default=str,
            )
        logger.info(f"Exported {len(entries)} journal entries to {path}")

    # ------------------------------------------------------------------
    # Wiki feedback logging
    # ------------------------------------------------------------------
    def log_wiki_feedback(self, data: dict) -> int:
        """Log a wiki validation decision for future learning.

        Args:
            data: dict with keys: symbol, regime, side, strategy,
                  wiki_action, alignment_score, min_alignment,
                  top_concepts, context_summary
        """
        ph = self._ph()
        sql = f"""
            INSERT INTO wiki_feedback (
                timestamp, symbol, regime, side, strategy,
                wiki_action, alignment_score, min_alignment,
                outcome, pnl, pnl_pct, top_concepts, context_summary
            ) VALUES ({', '.join([ph]*13)})
        """
        params = (
            self._dt(datetime.now()),
            data.get("symbol", ""),
            data.get("regime", ""),
            data.get("side", ""),
            data.get("strategy", ""),
            data.get("wiki_action", ""),
            data.get("alignment_score", 0),
            data.get("min_alignment", 0),
            data.get("outcome", "pending"),
            data.get("pnl", None),
            data.get("pnl_pct", None),
            data.get("top_concepts", ""),
            data.get("context_summary", "")[:500],
        )
        with self._connect() as conn:
            cur = self._exec(conn, sql, params)
            conn.commit()
            return self._lastrowid(cur)

    def update_wiki_feedback(
        self, feedback_id: int, outcome: str, pnl: float, pnl_pct: float
    ) -> bool:
        """Update wiki feedback outcome after trade close."""
        ph = self._ph()
        sql = f"UPDATE wiki_feedback SET outcome={ph}, pnl={ph}, pnl_pct={ph} WHERE id={ph}"
        params = (outcome, pnl, pnl_pct, feedback_id)
        try:
            with self._connect() as conn:
                cur = self._exec(conn, sql, params)
                conn.commit()
                return cur.rowcount > 0
        except Exception as e:
            logger.warning(f"Failed to update wiki feedback {feedback_id}: {e}")
            return False

    def get_wiki_feedback_stats(self, min_samples: int = 10) -> dict:
        """Compute wiki validation accuracy from feedback history."""
        with self._connect() as conn:
            cur = self._exec(
                conn,
                "SELECT wiki_action, outcome FROM wiki_feedback WHERE outcome != 'pending'",
                (),
            )
            rows = self._fetchall(cur)

        if len(rows) < min_samples:
            return {"samples": len(rows), "accuracy": None}

        # For accepted signals: outcome should be 'win'
        # For blocked signals: outcome should be 'loss' (wiki was right to block)
        correct = 0
        for r in rows:
            action = r["wiki_action"]
            outcome = r["outcome"]
            if action == "accepted" and outcome == "win":
                correct += 1
            elif action == "blocked" and outcome == "loss":
                correct += 1
            elif action == "downgraded":
                # Downgraded signals that win = wiki was too conservative
                # Downgraded signals that lose = wiki was right
                if outcome == "loss":
                    correct += 1

        return {
            "samples": len(rows),
            "accuracy": correct / len(rows) if rows else 0,
            "correct": correct,
        }

    # ------------------------------------------------------------------
    # Migration helper
    # ------------------------------------------------------------------
    def migrate_from_sqlite(self, sqlite_path: str):
        """Migrate data from SQLite to current backend (PostgreSQL)."""
        if self.backend != "postgres":
            raise ValueError(
                "migrate_from_sqlite only works when connected to PostgreSQL"
            )

        logger.info(f"Migrating data from {sqlite_path} to PostgreSQL...")
        src = TradeLogger(db_path=sqlite_path)

        # Migrate trades
        trades = src.get_trades(limit=100000)
        for t in trades:
            self.log_trade(t)

        # Migrate journal
        entries = src.get_journal(limit=100000)
        for e in entries:
            self.log_journal(e)

        # Migrate snapshots
        snaps = src.get_snapshots(limit=100000)
        for s in snaps:
            self.snapshot(s)

        logger.info(
            f"Migration complete: {len(trades)} trades, {len(entries)} journal entries, {len(snaps)} snapshots"
        )
