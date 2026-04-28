"""Tests for journal/trade_logger layer."""

import os
import tempfile

import pytest

from journal.trade_logger import EquitySnapshot, JournalEntry, TradeLogger, TradeRecord


class TestTradeLogger:
    @pytest.fixture
    def logger(self):
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        yield TradeLogger(db_path=path)
        os.unlink(path)

    def test_log_trade(self, logger):
        rid = logger.log_trade(
            TradeRecord(
                symbol="BTC/USDT",
                strategy="EMA-Trend",
                side="long",
                entry_price=64000,
                exit_price=65000,
                size=0.01,
                pnl=100,
                pnl_pct=0.0156,
                exit_reason="take_profit",
                reasoning="EMA cross",
                emotion_before="calm",
                emotion_after="confident",
            )
        )
        assert rid is not None
        assert rid > 0

    def test_get_trades(self, logger):
        logger.log_trade(
            TradeRecord(
                symbol="BTC/USDT",
                side="long",
                entry_price=60000,
                exit_price=61000,
                size=0.01,
                pnl=100,
            )
        )
        logger.log_trade(
            TradeRecord(
                symbol="ETH/USDT",
                side="long",
                entry_price=3000,
                exit_price=3100,
                size=0.1,
                pnl=100,
            )
        )
        trades = logger.get_trades(symbol="BTC/USDT")
        assert len(trades) == 1
        assert trades[0].symbol == "BTC/USDT"

    def test_trade_summary(self, logger):
        logger.log_trade(
            TradeRecord(
                symbol="BTC/USDT",
                side="long",
                entry_price=60000,
                exit_price=61000,
                size=0.01,
                pnl=100,
            )
        )
        logger.log_trade(
            TradeRecord(
                symbol="BTC/USDT",
                side="long",
                entry_price=60000,
                exit_price=59000,
                size=0.01,
                pnl=-100,
            )
        )
        summary = logger.trade_summary()
        assert summary["count"] == 2
        assert summary["winrate"] == 0.5
        assert summary["total_pnl"] == 0

    def test_log_journal(self, logger):
        jid = logger.log_journal(
            JournalEntry(
                date="2026-04-21",
                entry_type="post_session",
                content="Good discipline today",
                emotion="calm",
                focus_score=8,
                discipline_score=9,
            )
        )
        assert jid > 0
        entries = logger.get_journal(date="2026-04-21")
        assert len(entries) == 1
        assert entries[0].content == "Good discipline today"

    def test_snapshot(self, logger):
        sid = logger.snapshot(
            EquitySnapshot(
                equity=105000,
                cash=95000,
                open_positions=1,
                open_exposure=10000,
                drawdown_pct=0.05,
                daily_pnl=500,
            )
        )
        assert sid > 0
        snaps = logger.get_snapshots(limit=10)
        assert len(snaps) == 1
        assert snaps[0].equity == 105000

    def test_emotion_distribution(self, logger):
        logger.log_trade(
            TradeRecord(
                symbol="BTC/USDT",
                side="long",
                entry_price=60000,
                exit_price=61000,
                size=0.01,
                pnl=100,
                emotion_before="calm",
            )
        )
        logger.log_trade(
            TradeRecord(
                symbol="BTC/USDT",
                side="long",
                entry_price=60000,
                exit_price=61000,
                size=0.01,
                pnl=100,
                emotion_before="fomo",
            )
        )
        logger.log_trade(
            TradeRecord(
                symbol="BTC/USDT",
                side="long",
                entry_price=60000,
                exit_price=61000,
                size=0.01,
                pnl=100,
                emotion_before="calm",
            )
        )
        dist = logger.emotion_distribution()
        assert dist["calm"] == 2
        assert dist["fomo"] == 1

    def test_export_csv(self, logger, tmp_path):
        logger.log_trade(
            TradeRecord(
                symbol="BTC/USDT",
                side="long",
                entry_price=60000,
                exit_price=61000,
                size=0.01,
                pnl=100,
            )
        )
        csv_path = tmp_path / "trades.csv"
        logger.export_trades_csv(str(csv_path))
        assert csv_path.exists()
        content = csv_path.read_text()
        assert "BTC/USDT" in content

    def test_export_json(self, logger, tmp_path):
        logger.log_journal(JournalEntry(date="2026-04-21", content="Test"))
        json_path = tmp_path / "journal.json"
        logger.export_journal_json(str(json_path))
        assert json_path.exists()
        content = json_path.read_text()
        assert "Test" in content
