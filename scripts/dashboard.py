#!/usr/bin/env python3
"""Streamlit Dashboard for real-time trading performance monitoring.

Connects to PostgreSQL journal DB to display equity curve, trades, and metrics.

Usage:
    streamlit run scripts/dashboard.py

Or with custom port:
    streamlit run scripts/dashboard.py --server.port 8501
"""

import os
import sys
import base64
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from streamlit_autorefresh import st_autorefresh
from journal.trade_logger import TradeLogger


def get_live_prices():
    """Fetch real-time prices from Binance testnet."""
    try:
        from execution.connectors.ccxt_connector import CCXTConnector
        conn = CCXTConnector(exchange_id="binance", testnet=True)
        prices = {}
        for sym in ["BTC/USDT", "ETH/USDT", "SOL/USDT"]:
            ticker = conn.fetch_ticker(sym)
            if ticker:
                prices[sym] = {
                    "last": ticker.get("last", 0),
                    "change": ticker.get("percentage", 0),
                    "high": ticker.get("high", 0),
                    "low": ticker.get("low", 0),
                    "volume": ticker.get("quoteVolume", 0),
                }
        return prices
    except Exception as e:
        return {}


# ── Page config ──────────────────────────────────────────────────────
st.set_page_config(
    page_title="Trading Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ───────────────────────────────────────────────────────
st.markdown("""
<style>
    .metric-card {
        background-color: #1e1e1e;
        border-radius: 10px;
        padding: 20px;
        border: 1px solid #333;
    }
    .positive { color: #00ff88; }
    .negative { color: #ff4757; }
    .neutral { color: #ffa502; }
    div[data-testid="stMetricValue"] { font-size: 28px !important; font-weight: bold; }
</style>
""", unsafe_allow_html=True)


# ── Initialize logger ────────────────────────────────────────────────
@st.cache_resource
def get_logger():
    db_url = os.getenv(
        "TRADING_DB_URL",
        "postgresql://trader:trading123@localhost:5432/trading_journal"
    )
    return TradeLogger(db_url=db_url)


logger = get_logger()


# ── Auto-refresh ─────────────────────────────────────────────────────
refresh_interval = st.sidebar.slider("⏱️ Auto-refresh (seconds)", 5, 60, 10)
st_autorefresh(interval=refresh_interval * 1000, key="auto_refresh")
st.sidebar.caption(f"🔄 Auto-refreshing every **{refresh_interval}s**")


# ── Sidebar ──────────────────────────────────────────────────────────
st.sidebar.title("🚀 Trading Bot")
st.sidebar.markdown("---")

# Bot status
health_url = "http://localhost:8080/health"
try:
    import requests
    resp = requests.get(health_url, timeout=2)
    health = resp.json()
    status_color = "🟢" if health.get("status") == "healthy" else "🔴"
    st.sidebar.markdown(f"**Status:** {status_color} {health.get('status', 'unknown').upper()}")
    st.sidebar.markdown(f"**Mode:** {health.get('data', {}).get('mode', 'unknown').upper()}")
    st.sidebar.markdown(f"**Strategy:** {health.get('data', {}).get('strategy', 'unknown')}")
    symbols = health.get('data', {}).get('symbols', [])
    st.sidebar.markdown(f"**Symbols:** {', '.join(symbols)}")
except Exception:
    st.sidebar.warning("⚠️ Bot health check failed")

st.sidebar.markdown("---")
st.sidebar.info("Dashboard auto-refreshes every page load.\nHit **R** to refresh manually.")

# ── Export Section ───────────────────────────────────────────────────
st.sidebar.markdown("---")
st.sidebar.subheader("📤 Export")

# Get data for export
trades = logger.get_trades(limit=1000)
snapshots = logger.get_snapshots(limit=1000)
summary = logger.trade_summary()

if trades:
    # Export trades CSV
    df_export = pd.DataFrame([
        {
            "timestamp": t.timestamp.isoformat() if isinstance(t.timestamp, datetime) else str(t.timestamp),
            "symbol": t.symbol,
            "strategy": t.strategy,
            "side": t.side,
            "entry_price": t.entry_price,
            "exit_price": t.exit_price,
            "size": t.size,
            "pnl": t.pnl,
            "pnl_pct": t.pnl_pct,
            "holding_bars": t.holding_bars,
            "exit_reason": t.exit_reason,
            "market_regime": t.market_regime,
        }
        for t in trades
    ])
    csv = df_export.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    st.sidebar.download_button(
        label="📄 Download Trades (CSV)",
        data=csv,
        file_name=f"trades_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv",
    )

    # Export summary report as HTML
    report_html = f"""
    <html>
    <head><title>Trading Report</title></head>
    <body style="font-family: Arial, sans-serif; padding: 40px;">
        <h1>Trading Performance Report</h1>
        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <hr>
        <h2>Summary</h2>
        <table border="1" cellpadding="10" style="border-collapse: collapse;">
            <tr><td>Total Trades</td><td>{summary['count']}</td></tr>
            <tr><td>Total P&L</td><td>${summary['total_pnl']:,.2f}</td></tr>
            <tr><td>Winrate</td><td>{summary['winrate']:.1%}</td></tr>
            <tr><td>Profit Factor</td><td>{summary['profit_factor']:.2f}</td></tr>
            <tr><td>Avg Win</td><td>${summary['avg_win']:,.2f}</td></tr>
            <tr><td>Avg Loss</td><td>${summary['avg_loss']:,.2f}</td></tr>
            <tr><td>Max Win</td><td>${summary['max_win']:,.2f}</td></tr>
            <tr><td>Max Loss</td><td>${summary['max_loss']:,.2f}</td></tr>
        </table>
        <h2>Recent Trades</h2>
        {df_export.head(20).to_html(index=False)}
    </body>
    </html>
    """
    st.sidebar.download_button(
        label="📑 Download Report (HTML)",
        data=report_html,
        file_name=f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
        mime="text/html",
    )
else:
    st.sidebar.info("No data to export yet.")

# ── Trade Alert (Toast) ──────────────────────────────────────────────
if "last_trade_count" not in st.session_state:
    st.session_state.last_trade_count = 0

current_trade_count = len(trades)
if current_trade_count > st.session_state.last_trade_count:
    new_count = current_trade_count - st.session_state.last_trade_count
    if new_count == 1 and trades:
        latest = trades[0]
        emoji = "🟢" if latest.pnl > 0 else "🔴" if latest.pnl < 0 else "⚪"
        st.toast(
            f"{emoji} New Trade: {latest.side.upper()} {latest.symbol} "
            f"P&L: ${latest.pnl:,.2f} ({latest.pnl_pct:.2%})",
            icon="🔔",
        )
    else:
        st.toast(f"🔔 {new_count} new trade(s) detected!", icon="📈")

st.session_state.last_trade_count = current_trade_count


# ── Real-Time Price Ticker ───────────────────────────────────────────
st.title("📊 Trading Performance Dashboard")

live_prices = get_live_prices()
if live_prices:
    st.subheader("⚡ Real-Time Prices")
    price_cols = st.columns(len(live_prices))
    for i, (sym, data) in enumerate(live_prices.items()):
        with price_cols[i]:
            change_pct = data["change"] or 0
            emoji = "🟢" if change_pct >= 0 else "🔴"
            st.metric(
                label=f"{sym}",
                value=f"${data['last']:,.2f}",
                delta=f"{change_pct:+.2f}%",
                delta_color="normal" if change_pct >= 0 else "inverse",
            )
            st.caption(
                f"H: ${data['high']:,.2f} | L: ${data['low']:,.2f} | Vol: ${data['volume']:,.0f}"
            )
    st.markdown("---")
else:
    st.warning("⚠️ Real-time prices unavailable — bot may be offline")

# Data already fetched above for sidebar export + alerts

# ── KPI Cards ────────────────────────────────────────────────────────
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    equity = snapshots[0].equity if snapshots else 100000
    initial = 100000
    total_return = (equity - initial) / initial
    delta_color = "normal" if total_return >= 0 else "inverse"
    st.metric(
        label="💰 Equity",
        value=f"${equity:,.2f}",
        delta=f"{total_return:.2%}",
        delta_color=delta_color,
    )

with col2:
    st.metric(
        label="📈 Total P&L",
        value=f"${summary.get('total_pnl', 0):,.2f}",
    )

with col3:
    winrate = summary.get('winrate', 0)
    st.metric(
        label="🏆 Winrate",
        value=f"{winrate:.1%}",
    )

with col4:
    st.metric(
        label="🎯 Profit Factor",
        value=f"{summary.get('profit_factor', 0):.2f}",
    )

with col5:
    st.metric(
        label="🔢 Total Trades",
        value=f"{summary.get('count', 0)}",
    )

st.markdown("---")

# ── Charts ───────────────────────────────────────────────────────────
if snapshots:
    df_snap = pd.DataFrame([
        {
            "timestamp": s.timestamp,
            "equity": s.equity,
            "cash": s.cash,
            "drawdown": s.drawdown_pct * 100,
        }
        for s in reversed(snapshots)
    ])
    df_snap["timestamp"] = pd.to_datetime(df_snap["timestamp"])

    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.1,
        row_heights=[0.7, 0.3],
        subplot_titles=("Equity Curve", "Drawdown %"),
    )

    # Equity curve
    fig.add_trace(
        go.Scatter(
            x=df_snap["timestamp"],
            y=df_snap["equity"],
            mode="lines",
            name="Equity",
            line=dict(color="#00ff88", width=2),
            fill="tozeroy",
            fillcolor="rgba(0, 255, 136, 0.1)",
        ),
        row=1, col=1,
    )

    # Drawdown
    fig.add_trace(
        go.Scatter(
            x=df_snap["timestamp"],
            y=df_snap["drawdown"],
            mode="lines",
            name="Drawdown",
            line=dict(color="#ff4757", width=2),
            fill="tozeroy",
            fillcolor="rgba(255, 71, 87, 0.1)",
        ),
        row=2, col=1,
    )

    fig.update_layout(
        height=600,
        template="plotly_dark",
        paper_bgcolor="#0e0e0e",
        plot_bgcolor="#0e0e0e",
        font=dict(color="#ffffff"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=40, r=40, t=80, b=40),
    )

    fig.update_yaxes(title_text="USD", row=1, col=1, gridcolor="#333")
    fig.update_yaxes(title_text="%", row=2, col=1, gridcolor="#333")
    fig.update_xaxes(gridcolor="#333")

    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("📭 No equity snapshots yet. Bot will record them every 10 iterations.")

