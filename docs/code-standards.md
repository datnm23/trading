# Code Standards

## Ngôn ngữ và Style

- **Python 3.11+** với type hints
- **ruff** cho linting và formatting (line-length: 100)
- Docstrings cho classes và public methods
- Comments tiếng Việt hoặc tiếng Anh — nhất quán trong cùng file

## Naming Conventions

| Type | Convention | Example |
|------|-----------|---------|
| Classes | PascalCase | `BacktestEngine`, `RiskManager` |
| Functions/Methods | snake_case | `on_bar`, `check_stops` |
| Variables | snake_case | `max_drawdown`, `position_size` |
| Constants | UPPER_SNAKE_CASE | `COOLDOWN_BARS`, `MAX_RETRIES` |
| Private methods | _leading_underscore | `_check_stops`, `_update_equity` |
| Modules | snake_case | `order_manager.py`, `trade_logger.py` |
| Test files | test_*.py | `test_risk.py`, `test_execution.py` |

## Type Hints

- Bắt buộc type hints cho function signatures
- Sử dụng `Optional`, `List`, `Dict` từ `typing`
- Return type phải rõ ràng

```python
from typing import Optional, List, Dict

def on_bar(self, context: StrategyContext) -> Optional[Signal]:
    ...
```

## Error Handling

- **Không bao giờ swallow exceptions** không có logging
- Sử dụng `loguru` cho logging
- Fail-safe: mọi lỗi phải log và dừng an toàn

```python
from loguru import logger

try:
    result = risky_operation()
except Exception as e:
    logger.error(f"Risky operation failed: {e}")
    # Handle gracefully — don't crash the bot
    return None
```

## Thread Safety

- Shared mutable state **PHẢI** được bảo vệ bởi `threading.Lock()`
- Lock scope nên nhỏ gọn (không lock trong I/O blocking)

```python
import threading

class MyEngine:
    def __init__(self):
        self._lock = threading.Lock()
        self._state = {}

    def update_state(self, key, value):
        with self._lock:
            self._state[key] = value
```

## Config-Driven Design

- Behavior thay đổi qua YAML config, không đụng code
- Default values trong config, override qua CLI args

```python
# config/system.yaml
risk:
  max_risk_per_trade: 0.01
  max_total_exposure: 0.10

# Code
def __init__(self, config: dict):
    risk_cfg = config.get("risk", {})
    self.max_risk = risk_cfg.get("max_risk_per_trade", 0.01)
```

## Testing

- **Bắt buộc unit test** cho mọi strategy, risk rule, và execution component
- Sử dụng `pytest` và `pytest-asyncio` cho async tests
- Test names phải mô tả rõ behavior

```python
def test_drawdown_guard_triggers_at_threshold():
    guard = DrawdownGuard(max_drawdown_pct=0.10)
    assert guard.update(100000) is False
    assert guard.update(89000) is True
```

## Imports

- Import theo thứ tự: stdlib → third-party → local
- Sử dụng absolute imports cho local modules

```python
# Standard library
import json
from dataclasses import dataclass

# Third-party
import pandas as pd
from loguru import logger

# Local
from strategies.base import BaseStrategy
from risk.manager import RiskManager
```

## Data Classes

- Sử dụng `@dataclass` cho data containers
- Có `__repr__` hoặc `to_dict()` nếu cần serialize

```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class TradeRecord:
    symbol: str
    side: str
    entry_price: float
    exit_price: Optional[float] = None
    pnl: float = 0.0
```

## Magic Numbers

- **Không dùng magic numbers** — định nghĩa constants

```python
# Bad
if self.bars_since_last_trade < 48:
    return None

# Good
COOLDOWN_BARS = 48
if self.bars_since_last_trade < COOLDOWN_BARS:
    return None
```

## File Organization

- Mỗi module nên < 300 lines
- Nếu vượt 300 lines, xem xét tách thành submodules
- Tests nên ở `tests/` mirror structure của source

## Documentation

- Mỗi module phải có module docstring
- Public classes và methods phải có docstrings
- `docs/` cập nhật khi architecture thay đổi

## Security

- **Không bao giờ hardcode API keys** — dùng env vars hoặc config
- `.env` phải được gitignore
- Kiểm tra input validation cho tất cả user-facing endpoints

## Performance

- Tránh global random seed pollution (dùng `np.random.default_rng()`)
- Cache data fetch khi có thể
- Lock scope nhỏ gọn để tránh contention

## Common Pitfalls (đã gặp và fix)

1. **Missing stop-check**: `_check_stops()` phải được gọi trong vòng lặp chính, không chỉ khi có signal
2. **Duplicate code**: Review unreachable code sau `return` statements
3. **Null guard**: Luôn kiểm tra `None` trước khi `.get()` trên dict có thể là None
4. **Division by zero**: Kiểm tra denominator > 0 trước khi chia
5. **Double counting costs**: `total_return` đã include costs — không cộng thêm
