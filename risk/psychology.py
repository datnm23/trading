"""Psychological risk enforcer: automated discipline based on trading psychology.

Concepts applied:
    - ky_luat_trading (trading discipline)
    - tam_ly_bam_viu_hy_vong (don't hope, follow rules)
    - ngua_ngon_cai_hang (overconfidence after wins)
    - overtrading (too many trades)
    - cat_lo_khi_sai (cut losses quickly — emotional override)

Features:
    - Auto-pause after N consecutive losses
    - Reduce position size on "revenge" / "fomo" emotions
    - Daily trade limit to prevent overtrading
    - Win-streak cooldown (reduce size after big wins to avoid overconfidence)
    - Mandatory cooldown after large losses (> 2x avg loss)
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, List

from loguru import logger


@dataclass
class PsychologicalState:
    """Current psychological state of the trading system."""
    consecutive_losses: int = 0
    consecutive_wins: int = 0
    daily_trades: int = 0
    last_trade_date: str = ""
    last_emotion: Optional[str] = None
    total_pnl_today: float = 0.0
    largest_loss_today: float = 0.0
    is_paused: bool = False
    pause_until: Optional[datetime] = None
    size_multiplier: float = 1.0
    blocked_reason: Optional[str] = None


class PsychologicalEnforcer:
    """Enforce psychological discipline rules automatically.

    Usage:
        enforcer = PsychologicalEnforcer()
        # Before each trade
        state = enforcer.check_state(trade_record)
        if state.is_paused:
            # Skip trade
        position_size *= state.size_multiplier
    """

    def __init__(self, config: Optional[dict] = None):
        cfg = config or {}
        self.max_consecutive_losses = cfg.get("max_consecutive_losses", 3)
        self.pause_after_losses_hours = cfg.get("pause_after_losses_hours", 24)
        self.max_daily_trades = cfg.get("max_daily_trades", 10)
        self.revenge_emotions = set(cfg.get("revenge_emotions", ["revenge", "fomo", "panic", "angry"]))
        self.revenge_size_multiplier = cfg.get("revenge_size_multiplier", 0.5)
        self.win_streak_cooldown = cfg.get("win_streak_cooldown", 5)
        self.win_streak_multiplier = cfg.get("win_streak_multiplier", 0.8)
        self.large_loss_threshold = cfg.get("large_loss_threshold", 2.0)  # x avg loss
        self.large_loss_cooldown_hours = cfg.get("large_loss_cooldown_hours", 12)

        self.state = PsychologicalState()
        self._recent_pnls: List[float] = []
        self._max_recent = 50

    def check_state(self, pnl: float = 0.0, emotion: Optional[str] = None) -> PsychologicalState:
        """Update state with latest trade info and return current enforcement.

        Args:
            pnl: P&L of the most recent closed trade (0 before first trade)
            emotion: Emotion tag from journal (e.g. 'calm', 'fomo', 'revenge')
        """
        today = datetime.now().strftime("%Y-%m-%d")

        # Reset daily counters
        if self.state.last_trade_date != today:
            self.state.daily_trades = 0
            self.state.total_pnl_today = 0.0
            self.state.largest_loss_today = 0.0
            self.state.last_trade_date = today

        # Update P&L tracking
        if pnl != 0:
            self._recent_pnls.append(pnl)
            if len(self._recent_pnls) > self._max_recent:
                self._recent_pnls.pop(0)
            self.state.daily_trades += 1
            self.state.total_pnl_today += pnl

            if pnl < 0:
                self.state.consecutive_losses += 1
                self.state.consecutive_wins = 0
                if pnl < self.state.largest_loss_today:
                    self.state.largest_loss_today = pnl
            else:
                self.state.consecutive_wins += 1
                self.state.consecutive_losses = 0

        # Update emotion
        if emotion:
            self.state.last_emotion = emotion

        # Reset pause if expired
        if self.state.is_paused and self.state.pause_until:
            if datetime.now() >= self.state.pause_until:
                self.state.is_paused = False
                self.state.pause_until = None
                self.state.blocked_reason = None
                self.state.consecutive_losses = 0  # Reset after cooling off
                logger.info("Psychological pause expired. Trading resumed.")

        # Apply rules
        self._apply_rules(pnl)

        return self.state

    def _apply_rules(self, last_pnl: float):
        """Apply all psychological rules."""
        self.state.size_multiplier = 1.0
        self.state.blocked_reason = None

        # Rule 1: Pause after N consecutive losses
        if self.state.consecutive_losses >= self.max_consecutive_losses:
            if not self.state.is_paused:
                self.state.is_paused = True
                self.state.pause_until = datetime.now() + timedelta(hours=self.pause_after_losses_hours)
                self.state.blocked_reason = (
                    f"{self.state.consecutive_losses} consecutive losses. "
                    f"Paused until {self.state.pause_until.strftime('%Y-%m-%d %H:%M')}."
                )
                logger.warning(f"🧠 PSYCH HALT: {self.state.blocked_reason}")
            return

        # Rule 2: Daily trade limit (overtrading)
        if self.state.daily_trades >= self.max_daily_trades:
            self.state.blocked_reason = (
                f"Daily trade limit reached ({self.state.daily_trades}/{self.max_daily_trades})."
            )
            logger.warning(f"🧠 PSYCH BLOCK: {self.state.blocked_reason}")
            return

        # Rule 3: Reduce size on negative emotions
        if self.state.last_emotion in self.revenge_emotions:
            self.state.size_multiplier *= self.revenge_size_multiplier
            logger.warning(
                f"🧠 PSYCH ALERT: Emotion '{self.state.last_emotion}' detected. "
                f"Size reduced to {self.state.size_multiplier:.0%}."
            )

        # Rule 4: Win streak cooldown (avoid overconfidence)
        if self.state.consecutive_wins >= self.win_streak_cooldown:
            self.state.size_multiplier *= self.win_streak_multiplier
            logger.info(
                f"🧠 PSYCH COOLDOWN: {self.state.consecutive_wins} consecutive wins. "
                f"Size reduced to {self.state.size_multiplier:.0%} to avoid overconfidence."
            )

        # Rule 5: Large loss cooldown
        if last_pnl < 0 and self._recent_pnls:
            avg_loss = abs(sum(p for p in self._recent_pnls if p < 0) / max(1, sum(1 for p in self._recent_pnls if p < 0)))
            if avg_loss > 0 and abs(last_pnl) > avg_loss * self.large_loss_threshold:
                self.state.size_multiplier *= 0.5
                logger.warning(
                    f"🧠 PSYCH SHOCK: Large loss ${last_pnl:,.2f} (>{self.large_loss_threshold}x avg). "
                    f"Size reduced to {self.state.size_multiplier:.0%}."
                )

    def manual_pause(self, hours: int, reason: str):
        """Manually pause trading (e.g. from external command)."""
        self.state.is_paused = True
        self.state.pause_until = datetime.now() + timedelta(hours=hours)
        self.state.blocked_reason = reason
        logger.info(f"🧠 MANUAL PAUSE: {reason} until {self.state.pause_until}")

    def resume(self):
        """Manually resume trading."""
        self.state.is_paused = False
        self.state.pause_until = None
        self.state.consecutive_losses = 0
        self.state.blocked_reason = None
        logger.info("🧠 MANUAL RESUME: Trading resumed.")

    def get_summary(self) -> dict:
        """Return psychological state summary."""
        return {
            "consecutive_losses": self.state.consecutive_losses,
            "consecutive_wins": self.state.consecutive_wins,
            "daily_trades": self.state.daily_trades,
            "last_emotion": self.state.last_emotion,
            "is_paused": self.state.is_paused,
            "pause_until": self.state.pause_until.isoformat() if self.state.pause_until else None,
            "size_multiplier": self.state.size_multiplier,
            "blocked_reason": self.state.blocked_reason,
            "total_pnl_today": self.state.total_pnl_today,
        }
