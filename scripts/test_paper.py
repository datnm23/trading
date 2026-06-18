"""Paper trading simulation on full dataset to find trading activity."""

# ruff: noqa: E402

import sys

sys.path.insert(0, "/home/datnm/projects/trading")

import yaml
from loguru import logger

logger.remove()
logger.add(lambda msg: print(msg, end=""), level="WARNING")  # Quieter

from data.feed import DataFeed
from execution.live_trading import LiveTradingEngine
from strategies.base import StrategyContext
from strategies.ensemble.regime_ensemble import RegimeEnsembleStrategy

with open("/home/datnm/projects/trading/config/system.yaml") as f:
    config = yaml.safe_load(f)

# Fetch data
feed = DataFeed()
df = feed.fetch("BTC/USDT", timeframe="4h", limit=1000)

print("=" * 80)
print("PAPER TRADING SIMULATION ON FULL DATASET")
print("=" * 80)
print(f"Data: BTC/USDT 4h | {len(df)} bars")

strategy = RegimeEnsembleStrategy(params=config["strategies"]["registry"][2]["params"])

engine = LiveTradingEngine(
    config=config,
    strategy=strategy,
    mode="paper",
    symbols=["BTC/USDT"],
)

# Warmup
strategy.warmup(df.iloc[:100])

print(f"\nProcessing all {len(df)} bars...")

trades_executed = 0
wiki_blocked = 0
wiki_downgraded = 0
psych_pauses = 0

for i in range(100, len(df)):
    bar = df.iloc[i]

    context = StrategyContext(
        symbol="BTC/USDT",
        bar=bar,
        history=df.iloc[: i + 1],
        account={"capital": engine.capital, "equity": engine.equity},
        positions=list(engine.positions.values()),
    )

    # Risk check
    status = engine.risk.check(
        engine.capital, engine.equity, list(engine.positions.values())
    )
    if status["halted"]:
        print("\n🛑 DRAWDOWN HALT TRIGGERED")
        break

    # Psych check
    psych_state = engine.psych_enforcer.check_state()
    if psych_state.is_paused:
        psych_pauses += 1
        continue

    # Get signal
    signal = strategy.on_bar(context)
    if signal:
        # Wiki validation
        result = strategy.wiki_validator.validate(
            signal, regime=strategy.current_regime
        )

        if result.block_reason:
            wiki_blocked += 1
            continue

        if result.adjusted_strength < signal.strength:
            wiki_downgraded += 1

        # Execute
        engine._execute_signal("BTC/USDT", signal, bar, psych_state)
        trades_executed += 1

        # Update equity
        engine._update_equity("BTC/USDT", bar)

print("\n" + "=" * 80)
print("SIMULATION COMPLETE")
print("=" * 80)
print(f"Total bars processed: {len(df) - 100}")
print(f"Trades executed: {trades_executed}")
print(f"Wiki blocked: {wiki_blocked}")
print(f"Wiki downgraded: {wiki_downgraded}")
print(f"Psych pauses: {psych_pauses}")
print(f"Final equity: ${engine.equity:,.2f}")
print(f"Total return: {(engine.equity / 100000) - 1:.2%}")
print(f"Open positions: {len(engine.positions)}")

# Get trade summary from journal
summary = engine.journal.trade_summary()
if summary.get("count", 0) > 0:
    print("\nJournal Summary:")
    print(f"  Trades logged: {summary['count']}")
    print(f"  Total P&L: ${summary['total_pnl']:,.2f}")
    print(f"  Winrate: {summary['winrate']:.1%}")
    print(f"  Profit factor: {summary['profit_factor']:.2f}")

psych = engine.psych_enforcer.get_summary()
print("\nFinal Psych State:")
print(f"  Consecutive losses: {psych['consecutive_losses']}")
print(f"  Size multiplier: {psych['size_multiplier']:.0%}")
print(f"  Daily trades: {psych['daily_trades']}")
print(f"  Is paused: {psych['is_paused']}")
print("=" * 80)
