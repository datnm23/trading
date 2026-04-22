"""Streamlit dashboard for backtest visualization and wiki chat."""

import sys
from pathlib import Path

# Add project root to path so imports work when run via `streamlit run`
project_root = Path(__file__).parent.parent.resolve()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import json

import pandas as pd
import numpy as np

# Streamlit imports are inside functions to allow file import without streamlit installed


def _load_backtest_results():
    """Load any saved backtest results."""
    results_dir = Path("./data/processed")
    if not results_dir.exists():
        return []
    files = sorted(results_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    return files[:10]


def run_dashboard():
    import streamlit as st
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    st.set_page_config(page_title="Hybrid Trading System", layout="wide")

    # --- Sidebar ---
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", ["Backtest", "Wiki Chat", "Live Status", "Strategy Comparison", "ML Models"])

    # --- Page: Backtest ---
    if page == "Backtest":
        st.title("Backtest Results")

        # Strategy selector
        strategy = st.selectbox(
            "Strategy",
            ["EMA-Trend", "Monthly-Breakout", "Grid-MeanReversion", "RegimeEnsemble"]
        )
        symbol = st.selectbox("Symbol", ["BTC/USDT", "ETH/USDT", "SOL/USDT"])
        timeframe = st.selectbox("Timeframe", ["1d", "4h", "1h"])

        if st.button("Run Backtest"):
            with st.spinner("Running backtest..."):
                from backtest.run import run_backtest
                metrics = run_backtest(strategy, symbol, timeframe, "config/system.yaml")

            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total Return", f"{metrics['total_return']:.2%}")
            col2.metric("Sharpe", f"{metrics['sharpe']:.2f}")
            col3.metric("Max Drawdown", f"{metrics['max_drawdown']:.2%}")
            col4.metric("Trades", metrics['total_trades'])

            # Equity curve (mock if not saved)
            st.subheader("Equity Curve")
            st.info("Equity curve visualization requires saving results to processed/ directory.")

            # Comparison table
            if st.checkbox("Compare all strategies"):
                from backtest.run import run_backtest
                strategies = ["EMA-Trend", "Monthly-Breakout", "Grid-MeanReversion", "RegimeEnsemble"]
                results = []
                for s in strategies:
                    try:
                        results.append(run_backtest(s, symbol, timeframe, "config/system.yaml"))
                    except Exception as e:
                        st.error(f"{s} failed: {e}")

                if results:
                    df = pd.DataFrame(results)
                    df["total_return"] = df["total_return"].apply(lambda x: f"{x:.2%}")
                    df["max_drawdown"] = df["max_drawdown"].apply(lambda x: f"{x:.2%}")
                    df["winrate"] = df["winrate"].apply(lambda x: f"{x:.2%}")
                    st.dataframe(df[["strategy", "total_return", "sharpe", "max_drawdown", "winrate", "profit_factor", "total_trades"]])

    # --- Page: Wiki Chat ---
    elif page == "Wiki Chat":
        st.title("Turtle Trading Wiki - Knowledge Chat")

        from knowledge_engine.rag import WikiRAG

        @st.cache_resource
        def get_rag():
            rag = WikiRAG()
            rag.build_index()
            return rag

        rag = get_rag()

        query = st.text_input("Ask about trading concepts:", "drawdown management")
        if st.button("Search") or query:
            with st.spinner("Searching wiki..."):
                results = rag.search(query)

            if not results:
                st.warning("No results found.")
            else:
                for r in results:
                    doc = r["document"]
                    with st.expander(f"{doc['title']} (score: {r['score']:.3f})"):
                        st.markdown(doc["content"][:1500])
                        if doc.get("source_url"):
                            st.markdown(f"[Source]({doc['source_url']})")

        # Raw context
        if st.checkbox("Show raw context"):
            ctx = rag.get_context(query)
            st.text_area("Context for LLM", ctx[:2000], height=300)

    # --- Page: Live Status ---
    elif page == "Live Status":
        st.title("Paper Trading Status")

        if st.button("Start Paper Trading"):
            st.info("Paper trading started in background. Refresh to see updates.")
            # In a real app, this would spawn a background process

        # Mock status
        st.subheader("Account Summary")
        col1, col2, col3 = st.columns(3)
        col1.metric("Equity", "$102,450.00", "+2.45%")
        col2.metric("Open Positions", "1")
        col3.metric("Today P&L", "$+340.00")

        st.subheader("Recent Trades")
        trades_df = pd.DataFrame({
            "Time": ["2026-04-21 08:00", "2026-04-20 08:00"],
            "Symbol": ["BTC/USDT", "BTC/USDT"],
            "Side": ["BUY", "SELL"],
            "Price": [75840.0, 74200.0],
            "P&L": [0, 1840.0],
        })
        st.dataframe(trades_df)

    # --- Page: Strategy Comparison ---
    elif page == "Strategy Comparison":
        st.title("Real-Time Strategy Comparison")

        from monitoring.comparison_engine import StrategyComparison

        @st.cache_resource
        def get_comparison_engine():
            return StrategyComparison()

        comp = get_comparison_engine()

        if st.button("🔄 Refresh"):
            st.rerun()

        with st.spinner("Polling strategy bots..."):
            comp.poll_all()

        leaderboard = comp.leaderboard()

        if not leaderboard:
            st.warning("No strategy bots are currently running. Start bots with `python3 -m execution.live_trading`.")
        else:
            # Metrics row
            cols = st.columns(len(leaderboard))
            for idx, row in enumerate(leaderboard):
                delta_color = "normal" if row["return_pct"] >= 0 else "inverse"
                cols[idx].metric(
                    label=row["strategy"],
                    value=f"${row['equity']:,.2f}",
                    delta=f"{row['return_pct']:+.2%}",
                    delta_color=delta_color,
                )

            # Leaderboard table
            st.subheader("Leaderboard")
            df = pd.DataFrame(leaderboard)
            df["return_pct"] = df["return_pct"].apply(lambda x: f"{x:+.2%}")
            df["daily_pnl"] = df["daily_pnl"].apply(lambda x: f"${x:,.2f}")
            df["equity"] = df["equity"].apply(lambda x: f"${x:,.2f}")
            st.dataframe(df, use_container_width=True)

            # Equity curves
            st.subheader("Equity Curves")
            curves = comp.get_equity_curves()
            if curves and any(curves.values()):
                fig = go.Figure()
                for name, points in curves.items():
                    if points:
                        times = [p[0] for p in points]
                        equities = [p[1] for p in points]
                        fig.add_trace(go.Scatter(
                            x=times, y=equities,
                            mode='lines',
                            name=name,
                        ))
                fig.update_layout(
                    xaxis_title="Time",
                    yaxis_title="Equity ($)",
                    height=400,
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Equity curves will appear after multiple polling cycles.")

    # --- Page: ML Models ---
    elif page == "ML Models":
        st.title("ML Model Training")

        symbol = st.selectbox("Symbol", ["BTC/USDT", "ETH/USDT"])
        if st.button("Train Model"):
            with st.spinner("Training model (this may take a while)..."):
                from data.feed import DataFeed
                from ml.pipelines.xgboost_pipeline import MLClassifierPipeline

                feed = DataFeed()
                df = feed.fetch(symbol, timeframe="1d", limit=1000)

                pipeline = MLClassifierPipeline()
                metrics = pipeline.train(df)

            st.success(f"Training complete! Accuracy: {metrics['mean_accuracy']:.3f}")

            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Accuracy", f"{metrics['mean_accuracy']:.3f}")
            col2.metric("Precision", f"{metrics['mean_precision']:.3f}")
            col3.metric("Recall", f"{metrics['mean_recall']:.3f}")
            col4.metric("F1", f"{metrics['mean_f1']:.3f}")

            # Feature importance
            fi = metrics.get("feature_importance", {})
            if fi:
                top = sorted(fi.items(), key=lambda x: x[1], reverse=True)[:15]
                fi_df = pd.DataFrame(top, columns=["Feature", "Importance"])
                st.subheader("Top 15 Feature Importances")
                st.bar_chart(fi_df.set_index("Feature"))

            # Save model
            pipeline.save("./ml/models/latest_model.pkl")
            st.info("Model saved to ./ml/models/latest_model.pkl")

        if st.button("Predict Latest"):
            try:
                from data.feed import DataFeed
                from ml.pipelines.xgboost_pipeline import MLClassifierPipeline

                feed = DataFeed()
                df = feed.fetch(symbol, timeframe="1d", limit=100)

                pipeline = MLClassifierPipeline()
                pipeline.load("./ml/models/latest_model.pkl")
                pred_df = pipeline.predict(df)

                latest = pred_df.iloc[-1]
                signal_map = {1: "BULLISH", -1: "BEARISH", 0: "NEUTRAL"}
                st.metric("Latest Signal", signal_map.get(latest["signal"], "NEUTRAL"))
                st.metric("Confidence", f"{latest['prediction_proba']:.3f}")
            except Exception as e:
                st.error(f"Prediction failed: {e}. Train a model first.")


if __name__ == "__main__":
    run_dashboard()
