"""Tests for psychological enforcer."""

import pytest
from datetime import datetime, timedelta

from risk.psychology import PsychologicalEnforcer, PsychologicalState


class TestPsychologicalEnforcer:
    def test_consecutive_loss_pause(self):
        enforcer = PsychologicalEnforcer({"max_consecutive_losses": 3})
        enforcer.check_state(pnl=-100)
        enforcer.check_state(pnl=-100)
        state = enforcer.check_state(pnl=-100)
        assert state.is_paused is True
        assert state.consecutive_losses == 3
        assert "3 consecutive losses" in state.blocked_reason

    def test_pause_expires(self):
        enforcer = PsychologicalEnforcer({
            "max_consecutive_losses": 2,
            "pause_after_losses_hours": 0,
        })
        enforcer.check_state(pnl=-100)
        state = enforcer.check_state(pnl=-100)
        assert state.is_paused is True
        # Manually backdate pause
        enforcer.state.pause_until = datetime.now() - timedelta(minutes=1)
        state2 = enforcer.check_state()
        assert state2.is_paused is False

    def test_revenge_emotion_size_reduction(self):
        enforcer = PsychologicalEnforcer()
        state = enforcer.check_state(pnl=100, emotion="fomo")
        assert state.size_multiplier == 0.5
        assert state.last_emotion == "fomo"

    def test_win_streak_cooldown(self):
        enforcer = PsychologicalEnforcer({
            "win_streak_cooldown": 3,
            "win_streak_multiplier": 0.8,
        })
        enforcer.check_state(pnl=100)
        enforcer.check_state(pnl=100)
        state = enforcer.check_state(pnl=100)
        assert state.consecutive_wins == 3
        assert state.size_multiplier == 0.8

    def test_daily_trade_limit(self):
        enforcer = PsychologicalEnforcer({"max_daily_trades": 2})
        enforcer.check_state(pnl=100)
        enforcer.check_state(pnl=100)
        state = enforcer.check_state(pnl=100)
        assert state.blocked_reason is not None
        assert "Daily trade limit" in state.blocked_reason

    def test_large_loss_shock(self):
        enforcer = PsychologicalEnforcer({"large_loss_threshold": 2.0})
        # Seed some average losses
        enforcer._recent_pnls = [-50, -60, -55]
        state = enforcer.check_state(pnl=-200)  # 4x average loss
        assert state.size_multiplier < 1.0

    def test_manual_pause_resume(self):
        enforcer = PsychologicalEnforcer()
        enforcer.manual_pause(hours=1, reason="Manual review")
        assert enforcer.state.is_paused is True
        enforcer.resume()
        assert enforcer.state.is_paused is False
        assert enforcer.state.consecutive_losses == 0

    def test_daily_reset(self):
        enforcer = PsychologicalEnforcer()
        enforcer.state.daily_trades = 5
        enforcer.state.last_trade_date = "2000-01-01"
        state = enforcer.check_state()
        assert state.daily_trades == 0  # Reset for new day

    def test_get_summary(self):
        enforcer = PsychologicalEnforcer()
        enforcer.check_state(pnl=-100, emotion="calm")
        summary = enforcer.get_summary()
        assert summary["consecutive_losses"] == 1
        assert summary["last_emotion"] == "calm"
        assert "is_paused" in summary
