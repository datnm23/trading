"""Compare base backtest vs enhanced backtest (wiki + psych)."""

import yaml
from loguru import logger

from backtest.engine import BacktestEngine
from backtest.enhanced_engine import EnhancedBacktestEngine
from data.feed import DataFeed
from risk.manager import RiskManager
from strategies.ensemble.regime_ensemble import RegimeEnsembleStrategy

logger.remove()
logger.add(lambda msg: print(msg, end=""), level="INFO")


def load_config():
    with open("config/system.yaml") as f:
        return yaml.safe_load(f)


def run_comparison(symbol="BTC/USDT", timeframe="1d"):
    config = load_config()

    feed = DataFeed()
    df = feed.fetch(symbol, timeframe=timeframe, limit=2000)
    if df.empty:
        raise ValueError("No data")

    # Strategy
    strategy = RegimeEnsembleStrategy(
        params={
            "ema": config["strategies"]["registry"][0]["params"],
            "breakout": config["strategies"]["registry"][1]["params"],
            "grid": {"grid_levels": 5, "lookback_days": 30, "atr_period": 14},
            "regime_lookback": 30,
            "atr_period": 14,
            "wiki_min_alignment": 0.3,
        }
    )

    risk = RiskManager(config["risk"])

    # Base backtest
    print("\n" + "=" * 80)
    print("RUNNING BASE BACKTEST (no wiki, no psych)")
    print("=" * 80)
    base_engine = BacktestEngine(
        initial_capital=config["backtest"]["initial_capital"],
        commission=config["backtest"]["commission"],
        slippage=config["backtest"]["slippage"],
    )
    base_result = base_engine.run(df.copy(), strategy, risk)

    # Reset strategy for second run
    strategy.reset()

    # Enhanced backtest
    print("\n" + "=" * 80)
    print("RUNNING ENHANCED BACKTEST (wiki + psych)")
    print("=" * 80)
    enhanced_engine = EnhancedBacktestEngine(
        initial_capital=config["backtest"]["initial_capital"],
        commission=config["backtest"]["commission"],
        slippage=config["backtest"]["slippage"],
        use_wiki=True,
        use_psych=True,
        wiki_min_align=0.3,
        psych_config=config.get("psychology", {}),
    )
    enhanced_result = enhanced_engine.run(df.copy(), strategy, risk)

    # Print comparison
    print("\n" + "=" * 80)
    print("COMPARISON RESULTS")
    print("=" * 80)
    print(f"{'Metric':<25} {'Base':>12} {'Enhanced':>12} {'Delta':>12}")
    print("-" * 80)

    metrics = [
        ("Total Return", base_result.total_return, enhanced_result.total_return, ".2%"),
        ("Sharpe Ratio", base_result.sharpe, enhanced_result.sharpe, ".2f"),
        ("Max Drawdown", base_result.max_drawdown, enhanced_result.max_drawdown, ".2%"),
        ("Winrate", base_result.winrate, enhanced_result.winrate, ".2%"),
        (
            "Profit Factor",
            base_result.profit_factor,
            enhanced_result.profit_factor,
            ".2f",
        ),
        ("Total Trades", len(base_result.trades), len(enhanced_result.trades), "d"),
    ]

    for name, base_val, enh_val, fmt in metrics:
        delta = enh_val - base_val if isinstance(base_val, (int, float)) else 0
        base_str = format(base_val, fmt)
        enh_str = format(enh_val, fmt)
        delta_str = format(delta, fmt) if isinstance(delta, (int, float)) else "N/A"
        print(f"{name:<25} {base_str:>12} {enh_str:>12} {delta_str:>12}")

    # Wiki stats
    print("-" * 80)
    print(f"{'Wiki Blocked':<25} {'N/A':>12} {enhanced_result.wiki_blocked:>12d}")
    print(f"{'Wiki Downgraded':<25} {'N/A':>12} {enhanced_result.wiki_downgraded:>12d}")
    print(
        f"{'Wiki Avg Alignment':<25} {'N/A':>12} {enhanced_result.wiki_avg_alignment:>12.3f}"
    )
    print(
        f"{'Psych Paused Bars':<25} {'N/A':>12} {enhanced_result.psych_paused_bars:>12d}"
    )
    print(
        f"{'Psych Size Reductions':<25} {'N/A':>12} {enhanced_result.psych_size_reductions:>12d}"
    )
    print("=" * 80)

    return base_result, enhanced_result


if __name__ == "__main__":
    run_comparison()
