-- PostgreSQL schema for trading journal
-- Compatible with trade_logger.py

CREATE TABLE IF NOT EXISTS trades (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    symbol VARCHAR(20) NOT NULL,
    strategy VARCHAR(50),
    side VARCHAR(10),
    entry_price NUMERIC(20, 8),
    exit_price NUMERIC(20, 8),
    size NUMERIC(20, 8),
    pnl NUMERIC(20, 2),
    pnl_pct NUMERIC(10, 4),
    holding_bars INTEGER,
    exit_reason VARCHAR(50),
    stop_price NUMERIC(20, 8),
    target_price NUMERIC(20, 8),
    reasoning TEXT,
    emotion_before VARCHAR(20),
    emotion_after VARCHAR(20),
    market_regime VARCHAR(20),
    notes TEXT,
    tags VARCHAR(255),
    raw_metadata JSONB
);

CREATE INDEX idx_trades_timestamp ON trades(timestamp);
CREATE INDEX idx_trades_symbol ON trades(symbol);
CREATE INDEX idx_trades_strategy ON trades(strategy);
CREATE INDEX idx_trades_exit_reason ON trades(exit_reason);

CREATE TABLE IF NOT EXISTS journal (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    entry_type VARCHAR(30),
    content TEXT,
    emotion VARCHAR(20),
    focus_score INTEGER,
    discipline_score INTEGER,
    lessons TEXT,
    tags VARCHAR(255)
);

CREATE INDEX idx_journal_date ON journal(date);

CREATE TABLE IF NOT EXISTS snapshots (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    equity NUMERIC(20, 2),
    cash NUMERIC(20, 2),
    open_positions INTEGER,
    open_exposure NUMERIC(20, 2),
    drawdown_pct NUMERIC(10, 4),
    daily_pnl NUMERIC(20, 2)
);

CREATE INDEX idx_snapshots_timestamp ON snapshots(timestamp);

CREATE TABLE IF NOT EXISTS equity_snapshots (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    equity NUMERIC(20, 2) NOT NULL,
    cash NUMERIC(20, 2),
    open_positions INTEGER,
    drawdown_pct NUMERIC(10, 4)
);

CREATE INDEX idx_equity_timestamp ON equity_snapshots(timestamp);
