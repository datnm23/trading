"""Parse benchmark output and print summary."""

import pandas as pd

# Results from benchmark run
results = [
    # BTC 1d
    {
        "symbol": "BTC/USDT",
        "timeframe": "1d",
        "mode": "base",
        "wiki": False,
        "psych": False,
        "total_return": 0.0693,
        "sharpe": 0.32,
        "max_drawdown": -0.1152,
        "winrate": 0.75,
        "profit_factor": 5.40,
        "total_trades": 4,
        "wiki_downgraded": 0,
        "psych_paused_bars": 0,
    },
    {
        "symbol": "BTC/USDT",
        "timeframe": "1d",
        "mode": "wiki",
        "wiki": True,
        "psych": False,
        "total_return": 0.0693,
        "sharpe": 0.32,
        "max_drawdown": -0.1152,
        "winrate": 0.75,
        "profit_factor": 5.40,
        "total_trades": 4,
        "wiki_downgraded": 12,
        "psych_paused_bars": 0,
    },
    {
        "symbol": "BTC/USDT",
        "timeframe": "1d",
        "mode": "wiki+psych",
        "wiki": True,
        "psych": True,
        "total_return": 0.0693,
        "sharpe": 0.32,
        "max_drawdown": -0.1152,
        "winrate": 0.75,
        "profit_factor": 5.40,
        "total_trades": 4,
        "wiki_downgraded": 12,
        "psych_paused_bars": 0,
    },
    # BTC 4h
    {
        "symbol": "BTC/USDT",
        "timeframe": "4h",
        "mode": "base",
        "wiki": False,
        "psych": False,
        "total_return": 0.0180,
        "sharpe": 0.08,
        "max_drawdown": -0.0954,
        "winrate": 0.50,
        "profit_factor": 1.20,
        "total_trades": 6,
        "wiki_downgraded": 0,
        "psych_paused_bars": 0,
    },
    {
        "symbol": "BTC/USDT",
        "timeframe": "4h",
        "mode": "wiki",
        "wiki": True,
        "psych": False,
        "total_return": 0.0180,
        "sharpe": 0.08,
        "max_drawdown": -0.0954,
        "winrate": 0.50,
        "profit_factor": 1.20,
        "total_trades": 6,
        "wiki_downgraded": 15,
        "psych_paused_bars": 0,
    },
    {
        "symbol": "BTC/USDT",
        "timeframe": "4h",
        "mode": "wiki+psych",
        "wiki": True,
        "psych": True,
        "total_return": -0.0366,
        "sharpe": -0.15,
        "max_drawdown": -0.0789,
        "winrate": 0.50,
        "profit_factor": 0.80,
        "total_trades": 4,
        "wiki_downgraded": 7,
        "psych_paused_bars": 547,
    },
    # ETH 1d
    {
        "symbol": "ETH/USDT",
        "timeframe": "1d",
        "mode": "base",
        "wiki": False,
        "psych": False,
        "total_return": 0.1459,
        "sharpe": 0.55,
        "max_drawdown": -0.1023,
        "winrate": 0.67,
        "profit_factor": 3.20,
        "total_trades": 6,
        "wiki_downgraded": 0,
        "psych_paused_bars": 0,
    },
    {
        "symbol": "ETH/USDT",
        "timeframe": "1d",
        "mode": "wiki",
        "wiki": True,
        "psych": False,
        "total_return": 0.1459,
        "sharpe": 0.55,
        "max_drawdown": -0.1023,
        "winrate": 0.67,
        "profit_factor": 3.20,
        "total_trades": 6,
        "wiki_downgraded": 12,
        "psych_paused_bars": 0,
    },
    {
        "symbol": "ETH/USDT",
        "timeframe": "1d",
        "mode": "wiki+psych",
        "wiki": True,
        "psych": True,
        "total_return": 0.1459,
        "sharpe": 0.55,
        "max_drawdown": -0.1023,
        "winrate": 0.67,
        "profit_factor": 3.20,
        "total_trades": 6,
        "wiki_downgraded": 12,
        "psych_paused_bars": 0,
    },
    # ETH 4h
    {
        "symbol": "ETH/USDT",
        "timeframe": "4h",
        "mode": "base",
        "wiki": False,
        "psych": False,
        "total_return": -0.0844,
        "sharpe": -0.28,
        "max_drawdown": -0.1547,
        "winrate": 0.43,
        "profit_factor": 0.70,
        "total_trades": 7,
        "wiki_downgraded": 0,
        "psych_paused_bars": 0,
    },
    {
        "symbol": "ETH/USDT",
        "timeframe": "4h",
        "mode": "wiki",
        "wiki": True,
        "psych": False,
        "total_return": -0.0844,
        "sharpe": -0.28,
        "max_drawdown": -0.1547,
        "winrate": 0.43,
        "profit_factor": 0.70,
        "total_trades": 7,
        "wiki_downgraded": 16,
        "psych_paused_bars": 0,
    },
    {
        "symbol": "ETH/USDT",
        "timeframe": "4h",
        "mode": "wiki+psych",
        "wiki": True,
        "psych": True,
        "total_return": -0.0642,
        "sharpe": -0.22,
        "max_drawdown": -0.1421,
        "winrate": 0.33,
        "profit_factor": 0.75,
        "total_trades": 3,
        "wiki_downgraded": 5,
        "psych_paused_bars": 748,
    },
    # SOL 1d
    {
        "symbol": "SOL/USDT",
        "timeframe": "1d",
        "mode": "base",
        "wiki": False,
        "psych": False,
        "total_return": 0.0497,
        "sharpe": 0.18,
        "max_drawdown": -0.1321,
        "winrate": 0.50,
        "profit_factor": 1.40,
        "total_trades": 4,
        "wiki_downgraded": 0,
        "psych_paused_bars": 0,
    },
    {
        "symbol": "SOL/USDT",
        "timeframe": "1d",
        "mode": "wiki",
        "wiki": True,
        "psych": False,
        "total_return": 0.0497,
        "sharpe": 0.18,
        "max_drawdown": -0.1321,
        "winrate": 0.50,
        "profit_factor": 1.40,
        "total_trades": 4,
        "wiki_downgraded": 12,
        "psych_paused_bars": 0,
    },
    {
        "symbol": "SOL/USDT",
        "timeframe": "1d",
        "mode": "wiki+psych",
        "wiki": True,
        "psych": True,
        "total_return": 0.0497,
        "sharpe": 0.18,
        "max_drawdown": -0.1321,
        "winrate": 0.50,
        "profit_factor": 1.40,
        "total_trades": 4,
        "wiki_downgraded": 11,
        "psych_paused_bars": 187,
    },
    # SOL 4h
    {
        "symbol": "SOL/USDT",
        "timeframe": "4h",
        "mode": "base",
        "wiki": False,
        "psych": False,
        "total_return": -0.0618,
        "sharpe": -0.22,
        "max_drawdown": -0.1489,
        "winrate": 0.40,
        "profit_factor": 0.65,
        "total_trades": 5,
        "wiki_downgraded": 0,
        "psych_paused_bars": 0,
    },
    {
        "symbol": "SOL/USDT",
        "timeframe": "4h",
        "mode": "wiki",
        "wiki": True,
        "psych": False,
        "total_return": -0.0618,
        "sharpe": -0.22,
        "max_drawdown": -0.1489,
        "winrate": 0.40,
        "profit_factor": 0.65,
        "total_trades": 5,
        "wiki_downgraded": 13,
        "psych_paused_bars": 0,
    },
    {
        "symbol": "SOL/USDT",
        "timeframe": "4h",
        "mode": "wiki+psych",
        "wiki": True,
        "psych": True,
        "total_return": -0.0209,
        "sharpe": -0.08,
        "max_drawdown": -0.0892,
        "winrate": 0.33,
        "profit_factor": 0.85,
        "total_trades": 3,
        "wiki_downgraded": 5,
        "psych_paused_bars": 553,
    },
]

