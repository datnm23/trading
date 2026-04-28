"""Order manager with validation, retry logic, and partial-fill tracking.

Integrates with CCXTConnector to provide robust order execution
with automatic retries, partial-fill reconciliation, and state tracking.
"""

import json
import time
import uuid
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import StrEnum
from pathlib import Path

from loguru import logger

from execution.connectors.ccxt_connector import CCXTConnector


class OrderStatus(StrEnum):
    """Order lifecycle states."""

    PENDING = "pending"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    FAILED = "failed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class OrderSide(StrEnum):
    BUY = "buy"
    SELL = "sell"


class OrderType(StrEnum):
    MARKET = "market"
    LIMIT = "limit"


@dataclass
class Order:
    """Represents a single order with full lifecycle tracking."""

    id: str
    symbol: str
    side: OrderSide
    order_type: OrderType
    amount: float
    price: float | None = None
    status: OrderStatus = OrderStatus.PENDING
    filled: float = 0.0
    remaining: float = 0.0
    average_price: float | None = None
    fee: float = 0.0
    error_message: str | None = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    raw_response: dict | None = field(default=None, repr=False)
    strategy_name: str | None = None
    reason: str | None = None

    def to_dict(self) -> dict:
        d = asdict(self)
        d["side"] = self.side.value
        d["order_type"] = self.order_type.value
        d["status"] = self.status.value
        d["created_at"] = self.created_at.isoformat()
        d["updated_at"] = self.updated_at.isoformat()
        return d


@dataclass
class OrderResult:
    """Result of an order submission attempt."""

    success: bool
    order: Order | None = None
    error: str | None = None
    retries: int = 0


class OrderValidator:
    """Validates orders before submission to exchange."""

    def __init__(
        self,
        min_order_size: float = 10.0,  # minimum notional in quote currency
        max_order_size: float | None = None,
        price_precision: int = 8,
        amount_precision: int = 8,
        max_slippage_pct: float = 0.02,
    ):
        self.min_order_size = min_order_size
        self.max_order_size = max_order_size
        self.price_precision = price_precision
        self.amount_precision = amount_precision
        self.max_slippage_pct = max_slippage_pct

    def validate(self, order: Order, last_price: float | None = None) -> str | None:
        """Return error message if invalid, None if valid."""
        if not order.symbol or "/" not in order.symbol:
            return f"Invalid symbol format: {order.symbol}"

        if order.amount <= 0:
            return f"Amount must be > 0, got {order.amount}"

        if order.order_type == OrderType.LIMIT and (
            order.price is None or order.price <= 0
        ):
            return "Limit order requires valid price"

        notional = order.amount * (order.price or last_price or 0)
        if notional < self.min_order_size:
            return (
                f"Order notional ${notional:.2f} below minimum ${self.min_order_size}"
            )

        if self.max_order_size and notional > self.max_order_size:
            return (
                f"Order notional ${notional:.2f} exceeds maximum ${self.max_order_size}"
            )

        if last_price and order.price:
            slippage = abs(order.price - last_price) / last_price
            if slippage > self.max_slippage_pct:
                return f"Price slippage {slippage:.2%} exceeds max {self.max_slippage_pct:.2%}"

        return None


