'use client';

import { useEffect, useState, useCallback } from 'react';

export interface Trade {
  id: number | string;
  timestamp: string;
  symbol: string;
  side: string;
  entry_price: number;
  exit_price: number | null;
  size: number;
  pnl: number;
  pnl_pct: number;
  duration: string | null;
  exit_reason: string;
  stop_price: number | null;
  target_price: number | null;
  sub_strategy: string | null;
  wiki_alignment: number | null;
  wiki_action: string | null;
  regime: string | null;
  directional_regime: string | null;
  status: 'open' | 'closed';
}

interface UseTradesOptions {
  sub_strategy?: string;
  symbol?: string;
  limit?: number;
  pollInterval?: number;
}

export function useTrades(options: UseTradesOptions = {}) {
  const { sub_strategy, symbol, limit = 50, pollInterval = 30000 } = options;
  const [trades, setTrades] = useState<Trade[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchTrades = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      if (sub_strategy) params.set('sub_strategy', sub_strategy);
      if (symbol) params.set('symbol', symbol);
      params.set('limit', String(limit));

      const res = await fetch(`http://localhost:8090/api/v1/trades?${params}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setTrades(data.trades || []);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  }, [sub_strategy, symbol, limit]);

  useEffect(() => {
    fetchTrades();
    const interval = setInterval(fetchTrades, pollInterval);
    return () => clearInterval(interval);
  }, [fetchTrades, pollInterval]);

  return { trades, loading, error, refetch: fetchTrades };
}
