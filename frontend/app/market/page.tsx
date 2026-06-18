'use client';

import { useState, useEffect, useMemo } from 'react';
import Link from 'next/link';
import { useLang } from '@/components/layout/LangProvider';
import { NeoCard } from '@/components/ui/NeoCard';
import { t } from '@/lib/i18n';
import { getMarketOverview, type MarketStock } from '@/lib/api';
import { TrendingUp, TrendingDown } from 'lucide-react';

// ── helpers ───────────────────────────────────────────────────────────────────

function fmtVND(val: number): string {
  return val.toLocaleString('vi-VN') + ' ₫';
}

function fmtPct(val: number | null): string {
  if (val === null || val === undefined) return '—';
  return `${val >= 0 ? '+' : ''}${val.toFixed(2)}%`;
}

type SortKey = 'ticker' | 'price' | 'change_pct';
type SortDir = 'asc' | 'desc';

// ── component ─────────────────────────────────────────────────────────────────

export default function MarketPage() {
  const { lang } = useLang();
  const [stocks, setStocks] = useState<MarketStock[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sortKey, setSortKey] = useState<SortKey>('ticker');
  const [sortDir, setSortDir] = useState<SortDir>('asc');

  useEffect(() => {
    let cancelled = false;
    async function fetchData() {
      setLoading(true);
      setError(null);
      try {
        const data = await getMarketOverview();
        if (!cancelled) setStocks(data.stocks);
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : t('error', lang));
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    fetchData();
    return () => { cancelled = true; };
  }, [lang]);

  function toggleSort(key: SortKey) {
    if (sortKey === key) {
      setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortKey(key);
      setSortDir(key === 'change_pct' ? 'desc' : 'asc');
    }
  }

  const sorted = useMemo(() => {
    return [...stocks].sort((a, b) => {
      let diff = 0;
      if (sortKey === 'ticker') diff = a.ticker.localeCompare(b.ticker);
      else if (sortKey === 'price') diff = a.price - b.price;
      else diff = (a.change_pct ?? 0) - (b.change_pct ?? 0);
      return sortDir === 'asc' ? diff : -diff;
    });
  }, [stocks, sortKey, sortDir]);

  function SortIndicator({ col }: { col: SortKey }) {
    if (sortKey !== col) return <span className="text-neo-muted ml-1">↕</span>;
    return <span className="ml-1">{sortDir === 'asc' ? '↑' : '↓'}</span>;
  }

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-black uppercase tracking-wider">{t('market', lang)} — VN30</h2>

      {error && (
        <div className="neo-card p-4 text-neo-bearish font-bold text-center">
          {t('error', lang)}: {error}
        </div>
      )}

      <NeoCard title={`VN30 — ${stocks.length} ${t('ticker', lang)}`}>
        {loading && stocks.length === 0 ? (
          <div className="py-12 text-center text-neo-muted font-bold animate-pulse">
            {t('loading', lang)}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="neo-table w-full">
              <thead>
                <tr>
                  <th
                    className="cursor-pointer select-none hover:text-neo-primary"
                    onClick={() => toggleSort('ticker')}
                  >
                    {t('ticker', lang)} <SortIndicator col="ticker" />
                  </th>
                  <th>{t('companyName', lang)}</th>
                  <th>{t('sector', lang)}</th>
                  <th
                    className="cursor-pointer select-none hover:text-neo-primary"
                    onClick={() => toggleSort('price')}
                  >
                    {t('price', lang)} <SortIndicator col="price" />
                  </th>
                  <th
                    className="cursor-pointer select-none hover:text-neo-primary"
                    onClick={() => toggleSort('change_pct')}
                  >
                    {t('changePct', lang)} <SortIndicator col="change_pct" />
                  </th>
                </tr>
              </thead>
              <tbody>
                {sorted.map((s) => {
                  const up = s.change_pct !== null && s.change_pct >= 0;
                  const down = s.change_pct !== null && s.change_pct < 0;
                  return (
                    <tr key={s.ticker}>
                      <td className="font-black">
                        <Link
                          href={`/stock/${s.ticker}`}
                          className="hover:underline text-neo-primary"
                        >
                          {s.ticker}
                        </Link>
                      </td>
                      <td className="text-sm">{s.name}</td>
                      <td className="text-xs font-mono text-neo-muted">{s.sector}</td>
                      <td className="font-mono text-sm">{fmtVND(s.price)}</td>
                      <td
                        className={`font-bold font-mono flex items-center gap-1 ${
                          up ? 'text-neo-bullish' : down ? 'text-neo-bearish' : 'text-neo-muted'
                        }`}
                      >
                        {up && <TrendingUp size={13} />}
                        {down && <TrendingDown size={13} />}
                        {fmtPct(s.change_pct)}
                      </td>
                    </tr>
                  );
                })}
                {sorted.length === 0 && !loading && (
                  <tr>
                    <td colSpan={5} className="text-center text-neo-muted py-8">
                      {t('noData', lang)}
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </NeoCard>
    </div>
  );
}