st.markdown("---")

# ── Recent Trades ────────────────────────────────────────────────────
st.subheader("📝 Recent Trades")

if trades:
    df_trades = pd.DataFrame([
        {
            "Time": t.timestamp.strftime("%Y-%m-%d %H:%M") if isinstance(t.timestamp, datetime) else str(t.timestamp)[:16],
            "Symbol": t.symbol,
            "Side": t.side.upper(),
            "Entry": f"${t.entry_price:,.2f}",
            "Exit": f"${t.exit_price:,.2f}" if t.exit_price else "—",
            "P&L": f"${t.pnl:,.2f}",
            "P&L%": f"{t.pnl_pct:.2%}",
            "Reason": t.exit_reason,
            "Regime": t.market_regime,
        }
        for t in trades[:20]
    ])

    def highlight_pnl(val):
        try:
            num = float(val.replace("$", "").replace(",", ""))
            if num > 0:
                return "background-color: rgba(0, 255, 136, 0.2)"
            elif num < 0:
                return "background-color: rgba(255, 71, 87, 0.2)"
        except:
            pass
        return ""

    st.dataframe(
        df_trades.style.map(highlight_pnl, subset=["P&L"]),
        use_container_width=True,
        height=400,
    )
else:
    st.info("📭 No trades recorded yet.")

