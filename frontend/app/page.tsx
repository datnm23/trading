'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useLang } from '@/components/layout/LangProvider';
import { NeoCard } from '@/components/ui/NeoCard';
import { NeoMetric } from '@/components/ui/NeoMetric';
import { t } from '@/lib/i18n';
import {
  getMarketOverview,
  getSignals,
  type MarketOverviewResponse,
  type SignalsResponse,
} from '@/lib/api';
import { SignalBadge } from '@/components/stock/SignalBadge';
import { TrendingUp, TrendingDown } from 'lucide-react';

// ── helpers ───────────────────────────────────────────────────────────────────

function fmtPct(val: number | null): string {
  if (val === null || val === undefined) return '—';
  return `${val >= 0 ? '+' : ''}${val.toFixed(2)}%`;
}

function fmtVND(val: number): string {
  return val.toLocaleString('vi-VN') + ' ₫';
}

function fmtPoints(val: number): string {
  return val.toLocaleString('vi-VN', { maximumFractionDigits: 2 });
}

// ── component ─────────────────────────────────────────────────────────────────

export default function OverviewPage() {
  const { lang } = useLang();
  const [overview, setOverview] = useState<MarketOverviewResponse | null>(null);
  const [signals, setSignals] = useState<SignalsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function fetchAll() {
      setLoading(true);
      setError(null);
      try {
        const [ov, sg] = await Promise.all([getMarketOverview(), getSignals()]);
        if (!cancelled) {
          setOverview(ov);
          setSignals(sg);
        }
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : t('error', lang));
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    fetchAll();
    return () => { cancelled = true; };
  }, [lang]);

  const stocks = overview?.stocks ?? [];
  const idx = overview?.index ?? null;

  // Top 5 gainers / losers by change_pct
  const withChange = stocks.filter((s) => s.change_pct !== null);
  const gainers = [...withChange]
    .sort((a, b) => (b.change_pct ?? 0) - (a.change_pct ?? 0))
    .slice(0, 5);
  const losers = [...withChange]
    .sort((a, b) => (a.change_pct ?? 0) - (b.change_pct ?? 0))
    .slice(0, 5);

  // Top 5 signals sorted by score desc (backend already sorts, but guard)
  const topSignals = (signals?.items ?? []).slice(0, 5);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-16 text-neo-muted font-bold animate-pulse text-xl uppercase">
        {t('loading', lang)}
      </div>
    );
  }

  if (error) {
    return (
      <div className="neo-card p-6 text-neo-bearish font-bold text-center">
        {t('error', lang)}: {error}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-black uppercase tracking-wider">{t('overview', lang)}</h2>

      {/* VN-Index card */}
      {idx && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <NeoCard>
            <NeoMetric
              label={t('vnindex', lang)}
              value={fmtPoints(idx.value)}
              variant={
                idx.change_pct === null ? 'neutral' : idx.change_pct >= 0 ? 'bullish' : 'bearish'
              }
            />
            {idx.change_pct !== null && (
              <div
                className={`mt-2 font-bold font-mono text-sm ${
                  idx.change_pct >= 0 ? 'text-neo-bullish' : 'text-neo-bearish'
                }`}
              >
                {idx.change_pct >= 0 ? (
                  <TrendingUp size={14} className="inline mr-1" />
                ) : (
                  <TrendingDown size={14} className="inline mr-1" />
                )}
                {fmtPct(idx.change_pct)}
              </div>
            )}
          </NeoCard>
        </div>
      )}

      {/* Top gainers / losers */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <NeoCard title={t('topGainers', lang)}>
          {gainers.length === 0 ? (
            <p className="text-neo-muted text-center py-4">{t('noData', lang)}</p>
          ) : (
            <table className="neo-table w-full">
              <thead>
                <tr>
                  <th>{t('ticker', lang)}</th>
                  <th>{t('price', lang)}</th>
                  <th>{t('changePct', lang)}</th>
                </tr>
              </thead>
              <tbody>
                {gainers.map((s) => (
                  <tr key={s.ticker}>
                    <td className="font-black">
                      <Link href={`/stock/${s.ticker}`} className="hover:underline text-neo-primary">
                        {s.ticker}
                      </Link>
                    </td>
                    <td className="font-mono text-sm">{fmtVND(s.price)}</td>
                    <td className="font-bold font-mono text-neo-bullish">
                      {fmtPct(s.change_pct)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </NeoCard>

        <NeoCard title={t('topLosers', lang)}>
          {losers.length === 0 ? (
            <p className="text-neo-muted text-center py-4">{t('noData', lang)}</p>
          ) : (
            <table className="neo-table w-full">
              <thead>
                <tr>
                  <th>{t('ticker', lang)}</th>
                  <th>{t('price', lang)}</th>
                  <th>{t('changePct', lang)}</th>
                </tr>
              </thead>
              <tbody>
                {losers.map((s) => (
                  <tr key={s.ticker}>
                    <td className="font-black">
                      <Link href={`/stock/${s.ticker}`} className="hover:underline text-neo-primary">
                        {s.ticker}
                      </Link>
                    </td>
                    <td className="font-mono text-sm">{fmtVND(s.price)}</td>
                    <td className="font-bold font-mono text-neo-bearish">
                      {fmtPct(s.change_pct)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </NeoCard>
      </div>

      {/* Top unified signals */}
      <NeoCard title={t('topSignals', lang)}>
        {topSignals.length === 0 ? (
          <p className="text-neo-muted text-center py-4">{t('noData', lang)}</p>
        ) : (
          <table className="neo-table w-full">
            <thead>
              <tr>
                <th>#</th>
                <th>{t('ticker', lang)}</th>
                <th>{t('signalAction', lang)}</th>
                <th>{t('signalScore', lang)}</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {topSignals.map((item, idx) => (
                <tr key={item.ticker}>
                  <td className="font-mono text-neo-muted">{idx + 1}</td>
                  <td className="font-black">{item.ticker}</td>
                  <td>
                    <SignalBadge action={item.action} />
                  </td>
                  <td
                    className={`font-mono font-bold ${
                      item.score >= 60
                        ? 'text-neo-bullish'
                        : item.score <= 30
                          ? 'text-neo-bearish'
                          : 'text-neo-warning'
                    }`}
                  >
                    {item.score.toFixed(1)}
                  </td>
                  <td>
                    <Link
                      href={`/stock/${item.ticker}`}
                      className="neo-button px-3 py-1 text-xs font-bold uppercase tracking-wider bg-neo-surface border-[2px] border-neo-stroke hover:bg-neo-primary hover:shadow-neo"
                    >
                      Chi tiết →
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </NeoCard>
    </div>
  );
}
