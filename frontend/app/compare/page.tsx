'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useLang } from '@/components/layout/LangProvider';
import { NeoCard } from '@/components/ui/NeoCard';
import { NeoMetric } from '@/components/ui/NeoMetric';
import { t } from '@/lib/i18n';
import {
  getStock,
  getValuation,
  getSignal,
  type StockDetail,
  type ValuationResponse,
  type SignalItem,
} from '@/lib/api';
import { SignalBadge } from '@/components/stock/SignalBadge';
import { AlertTriangle, X } from 'lucide-react';

// ── helpers ───────────────────────────────────────────────────────────────────

function fmtVND(val: number | null): string {
  if (val === null || val === undefined) return '—';
  return val.toLocaleString('vi-VN') + ' ₫';
}

function fmtPct(val: number | null): string {
  if (val === null || val === undefined) return '—';
  return `${val >= 0 ? '+' : ''}${val.toFixed(2)}%`;
}

function fmtNum(val: number | null, dec = 2): string {
  if (val === null || val === undefined) return '—';
  return val.toFixed(dec);
}

// ── types ─────────────────────────────────────────────────────────────────────

interface StockData {
  ticker: string;
  stock: StockDetail | null;
  valuation: ValuationResponse | null;
  signal: SignalItem | null;
  loading: boolean;
  error: string | null;
}

const DEFAULT_TICKERS = ['FPT', 'VCB'];

/** Blank StockData for initial/loading state */
function emptyStockData(ticker: string, loading = true): StockData {
  return { ticker, stock: null, valuation: null, signal: null, loading, error: null };
}

// ── sub-components ────────────────────────────────────────────────────────────

function StockColumn({ data, lang }: { data: StockData; lang: 'vi' | 'en' }) {
  const { ticker, stock, valuation, signal, loading, error } = data;

  return (
    <div className="min-w-[180px] flex-1">
      <div className="font-black text-lg uppercase tracking-wider border-b-2 border-neo-stroke pb-2 mb-4">
        {ticker}
        {stock?.company.short_name && (
          <span className="block text-xs font-bold text-neo-muted normal-case tracking-normal mt-0.5">
            {stock.company.short_name}
          </span>
        )}
      </div>

      {loading && (
        <div className="text-neo-muted font-bold animate-pulse py-4 text-sm">
          {t('loading', lang)}
        </div>
      )}

      {error && (
        <div className="text-neo-bearish font-bold text-sm py-2">
          {t('error', lang)}: {error}
        </div>
      )}

      {!loading && !error && stock && (
        <div className="space-y-3">
          {/* Unified signal — source-of-truth, shown first */}
          <NeoMetric
            label={t('signalAction', lang)}
            value={signal ? <SignalBadge action={signal.action} /> : <span className="text-neo-muted">—</span>}
            variant="neutral"
          />
          <NeoMetric
            label={t('signalScore', lang)}
            value={signal != null ? `${signal.score.toFixed(1)}/100` : '—'}
            variant={
              signal != null
                ? signal.score >= 60 ? 'bullish' : signal.score <= 30 ? 'bearish' : 'neutral'
                : 'neutral'
            }
          />
          <NeoMetric
            label={t('price', lang)}
            value={fmtVND(stock.price.current_price)}
            variant="neutral"
          />
          <NeoMetric
            label={t('marketCap', lang)}
            value={fmtVND(stock.price.market_cap)}
            variant="neutral"
          />
          <NeoMetric label="P/E" value={fmtNum(stock.financials.pe_ratio)} variant="neutral" />
          <NeoMetric label="P/B" value={fmtNum(stock.financials.pb_ratio)} variant="neutral" />
          <NeoMetric
            label="ROE"
            value={
              stock.financials.roe !== null ? fmtPct(stock.financials.roe * 100) : '—'
            }
            variant={
              stock.financials.roe !== null
                ? stock.financials.roe > 0
                  ? 'bullish'
                  : 'bearish'
                : 'neutral'
            }
          />
          <NeoMetric
            label={t('netMargin', lang)}
            value={
              stock.financials.net_margin !== null
                ? fmtPct(stock.financials.net_margin * 100)
                : '—'
            }
            variant={
              stock.financials.net_margin !== null
                ? stock.financials.net_margin > 0
                  ? 'bullish'
                  : 'bearish'
                : 'neutral'
            }
          />
          <NeoMetric
            label="D/E"
            value={fmtNum(stock.financials.debt_to_equity)}
            variant={
              stock.financials.debt_to_equity !== null
                ? stock.financials.debt_to_equity < 1
                  ? 'bullish'
                  : 'bearish'
                : 'neutral'
            }
          />
          <NeoMetric label="EPS" value={fmtNum(stock.financials.eps)} variant="neutral" />
          {valuation && (
            <>
              <NeoMetric
                label={t('upside', lang)}
                value={
                  valuation.upside_pct !== null
                    ? fmtPct(valuation.upside_pct * 100)
                    : '—'
                }
                variant={
                  valuation.upside_pct !== null
                    ? valuation.upside_pct >= 0
                      ? 'bullish'
                      : 'bearish'
                    : 'neutral'
                }
              />
              <NeoMetric
                label={t('targetPrice', lang)}
                value={fmtVND(valuation.target_price)}
                variant="neutral"
              />
            </>
          )}
        </div>
      )}
    </div>
  );
}

