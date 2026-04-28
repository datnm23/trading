'use client';

import { useState, useEffect, useCallback } from 'react';
import { useLang } from '@/components/layout/LangProvider';
import { NeoCard } from '@/components/ui/NeoCard';
import { NeoMetric } from '@/components/ui/NeoMetric';
import { MarketPriceChart } from '@/components/charts/MarketPriceChart';
import { t } from '@/lib/i18n';
import { API_BASE_URL, apiHeaders } from '@/lib/api';
import { TrendingUp, TrendingDown, Activity } from 'lucide-react';

const SYMBOLS = [
  { id: 'BTC/USDT', name: 'Bitcoin', icon: '₿' },
  { id: 'ETH/USDT', name: 'Ethereum', icon: 'Ξ' },
  { id: 'SOL/USDT', name: 'Solana', icon: '◎' },
];

const TIMEFRAMES = [
  { id: '1h', label: '1H' },
  { id: '4h', label: '4H' },
  { id: '1d', label: '1D' },
];

interface TickerData {
  price: number;
  change_24h_pct: number;
}

interface Candle {
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export default function MarketPage() {
  const { lang } = useLang();
  const [activeSymbol, setActiveSymbol] = useState('BTC/USDT');
  const [activeTf, setActiveTf] = useState('1d');
  const [candles, setCandles] = useState<Candle[]>([]);
  const [tickers, setTickers] = useState<Record<string, TickerData>>({});
  const [loading, setLoading] = useState(true);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [ohlcvRes, tickerRes] = await Promise.all([
        fetch(`${API_BASE_URL}/api/v1/market/ohlcv?symbol=${activeSymbol}&timeframe=${activeTf}&limit=100`, { headers: apiHeaders() }),
        fetch(`${API_BASE_URL}/api/v1/market/tickers`, { headers: apiHeaders() }),
      ]);

      if (ohlcvRes.ok) {
        const ohlcvData = await ohlcvRes.json();
        setCandles(ohlcvData.candles || []);
      }

      if (tickerRes.ok) {
        const tickerData = await tickerRes.json();
        setTickers(tickerData.tickers || {});
      }
    } catch (e) {
      console.error('Market data fetch failed:', e);
    } finally {
      setLoading(false);
    }
  }, [activeSymbol, activeTf]);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000); // refresh every 30s
    return () => clearInterval(interval);
  }, [fetchData]);

  const activeTicker = tickers[activeSymbol] || { price: 0, change_24h_pct: 0 };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-black uppercase tracking-wider">{t('market', lang)}</h2>
        <div className="flex items-center gap-2">
          <Activity size={16} className="text-neo-bullish animate-pulse" />
          <span className="text-sm font-bold font-mono">Live</span>
        </div>
      </div>

      {/* Symbol Tabs */}
      <div className="flex gap-2">
        {SYMBOLS.map((sym) => {
          const ticker = tickers[sym.id] || { price: 0, change_24h_pct: 0 };
          const isActive = activeSymbol === sym.id;
          return (
            <button
              key={sym.id}
              onClick={() => setActiveSymbol(sym.id)}
              className={`neo-button px-4 py-2 text-sm font-bold uppercase tracking-wider transition-all ${
                isActive
                  ? 'bg-neo-primary border-neo-stroke text-neo-stroke translate-x-1 shadow-neo'
                  : 'bg-neo-surface border-neo-stroke text-neo-text hover:bg-neo-bg'
              }`}
            >
              <span className="mr-2">{sym.icon}</span>
              {sym.name}
              {ticker.price > 0 && (
                <span className="ml-2 text-xs font-mono">
                  ${ticker.price.toLocaleString('en-US', { maximumFractionDigits: 0 })}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* Current Price Metrics */}
      {activeTicker.price > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <NeoCard>
            <NeoMetric
              label={SYMBOLS.find((s) => s.id === activeSymbol)?.name || activeSymbol}
              value={`$${activeTicker.price.toLocaleString('en-US', { maximumFractionDigits: 2 })}`}
              variant={activeTicker.change_24h_pct >= 0 ? 'bullish' : 'bearish'}
            />
          </NeoCard>
          <NeoCard>
            <NeoMetric
              label={t('change24h', lang)}
              value={`${activeTicker.change_24h_pct >= 0 ? '+' : ''}${activeTicker.change_24h_pct.toFixed(2)}%`}
              variant={activeTicker.change_24h_pct >= 0 ? 'bullish' : 'bearish'}
            />
          </NeoCard>
          <NeoCard>
            <NeoMetric
              label="High"
              value={candles.length > 0 ? `$${Math.max(...candles.map((c) => c.high)).toLocaleString()}` : '-'}
              variant="neutral"
            />
          </NeoCard>
          <NeoCard>
            <NeoMetric
              label="Low"
              value={candles.length > 0 ? `$${Math.min(...candles.map((c) => c.low)).toLocaleString()}` : '-'}
              variant="neutral"
            />
          </NeoCard>
        </div>
      )}

      {/* Timeframe Selector */}
      <div className="flex gap-2">
        {TIMEFRAMES.map((tf) => (
          <button
            key={tf.id}
            onClick={() => setActiveTf(tf.id)}
            className={`neo-button px-3 py-1 text-xs font-black uppercase tracking-wider transition-all ${
              activeTf === tf.id
                ? 'bg-neo-stroke text-neo-surface'
                : 'bg-neo-surface border-neo-stroke text-neo-text hover:bg-neo-bg'
            }`}
          >
            {tf.label}
          </button>
        ))}
      </div>

      {/* Price Chart */}
      <NeoCard title={`${t('priceChart', lang)} — ${activeSymbol}`}>
        {loading && candles.length === 0 ? (
          <div className="h-[470px] flex items-center justify-center">
            <div className="text-neo-muted font-bold animate-pulse">{t('loading', lang)}</div>
          </div>
        ) : candles.length > 0 ? (
          <MarketPriceChart data={candles} />
        ) : (
          <div className="h-[470px] flex items-center justify-center text-neo-muted font-bold">
            {t('noPriceData', lang)}
          </div>
        )}
      </NeoCard>

      {/* All Tickers Table */}
      <NeoCard title="All Markets">
        <div className="overflow-x-auto">
          <table className="neo-table">
            <thead>
              <tr>
                <th>Symbol</th>
                <th>Price</th>
                <th>24h Change</th>
                <th>Trend</th>
              </tr>
            </thead>
            <tbody>
              {SYMBOLS.map((sym) => {
                const t = tickers[sym.id] || { price: 0, change_24h_pct: 0 };
                return (
                  <tr
                    key={sym.id}
                    className={activeSymbol === sym.id ? 'bg-neo-primary/20' : ''}
                    onClick={() => setActiveSymbol(sym.id)}
                    style={{ cursor: 'pointer' }}
                  >
                    <td className="font-bold">
                      <span className="mr-2">{sym.icon}</span>
                      {sym.name}
                      <span className="text-neo-muted text-xs ml-2">{sym.id}</span>
                    </td>
                    <td className="font-mono">
                      {t.price > 0 ? `$${t.price.toLocaleString('en-US', { maximumFractionDigits: 2 })}` : '-'}
                    </td>
                    <td className={t.change_24h_pct >= 0 ? 'text-neo-bullish font-bold font-mono' : 'text-neo-bearish font-bold font-mono'}>
                      {t.change_24h_pct !== 0 ? `${t.change_24h_pct >= 0 ? '+' : ''}${t.change_24h_pct.toFixed(2)}%` : '-'}
                    </td>
                    <td>
                      {t.change_24h_pct >= 0 ? (
                        <TrendingUp size={18} className="text-neo-bullish" />
                      ) : (
                        <TrendingDown size={18} className="text-neo-bearish" />
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </NeoCard>
    </div>
  );
}
