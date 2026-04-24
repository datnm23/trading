'use client';

import { useEffect, useState, useCallback } from 'react';
import { io, Socket } from 'socket.io-client';

interface StrategyState {
  name: string;
  equity: number;
  return_pct: number;
  open_positions: number;
  running: boolean;
  mode: string;
  daily_pnl?: number;
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

interface SystemState {
  timestamp: string;
  strategies: StrategyState[];
  positions: any[];
  alerts: any[];
  equity_history?: { timestamp: string; equity: number; strategy: string }[];
  sub_strategy?: SubStrategyState;
  current_regime?: string;
  directional_regime?: string;
  regime_distribution?: Record<string, number>;
}

export function useSocketIO(url: string = 'http://localhost:8090') {
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