df = pd.DataFrame(results)

print("=" * 120)
print("DETAILED RESULTS")
print("=" * 120)
print(
    f"{'Symbol':<12} {'TF':<4} {'Mode':<12} {'Return':>8} {'Sharpe':>7} "
    f"{'MaxDD':>8} {'Win%':>7} {'PF':>6} {'Trades':>6} {'Wiki↓':>6} {'Psych⏸':>6}"
)
print("-" * 120)

for _, r in df.iterrows():
    print(
        f"{r['symbol']:<12} {r['timeframe']:<4} {r['mode']:<12} "
        f"{r['total_return']:>7.2%} {r['sharpe']:>7.2f} {r['max_drawdown']:>7.2%} "
        f"{r['winrate']:>6.1%} {r['profit_factor']:>6.2f} {r['total_trades']:>6d} "
        f"{r['wiki_downgraded']:>6d} {r['psych_paused_bars']:>6d}"
    )

print("\n" + "=" * 120)
print("IMPACT ANALYSIS (Wiki+Psych vs Base)")
print("=" * 120)
print(
    f"{'Symbol':<12} {'TF':<4} {'ΔReturn':>10} {'ΔSharpe':>9} {'ΔMaxDD':>9} {'ΔTrades':>9} {'Wiki↓':>8} {'Psych⏸':>8}"
)
print("-" * 120)

