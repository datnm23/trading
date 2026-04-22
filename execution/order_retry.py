"""Order Retry Manager — Exponential backoff retry for failed orders."""

import time
from dataclasses import dataclass
from typing import Callable, Optional, Any
from loguru import logger


@dataclass
class RetryConfig:
    max_retries: int = 3
    base_delay: float = 1.0       # seconds
    max_delay: float = 30.0       # seconds
    exponential_base: float = 2.0
    retryable_exceptions: tuple = (Exception,)  # override with specific exceptions


class OrderRetryManager:
    """Wraps order submission with exponential backoff retry.

    Usage:
        retry = OrderRetryManager()
        result = retry.execute(
            func=order_manager.submit,
            order=order,
            last_price=price,
        )
    """

    def __init__(self, config: Optional[RetryConfig] = None):
        self.config = config or RetryConfig()
        self.stats = {"total_attempts": 0, "successes": 0, "failures": 0}

    def execute(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with retry logic."""
        last_exception = None

        for attempt in range(self.config.max_retries + 1):
            self.stats["total_attempts"] += 1
            try:
                result = func(*args, **kwargs)
                if attempt > 0:
                    logger.info(f"✅ Order succeeded on attempt {attempt + 1}/{self.config.max_retries + 1}")
                self.stats["successes"] += 1
                return result
            except self.config.retryable_exceptions as e:
                last_exception = e
                if attempt < self.config.max_retries:
                    delay = min(
                        self.config.base_delay * (self.config.exponential_base ** attempt),
                        self.config.max_delay,
                    )
                    logger.warning(
                        f"⚠️  Order attempt {attempt + 1} failed: {e} | Retrying in {delay:.1f}s..."
                    )
                    time.sleep(delay)
                else:
                    logger.error(f"❌ Order failed after {self.config.max_retries + 1} attempts: {e}")

        self.stats["failures"] += 1
        raise last_exception

    def get_stats(self) -> dict:
        """Return retry statistics."""
        return self.stats.copy()
