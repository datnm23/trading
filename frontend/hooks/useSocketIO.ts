'use client';

import { useEffect, useState, useCallback } from 'react';
import { io, Socket } from 'socket.io-client';

export interface StrategyState {
  name: string;
  equity: number;
  return_pct: number;
  open_positions: number;
  running: boolean;
  mode: string;
  daily_pnl?: number;
  strategy_type?: string;
  capital?: number;
  meta?: Record<string, unknown>;
}

interface SubStrategyState {
  symbol?: string;
  bar_time?: string;
  regime?: string;
  directional_regime?: string;
  sub_signals?: Record<string, string>;
  rejection_reasons?: string[];
  final_decision?: string;
  wiki_alignment?: number;
  wiki_top_concepts?: string;
  wiki_action?: string;
  wiki_min_alignment?: number;
}

export interface Position {
  symbol: string;
  side: string;
  entry_price: number;
  size: number;
  current_price?: number;
  unrealized_pnl?: number;
  stop_price?: number;
  strategy?: string;
  entry_time?: string;
  meta?: Record<string, unknown>;
}

export interface TrailingStop {
  symbol: string;
  entry_price: number;
  peak_price: number;
  current_stop: number;
  activated: boolean;
  profit_pct: number;
}

export interface SlippageItem {
  symbol: string;
  trades: number;
  avg_slippage_pct: number;
  max_slippage_pct: number;
  total_cost: number;
}

export interface PartialExit {
  symbol: string;
  entry: number;
  initial_size: number;
  remaining: number;
  executed_count: number;
}

interface Alert {
  level: string;
  message: string;
  timestamp: string;
  source?: string;
}

interface SystemState {
  timestamp: string;
  strategies: StrategyState[];
  positions: Position[];
  alerts: Alert[];
  equity_history?: { timestamp: string; equity: number; strategy: string }[];
  trailing_stops?: TrailingStop[];
  slippage?: SlippageItem[];
  partial_exits?: PartialExit[];
  sub_strategy?: SubStrategyState;
  current_regime?: string;
  directional_regime?: string;
  regime_distribution?: Record<string, number>;
}

import { API_BASE_URL } from '@/lib/api';

export function useSocketIO(url: string = API_BASE_URL) {
  const [socket, setSocket] = useState<Socket | null>(null);
  const [connected, setConnected] = useState(false);
  const [state, setState] = useState<SystemState | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const s = io(url, {
      transports: ['websocket', 'polling'],
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionAttempts: 10,
      timeout: 10000,
    });

    s.on('connect', () => {
      setConnected(true);
      setError(null);
      s.emit('subscribe', { channel: 'all' });
    });

    s.on('disconnect', () => {
      setConnected(false);
    });

    s.on('state_update', (data: SystemState) => {
      setState(data);
    });

    s.on('connect_error', (err) => {
      setError(err.message);
      setConnected(false);
    });

    setSocket(s);

    return () => {
      s.disconnect();
    };
  }, [url]);

  const reconnect = useCallback(() => {
    if (socket) {
      socket.connect();
    }
  }, [socket]);

  return { socket, connected, state, error, reconnect };
}