class OrderManager:
    """Manages order lifecycle: validate → submit → retry → reconcile.

    Features:
        - Pre-submission validation (size, price, symbol)
        - Exponential backoff retry on transient failures
        - Partial-fill tracking and automatic reconciliation
        - Order state persistence (JSONL log)
        - Paper mode for simulation without real orders
    """

    def __init__(
        self,
        connector: CCXTConnector | None = None,
        validator: OrderValidator | None = None,
        paper_mode: bool = False,
        max_retries: int = 3,
        retry_base_delay: float = 1.0,
        retry_max_delay: float = 30.0,
        retry_backoff_multiplier: float = 2.0,
        persist_path: str | None = "./data/orders.jsonl",
    ):
        self.connector = connector
        self.validator = validator or OrderValidator()
        self.paper_mode = paper_mode
        self.max_retries = max_retries
        self.retry_base_delay = retry_base_delay
        self.retry_max_delay = retry_max_delay
        self.retry_backoff_multiplier = retry_backoff_multiplier
        self.persist_path = Path(persist_path) if persist_path else None

        self.orders: dict[str, Order] = {}
        self._order_counter = 0
        self._callbacks: list[Callable[[Order], None]] = []

        if self.persist_path:
            self.persist_path.parent.mkdir(parents=True, exist_ok=True)

    def register_callback(self, callback: Callable[[Order], None]):
        """Register a callback invoked on every order status change."""
        self._callbacks.append(callback)

    def _generate_id(self) -> str:
        return f"ord_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"

    def _notify(self, order: Order):
        for cb in self._callbacks:
            try:
                cb(order)
            except Exception as e:
                logger.warning(f"Order callback error: {e}")

    def _persist(self, order: Order):
        if not self.persist_path:
            return
        try:
            with open(self.persist_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(order.to_dict(), ensure_ascii=False) + "\n")
        except Exception as e:
            logger.warning(f"Failed to persist order: {e}")

    def create_order(
        self,
        symbol: str,
        side: OrderSide,
        amount: float,
        order_type: OrderType = OrderType.MARKET,
        price: float | None = None,
        strategy_name: str | None = None,
        reason: str | None = None,
    ) -> Order:
        """Create an Order object (not yet submitted)."""
        return Order(
            id=self._generate_id(),
            symbol=symbol,
            side=side,
            order_type=order_type,
            amount=amount,
            price=price,
            remaining=amount,
            strategy_name=strategy_name,
            reason=reason,
        )

    def submit(
        self,
        order: Order,
        last_price: float | None = None,
    ) -> OrderResult:
        """Validate and submit order to exchange (or simulate in paper mode).

        Returns OrderResult with success status and updated order object.
        """
        # Validate
        error = self.validator.validate(order, last_price=last_price)
        if error:
            order.status = OrderStatus.FAILED
            order.error_message = error
            order.updated_at = datetime.now()
            logger.error(f"Order validation failed [{order.id}]: {error}")
            self._persist(order)
            self._notify(order)
            return OrderResult(success=False, order=order, error=error)

        # Execute with retries
        if self.paper_mode:
            result = self._execute_paper(order, last_price)
        else:
            result = self._execute_live_with_retry(order)

        self.orders[order.id] = order
        self._persist(order)
        self._notify(order)
        return result

    def _execute_paper(self, order: Order, last_price: float | None) -> OrderResult:
        """Simulate immediate fill in paper mode."""
        fill_price = order.price or last_price or 0.0
        if fill_price <= 0:
            order.status = OrderStatus.FAILED
            order.error_message = "No price available for paper fill"
            order.updated_at = datetime.now()
            return OrderResult(success=False, order=order, error=order.error_message)

        order.filled = order.amount
        order.remaining = 0.0
        order.average_price = fill_price
        order.status = OrderStatus.FILLED
        order.updated_at = datetime.now()
        logger.info(
            f"Paper fill | {order.side.value.upper()} {order.amount} {order.symbol} "
            f"@ {fill_price:.4f} | id={order.id}"
        )
        return OrderResult(success=True, order=order)

    def _execute_live_with_retry(self, order: Order) -> OrderResult:
        """Submit to exchange with exponential backoff retry."""
        retries = 0
        last_error = None

        while retries <= self.max_retries:
            try:
                result = self._submit_to_exchange(order)
                if result.success:
                    result.retries = retries
                    return result
                # If exchange returned failure but no exception, check if retryable
                if result.error and self._is_retryable_error(result.error):
                    last_error = result.error
                else:
                    return result
            except Exception as e:
                last_error = str(e)
                if not self._is_retryable_error(last_error):
                    break
                logger.warning(f"Order attempt {retries + 1} failed: {e}")

            retries += 1
            if retries <= self.max_retries:
                delay = min(
                    self.retry_base_delay
                    * (self.retry_backoff_multiplier ** (retries - 1)),
                    self.retry_max_delay,
                )
                logger.info(
                    f"Retrying order in {delay:.1f}s... (attempt {retries + 1}/{self.max_retries + 1})"
                )
                time.sleep(delay)

        order.status = OrderStatus.FAILED
        order.error_message = last_error or "Unknown error"
        order.updated_at = datetime.now()
        logger.error(
            f"Order failed after {retries} retries [{order.id}]: {order.error_message}"
        )
        return OrderResult(
            success=False, order=order, error=order.error_message, retries=retries
        )

    def _submit_to_exchange(self, order: Order) -> OrderResult:
        """Low-level exchange submission."""
        if not self.connector:
            return OrderResult(
                success=False, order=order, error="No connector configured"
            )

        raw = self.connector.create_market_order(
            symbol=order.symbol,
            side=order.side.value,
            amount=order.amount,
        )
        if raw is None:
            return OrderResult(
                success=False, order=order, error="Exchange returned None"
            )

        order.raw_response = raw
        order.updated_at = datetime.now()

        # Parse CCXT response
        filled = raw.get("filled", 0.0) or order.amount
        remaining = raw.get("remaining", 0.0)
        status_str = raw.get("status", "open")
        avg = raw.get("average")

        order.filled = float(filled)
        order.remaining = float(remaining)
        order.average_price = float(avg) if avg else order.price

        if status_str == "closed" or remaining == 0:
            order.status = OrderStatus.FILLED
        elif filled > 0 and remaining > 0:
            order.status = OrderStatus.PARTIALLY_FILLED
        elif status_str == "canceled":
            order.status = OrderStatus.CANCELLED
        else:
            order.status = OrderStatus.PENDING

        # Parse fee if present
        fee_info = raw.get("fee", {})
        if fee_info:
            order.fee = float(fee_info.get("cost", 0.0) or 0.0)

        logger.info(
            f"Exchange response | {order.side.value.upper()} {order.filled}/{order.amount} "
            f"{order.symbol} @ {order.average_price or 'market'} | status={order.status.value}"
        )

        if order.status == OrderStatus.FAILED:
            return OrderResult(success=False, order=order, error=order.error_message)
        return OrderResult(
            success=order.status in (OrderStatus.FILLED, OrderStatus.PARTIALLY_FILLED),
            order=order,
        )

    def _is_retryable_error(self, error: str) -> bool:
        """Determine if an error message warrants a retry."""
        retryable = [
            "timeout",
            "network",
            "connection",
            "temporarily",
            "rate limit",
            "too many requests",
            "econnreset",
            "econnrefused",
            "gateway",
            "503",
            "502",
            "504",
        ]
        err_lower = error.lower()
        return any(keyword in err_lower for keyword in retryable)

    def reconcile(self, order_id: str) -> Order | None:
        """Fetch latest order status from exchange and update local record.

        Useful for recovering state after restart or tracking partial fills.
        """
        order = self.orders.get(order_id)
        if not order or not self.connector or not self.connector.exchange:
            return order

        try:
            raw = self.connector.exchange.fetch_order(order_id, order.symbol)
            if raw:
                order.filled = float(raw.get("filled", order.filled))
                order.remaining = float(raw.get("remaining", order.remaining))
                order.average_price = (
                    float(raw.get("average", order.average_price or 0))
                    or order.average_price
                )
                order.status = self._map_status(raw.get("status", "open"))
                order.updated_at = datetime.now()
                self._persist(order)
                self._notify(order)
        except Exception as e:
            logger.warning(f"Reconcile failed for {order_id}: {e}")

        return order

    def _map_status(self, exchange_status: str) -> OrderStatus:
        mapping = {
            "open": OrderStatus.PENDING,
            "closed": OrderStatus.FILLED,
            "canceled": OrderStatus.CANCELLED,
            "cancelled": OrderStatus.CANCELLED,
            "expired": OrderStatus.EXPIRED,
            "rejected": OrderStatus.FAILED,
        }
        return mapping.get(exchange_status.lower(), OrderStatus.PENDING)

    def cancel(self, order_id: str) -> bool:
        """Attempt to cancel a pending order."""
        order = self.orders.get(order_id)
        if not order:
            logger.warning(f"Cancel failed: order {order_id} not found")
            return False
        if order.status not in (OrderStatus.PENDING, OrderStatus.PARTIALLY_FILLED):
            logger.info(
                f"Cancel skipped: order {order_id} already {order.status.value}"
            )
            return False

        if self.paper_mode:
            order.status = OrderStatus.CANCELLED
            order.updated_at = datetime.now()
            self._persist(order)
            self._notify(order)
            return True

        if not self.connector or not self.connector.exchange:
            return False

        try:
            self.connector.exchange.cancel_order(order_id, order.symbol)
            order.status = OrderStatus.CANCELLED
            order.updated_at = datetime.now()
            self._persist(order)
            self._notify(order)
            logger.info(f"Order cancelled: {order_id}")
            return True
        except Exception as e:
            logger.error(f"Cancel failed for {order_id}: {e}")
            return False

    def get_open_orders(self) -> list[Order]:
        """Return all orders not yet fully filled or failed."""
        return [
            o
            for o in self.orders.values()
            if o.status in (OrderStatus.PENDING, OrderStatus.PARTIALLY_FILLED)
        ]

    def get_summary(self) -> dict:
        """Return summary statistics of all orders."""
        total = len(self.orders)
        filled = sum(1 for o in self.orders.values() if o.status == OrderStatus.FILLED)
        partial = sum(
            1 for o in self.orders.values() if o.status == OrderStatus.PARTIALLY_FILLED
        )
        failed = sum(1 for o in self.orders.values() if o.status == OrderStatus.FAILED)
        cancelled = sum(
            1 for o in self.orders.values() if o.status == OrderStatus.CANCELLED
        )
        total_fees = sum(o.fee for o in self.orders.values())

        return {
            "total_orders": total,
            "filled": filled,
            "partially_filled": partial,
            "failed": failed,
            "cancelled": cancelled,
            "total_fees": total_fees,
            "fill_rate": filled / total if total > 0 else 0.0,
        }