st.markdown("---")

# ── Trade Summary by Symbol ──────────────────────────────────────────
if trades:
    st.subheader("📊 Performance by Symbol")

    symbols = list(set(t.symbol for t in trades))
    cols = st.columns(len(symbols))

    for i, sym in enumerate(symbols):
        sym_summary = logger.trade_summary(symbol=sym)
        with cols[i]:
            st.markdown(f"**{sym}**")
            st.markdown(f"Trades: {sym_summary['count']}")
            st.markdown(f"P&L: `${sym_summary['total_pnl']:,.2f}`")
            st.markdown(f"Winrate: `{sym_summary['winrate']:.1%}`")

st.markdown("---")

# ── Emotion Distribution ─────────────────────────────────────────────
emotions = logger.emotion_distribution()
if emotions:
    st.subheader("🎭 Emotion Distribution")
    df_emo = pd.DataFrame([
        {"Emotion": k, "Count": v}
        for k, v in sorted(emotions.items(), key=lambda x: -x[1])
    ])
    fig_emo = go.Figure(go.Bar(
        x=df_emo["Emotion"],
        y=df_emo["Count"],
        marker_color=["#00ff88", "#ffa502", "#ff4757", "#74b9ff", "#a29bfe"],
    ))
    fig_emo.update_layout(
        template="plotly_dark",
        paper_bgcolor="#0e0e0e",
        plot_bgcolor="#0e0e0e",
        font=dict(color="#ffffff"),
        margin=dict(l=40, r=40, t=40, b=40),
    )
    st.plotly_chart(fig_emo, use_container_width=True)

# ── Footer ───────────────────────────────────────────────────────────
st.markdown("---")
st.caption(f"🕐 Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Auto-refresh: {refresh_interval}s")