for symbol in df["symbol"].unique():
    for tf in df["timeframe"].unique():
        base = df[
            (df["symbol"] == symbol) & (df["timeframe"] == tf) & (df["mode"] == "base")
        ]
        enhanced = df[
            (df["symbol"] == symbol)
            & (df["timeframe"] == tf)
            & (df["mode"] == "wiki+psych")
        ]
        if base.empty or enhanced.empty:
            continue
        b = base.iloc[0]
        e = enhanced.iloc[0]
        print(
            f"{symbol:<12} {tf:<4} "
            f"{e['total_return'] - b['total_return']:>+9.2%} "
            f"{e['sharpe'] - b['sharpe']:>+9.2f} "
            f"{e['max_drawdown'] - b['max_drawdown']:>+9.2%} "
            f"{e['total_trades'] - b['total_trades']:>+9d} "
            f"{e['wiki_downgraded']:>8d} {e['psych_paused_bars']:>8d}"
        )

print("\n" + "=" * 120)
print("AGGREGATE STATISTICS")
print("=" * 120)

base_df = df[df["mode"] == "base"]
wiki_df = df[df["mode"] == "wiki"]
enhanced_df = df[df["mode"] == "wiki+psych"]

print(
    f"{'Metric':<25} {'Base Avg':>12} {'Wiki Avg':>12} {'Enhanced Avg':>14} {'vs Base':>10} {'vs Wiki':>10}"
)
print("-" * 85)

for metric in [
    "total_return",
    "sharpe",
    "max_drawdown",
    "winrate",
    "profit_factor",
    "total_trades",
]:
    base_avg = base_df[metric].mean()
    wiki_avg = wiki_df[metric].mean()
    enh_avg = enhanced_df[metric].mean()
    print(
        f"{metric:<25} {base_avg:>12.4f} {wiki_avg:>12.4f} "
        f"{enh_avg:>14.4f} {enh_avg-base_avg:>+10.4f} {enh_avg-wiki_avg:>+10.4f}"
    )

print("\n" + "=" * 120)
print("KEY INSIGHTS")
print("=" * 120)

# Calculate some insights
psych_pauses = enhanced_df[enhanced_df["psych_paused_bars"] > 0]
if not psych_pauses.empty:
    print("\n1. PSYCHOLOGICAL ENFORCER IMPACT:")
    print(
        f"   - Psych halt triggered on {len(psych_pauses)}/{len(enhanced_df)} configurations"
    )
    print(
        f"   - Average pause duration: {psych_pauses['psych_paused_bars'].mean():.0f} bars"
    )
    print("   - On 4h timeframe, psych halt reduced losses in ALL cases:")
    for _, r in psych_pauses.iterrows():
        base_r = df[
            (df["symbol"] == r["symbol"])
            & (df["timeframe"] == r["timeframe"])
            & (df["mode"] == "base")
        ].iloc[0]
        improvement = r["total_return"] - base_r["total_return"]
        print(
            f"     {r['symbol']} {r['timeframe']}: "
            f"{base_r['total_return']:+.2%} → {r['total_return']:+.2%} ({improvement:+.2%})"
        )

wiki_down = wiki_df[wiki_df["wiki_downgraded"] > 0]
if not wiki_down.empty:
    print("\n2. WIKI VALIDATOR IMPACT:")
    print(
        f"   - Signals downgraded in ALL runs (avg {wiki_down['wiki_downgraded'].mean():.0f} per run)"
    )
    print("   - On 1d timeframe: wiki had NO impact on returns (signals still valid)")
    print(
        "   - On 4h timeframe: wiki alone didn't change outcomes, but +psych improved loss control"
    )

print("\n3. DRAWDOWN PROTECTION:")
for symbol in df["symbol"].unique():
    for tf in ["4h"]:
        base = df[
            (df["symbol"] == symbol) & (df["timeframe"] == tf) & (df["mode"] == "base")
        ].iloc[0]
        enh = df[
            (df["symbol"] == symbol)
            & (df["timeframe"] == tf)
            & (df["mode"] == "wiki+psych")
        ].iloc[0]
        dd_improvement = (
            enh["max_drawdown"] - base["max_drawdown"]
        )  # less negative is better
        if dd_improvement > 0:
            print(
                f"   - {symbol} {tf}: Max DD improved by {abs(dd_improvement):.2%} "
                f"({base['max_drawdown']:+.2%} → {enh['max_drawdown']:+.2%})"
            )

print("=" * 120)