// ── main ──────────────────────────────────────────────────────────────────────

export default function ComparePage() {
  const { lang } = useLang();
  const [inputVal, setInputVal] = useState('');
  const [tickers, setTickers] = useState<string[]>(DEFAULT_TICKERS);
  const [dataMap, setDataMap] = useState<Record<string, StockData>>({});

  // Fetch a single ticker (stock + valuation + signal) and update dataMap
  async function fetchTicker(ticker: string) {
    const upper = ticker.toUpperCase().trim();
    if (!upper) return;

    setDataMap((prev) => ({
      ...prev,
      [upper]: emptyStockData(upper),
    }));

    try {
      const [stock, valuation, signal] = await Promise.all([
        getStock(upper),
        getValuation(upper),
        getSignal(upper),
      ]);
      setDataMap((prev) => ({
        ...prev,
        [upper]: { ticker: upper, stock, valuation, signal, loading: false, error: null },
      }));
    } catch (e) {
      setDataMap((prev) => ({
        ...prev,
        [upper]: {
          ticker: upper,
          stock: null,
          valuation: null,
          signal: null,
          loading: false,
          error: e instanceof Error ? e.message : t('error', lang),
        },
      }));
    }
  }

  // Load default tickers on first render
  useState(() => {
    DEFAULT_TICKERS.forEach(fetchTicker);
  });

  function addTicker() {
    const upper = inputVal.toUpperCase().trim();
    if (!upper || tickers.includes(upper) || tickers.length >= 4) return;
    setTickers((prev) => [...prev, upper]);
    fetchTicker(upper);
    setInputVal('');
  }

  function removeTicker(ticker: string) {
    setTickers((prev) => prev.filter((t) => t !== ticker));
    setDataMap((prev) => {
      const next = { ...prev };
      delete next[ticker];
      return next;
    });
  }

  const columns = tickers.map((tk) => dataMap[tk] ?? emptyStockData(tk));

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-black uppercase tracking-wider">{t('compareStocks', lang)}</h2>

      {/* Disclaimer */}
      <div className="flex items-start gap-3 border-[3px] border-neo-warning bg-neo-warning/10 px-4 py-3">
        <AlertTriangle size={18} className="text-neo-warning mt-0.5 shrink-0" />
        <p className="text-sm font-bold">
          {lang === 'vi'
            ? 'Chỉ mang tính tham khảo, không phải lời khuyên đầu tư.'
            : 'For reference only, not investment advice.'}
        </p>
      </div>

      {/* Ticker input */}
      <div className="flex items-center gap-3 flex-wrap">
        <input
          type="text"
          value={inputVal}
          onChange={(e) => setInputVal(e.target.value.toUpperCase())}
          onKeyDown={(e) => e.key === 'Enter' && addTicker()}
          placeholder={t('addTicker', lang) + ' (VD: VIC)'}
          maxLength={10}
          className="border-[3px] border-neo-stroke px-4 py-2 bg-neo-surface font-mono w-40 focus:outline-none focus:shadow-neo uppercase"
        />
        <button
          onClick={addTicker}
          disabled={tickers.length >= 4}
          className="neo-button px-4 py-2 text-sm font-bold uppercase tracking-wider bg-neo-primary border-[3px] border-neo-stroke hover:shadow-neo disabled:opacity-50"
        >
          {t('compare', lang)}
        </button>
        <div className="flex items-center gap-2 flex-wrap">
          {tickers.map((tk) => (
            <div
              key={tk}
              className="flex items-center gap-1 border-[2px] border-neo-stroke px-2 py-1 bg-neo-surface text-sm font-bold"
            >
              <Link href={`/stock/${tk}`} className="hover:underline text-neo-primary">
                {tk}
              </Link>
              <button onClick={() => removeTicker(tk)} className="ml-1 text-neo-muted hover:text-neo-bearish">
                <X size={12} />
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* Comparison grid */}
      <NeoCard title={t('compareStocks', lang)}>
        {columns.length === 0 ? (
          <p className="text-neo-muted text-center py-8">{t('noData', lang)}</p>
        ) : (
          <div className="flex gap-8 overflow-x-auto pb-2">
            {columns.map((col) => (
              <StockColumn key={col.ticker} data={col} lang={lang} />
            ))}
          </div>
        )}
      </NeoCard>
    </div>
  );
}
