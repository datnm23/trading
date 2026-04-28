"""Tests for execution layer: OrderManager, LiveTradingEngine."""

from execution.order_manager import (
    OrderManager,
    OrderSide,
    OrderStatus,
    OrderType,
    OrderValidator,
)
from monitoring.health_server import HealthServer


class TestOrderValidator:
    def test_valid_market_order(self):
        v = OrderValidator(min_order_size=10.0)
        from execution.order_manager import Order

        order = Order(
            id="test_1",
            symbol="BTC/USDT",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            amount=0.001,
            price=None,
        )
        assert v.validate(order, last_price=65000) is None

    def test_invalid_symbol(self):
        v = OrderValidator()
        from execution.order_manager import Order

        order = Order(
            id="test_2",
            symbol="INVALID",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            amount=0.001,
        )
        err = v.validate(order, last_price=65000)
        assert err is not None
        assert "symbol" in err.lower()

    def test_min_notional(self):
        v = OrderValidator(min_order_size=100.0)
        from execution.order_manager import Order

        order = Order(
            id="test_3",
            symbol="BTC/USDT",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            amount=0.0001,
        )
        err = v.validate(order, last_price=65000)
        assert err is not None
        assert "minimum" in err.lower()

    def test_slippage_limit(self):
        v = OrderValidator(max_slippage_pct=0.01)
        from execution.order_manager import Order

        order = Order(
            id="test_4",
            symbol="BTC/USDT",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            amount=0.001,
            price=70000,
        )
        err = v.validate(order, last_price=65000)
        assert err is not None
        assert "slippage" in err.lower()


class TestOrderManager:
    def test_paper_fill(self):
        om = OrderManager(paper_mode=True)
        order = om.create_order(
            symbol="BTC/USDT",
            side=OrderSide.BUY,
            amount=0.01,
            strategy_name="Test",
            reason="test",
        )
        result = om.submit(order, last_price=65000)
        assert result.success is True
        assert result.order.status == OrderStatus.FILLED
        assert result.order.average_price == 65000

    def test_paper_sell(self):
        om = OrderManager(paper_mode=True)
        order = om.create_order(
            symbol="BTC/USDT",
            side=OrderSide.SELL,
            amount=0.01,
        )
        result = om.submit(order, last_price=66000)
        assert result.success is True
        assert result.order.status == OrderStatus.FILLED

    def test_validation_failure(self):
        om = OrderManager(
            paper_mode=True, validator=OrderValidator(min_order_size=100000)
        )
        order = om.create_order(
            symbol="BTC/USDT",
            side=OrderSide.BUY,
            amount=0.0001,
        )
        result = om.submit(order, last_price=65000)
        assert result.success is False
        assert result.order.status == OrderStatus.FAILED

    def test_order_summary(self):
        om = OrderManager(paper_mode=True)
        for _ in range(3):
            o = om.create_order("BTC/USDT", OrderSide.BUY, 0.01)
            om.submit(o, last_price=65000)
        summary = om.get_summary()
        assert summary["total_orders"] == 3
        assert summary["filled"] == 3
        assert summary["fill_rate"] == 1.0

    def test_callback(self):
        om = OrderManager(paper_mode=True)
        called = []
        om.register_callback(lambda o: called.append(o.id))
        o = om.create_order("BTC/USDT", OrderSide.BUY, 0.01)
        om.submit(o, last_price=65000)
        assert len(called) == 1

    def test_cancel(self):
        om = OrderManager(paper_mode=True)
        o = om.create_order("BTC/USDT", OrderSide.BUY, 0.01)
        # Paper mode fills immediately, so cancel should fail
        result = om.submit(o, last_price=65000)
        assert result.order.status == OrderStatus.FILLED
        assert om.cancel(result.order.id) is False


class TestHealthServer:
    def test_health_endpoint(self):
        server = HealthServer(
            port=18081,
            status_provider=lambda: {"running": True, "equity": 100000},
        )
        server.start()
        import requests

        resp = requests.get("http://localhost:18081/health", timeout=5)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        server.stop()

    def test_metrics_endpoint(self):
        server = HealthServer(
            port=18082,
            status_provider=lambda: {
                "running": True,
                "equity": 100000,
                "capital": 95000,
                "open_positions": 1,
            },
        )
        server.start()
        import requests

        resp = requests.get("http://localhost:18082/metrics", timeout=5)
        assert resp.status_code == 200
        assert "equity 100000" in resp.text
        server.stop()
