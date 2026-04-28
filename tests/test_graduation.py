"""Tests for GraduationService."""

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

from backend.api.graduation_service import GraduationService


def make_fake_trade(ts: datetime, pnl: float) -> dict:
    return {
        "timestamp": ts,
        "pnl": pnl,
        "pnl_pct": pnl / 1000,
        "exit_price": 100,
        "entry_price": 100,
    }


class TestGraduationService:
    def test_empty_db_returns_empty_result(self):
        svc = GraduationService(initial_capital=100000)
        svc.db_url = None
        result = svc.compute_metrics()
        assert result["approved"] is False
        assert result["trade_count"] == 0
        assert "No database" in result["message"]

    def test_no_trades_returns_no_data(self):
        svc = GraduationService(initial_capital=100000)
        svc.db_url = "postgresql://test:test@localhost/test"
        with patch.object(svc, "_connect") as mock_conn:
            mock_cur = MagicMock()
            mock_cur.fetchall.return_value = []
            mock_conn.return_value.cursor.return_value = mock_cur
            result = svc.compute_metrics()
            assert result["approved"] is False
            assert "No trades" in result["message"]

    def test_approved_when_all_gates_pass(self):
        svc = GraduationService(initial_capital=100000)
        svc.db_url = "postgresql://test:test@localhost/test"
        now = datetime.now(UTC)
        trades = []
        for i in range(30):
            ts = now - timedelta(days=i)
            # 25 wins, 5 losses, positive P&L
            pnl = 500 if i % 6 != 0 else -100
            trades.append(make_fake_trade(ts, pnl))

        with patch.object(svc, "_connect") as mock_conn:
            mock_cur = MagicMock()
            mock_cur.fetchall.return_value = trades
            mock_conn.return_value.cursor.return_value = mock_cur
            result = svc.compute_metrics()
            assert result["days_traded"] == 30
            assert result["trade_count"] == 30
            assert result["return_pct"] > 0
            assert result["winrate"] > 40
            assert result["max_drawdown_pct"] < 10
            assert result["sharpe"] > 0.5
            assert result["approved"] is True
            assert all(result["gates"].values())

    def test_not_approved_with_negative_return(self):
        svc = GraduationService(initial_capital=100000)
        svc.db_url = "postgresql://test:test@localhost/test"
        now = datetime.now(UTC)
        trades = [make_fake_trade(now - timedelta(days=i), -500) for i in range(30)]

        with patch.object(svc, "_connect") as mock_conn:
            mock_cur = MagicMock()
            mock_cur.fetchall.return_value = trades
            mock_conn.return_value.cursor.return_value = mock_cur
            result = svc.compute_metrics()
            assert result["approved"] is False
            assert result["gates"]["return_positive"] is False

    def test_not_approved_with_high_drawdown(self):
        svc = GraduationService(initial_capital=100000)
        svc.db_url = "postgresql://test:test@localhost/test"
        now = datetime.now(UTC)
        trades = []
        for i in range(30):
            pnl = 100 if i != 15 else -15000  # one massive loss
            trades.append(make_fake_trade(now - timedelta(days=i), pnl))

        with patch.object(svc, "_connect") as mock_conn:
            mock_cur = MagicMock()
            mock_cur.fetchall.return_value = trades
            mock_conn.return_value.cursor.return_value = mock_cur
            result = svc.compute_metrics()
            assert result["approved"] is False
            assert result["gates"]["drawdown"] is False

    def test_telegram_alert_sent_once(self, tmp_path, monkeypatch):
        notify_file = tmp_path / "graduation_notified"
        monkeypatch.setenv("GRADUATION_NOTIFY_FILE", str(notify_file))
        svc = GraduationService(initial_capital=100000)
        svc.db_url = "postgresql://test:test@localhost/test"
        now = datetime.now(UTC)
        # Need variance in daily returns for sharpe > 0.5
        trades = []
        for i in range(30):
            ts = now - timedelta(days=i)
            # Varying daily P&L for standard deviation > 0
            daily_pnl = 500 + (i % 7) * 100  # 500, 600, 700, ... varying
            trades.append(make_fake_trade(ts, daily_pnl))
            trades.append(make_fake_trade(ts, -50))  # one small loss for winrate

        with patch.object(svc, "_connect") as mock_conn:
            mock_cur = MagicMock()
            mock_cur.fetchall.return_value = trades
            mock_conn.return_value.cursor.return_value = mock_cur
            with patch.object(svc._alerter, "send") as mock_send:
                result1 = svc.compute_metrics()
                assert result1["approved"] is True, f"Expected approved, got: {result1}"
                mock_send.assert_called_once()
                # Second call should not send again
                svc.compute_metrics()
                mock_send.assert_called_once()
                # Persistence file should exist
                assert notify_file.exists()

    def test_notification_persisted_across_restarts(self, tmp_path, monkeypatch):
        notify_file = tmp_path / "graduation_notified"
        notify_file.write_text("2026-01-01T00:00:00+00:00")
        monkeypatch.setenv("GRADUATION_NOTIFY_FILE", str(notify_file))
        svc = GraduationService(initial_capital=100000)
        assert svc._notified is True

    def test_reset_notification(self, tmp_path, monkeypatch):
        notify_file = tmp_path / "graduation_notified"
        notify_file.write_text("2026-01-01T00:00:00+00:00")
        monkeypatch.setenv("GRADUATION_NOTIFY_FILE", str(notify_file))
        svc = GraduationService(initial_capital=100000)
        assert svc._notified is True
        svc.reset_notification()
        assert svc._notified is False
        assert not notify_file.exists()
