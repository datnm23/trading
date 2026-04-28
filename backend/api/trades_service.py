"""Trade history service — queries PostgreSQL for closed trades with sub-strategy metadata."""

import os
import json
from datetime import datetime
from typing import List, Dict, Optional

import psycopg2
from psycopg2.extras import RealDictCursor
from loguru import logger


class TradesService:
    """Query closed trades from PostgreSQL, parse sub-strategy metadata."""

    def __init__(self, db_url: Optional[str] = None):
        self.db_url = db_url or os.environ.get("TRADING_DB_URL")
        if not self.db_url:
            raise ValueError("TRADING_DB_URL required")

    def _connect(self):
        return psycopg2.connect(self.db_url)

    def get_trades(
        self,
        sub_strategy: Optional[str] = None,
        symbol: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict]:
        """Fetch closed trades with parsed sub-strategy metadata.

        Only returns trades with raw_metadata (sub-strategy info available).
        """
        conn = self._connect()
        try:
            cur = conn.cursor(cursor_factory=RealDictCursor)

            query = """
                SELECT id, timestamp, symbol, side, entry_price, exit_price,
                       size, pnl, pnl_pct, holding_bars, exit_reason,
                       stop_price, target_price, raw_metadata
                FROM trades
                WHERE raw_metadata IS NOT NULL
                  AND raw_metadata::text != ''
                  AND raw_metadata::text != '{}'
            """
            params: List = []

            if sub_strategy:
                query += " AND raw_metadata::jsonb->>'ensemble_source' = %s"
                params.append(sub_strategy)
            if symbol:
                query += " AND symbol = %s"
                params.append(symbol)
            if start_date:
                query += " AND timestamp >= %s"
                params.append(start_date)
            if end_date:
                query += " AND timestamp <= %s"
                params.append(end_date)

            query += " ORDER BY timestamp DESC LIMIT %s"
            params.append(limit)

            cur.execute(query, params)
            rows = cur.fetchall()

            return [self._parse_row(r) for r in rows]
        except Exception as e:
            logger.error(f"Trades query failed: {e}")
            return []
        finally:
            conn.close()

    def get_sub_strategy_stats(self) -> Dict[str, Dict]:
        """Compute cumulative P&L per sub-strategy from closed trades.

        Returns:
            Dict mapping ensemble_source -> {total_pnl, trade_count, winrate, avg_pnl}
        """
        conn = self._connect()
        try:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            # PostgreSQL: extract ensemble_source from JSONB and aggregate
            cur.execute("""
                SELECT
                    raw_metadata::jsonb->>'ensemble_source' as source,
                    COUNT(*) as trade_count,
                    SUM(pnl) as total_pnl,
                    AVG(pnl) as avg_pnl,
                    SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END)::float / NULLIF(COUNT(*), 0) as winrate
                FROM trades
                WHERE raw_metadata IS NOT NULL
                  AND raw_metadata::text != ''
                  AND raw_metadata::text != '{}'
                  AND raw_metadata::jsonb->>'ensemble_source' IS NOT NULL
                GROUP BY raw_metadata::jsonb->>'ensemble_source'
            """)
            rows = cur.fetchall()

            stats = {}
            for r in rows:
                source = r["source"]
                if not source:
                    continue
                stats[source] = {
                    "total_pnl": float(r["total_pnl"] or 0),
                    "trade_count": int(r["trade_count"] or 0),
                    "avg_pnl": float(r["avg_pnl"] or 0),
                    "winrate": float(r["winrate"] or 0),
                }
            return stats
        except Exception as e:
            logger.error(f"Sub-strategy stats query failed: {e}")
            return {}
        finally:
            conn.close()

    def _parse_row(self, row: Dict) -> Dict:
        """Parse DB row + extract sub-strategy metadata."""
        raw_meta = row.get("raw_metadata") or "{}"
        try:
            meta = json.loads(raw_meta)
        except json.JSONDecodeError:
            meta = {}

        # Calculate duration from holding_bars (assume 1h bars)
        duration = None
        holding_bars = row.get("holding_bars")
        if holding_bars:
            hours = holding_bars
            if hours < 24:
                duration = f"{hours}h"
            else:
                days = hours // 24
                rem_hours = hours % 24
                duration = f"{days}d {rem_hours}h" if rem_hours else f"{days}d"

        ts = row.get("timestamp")
        return {
            "id": row["id"],
            "timestamp": ts.isoformat() if isinstance(ts, datetime) else str(ts),
            "symbol": row["symbol"],
            "side": row["side"],
            "entry_price": float(row["entry_price"]) if row.get("entry_price") else 0.0,
            "exit_price": float(row["exit_price"]) if row.get("exit_price") else None,
            "size": float(row["size"]) if row.get("size") else 0.0,
            "pnl": float(row["pnl"]) if row.get("pnl") else 0.0,
            "pnl_pct": float(row["pnl_pct"]) if row.get("pnl_pct") else 0.0,
            "duration": duration,
            "exit_reason": row.get("exit_reason", ""),
            "stop_price": float(row["stop_price"]) if row.get("stop_price") else None,
            "target_price": float(row["target_price"]) if row.get("target_price") else None,
            "sub_strategy": meta.get("ensemble_source"),
            "wiki_alignment": meta.get("wiki_alignment"),
            "wiki_action": meta.get("wiki_action"),
            "regime": meta.get("regime"),
            "directional_regime": meta.get("directional_regime"),
            "status": "closed",
        }
