'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useLang } from '@/components/layout/LangProvider';
import { NeoCard } from '@/components/ui/NeoCard';
import { t } from '@/lib/i18n';
import { getRecommendations, type RecommendationItem } from '@/lib/api';
import { SignalBadge } from '@/components/stock/SignalBadge';
import { Minus, AlertTriangle, RefreshCw } from 'lucide-react';

// ── helpers ───────────────────────────────────────────────────────────────────

function fmtVND(val: number | null): string {
  if (val === null || val === undefined) return '—';
  return val.toLocaleString('vi-VN') + ' ₫';
}

function fmtUpside(val: number | null): string {
  if (val === null || val === undefined) return '—';
  // API returns fraction (e.g. 0.109 = +10.9%)
  const pct = val * 100;
  return `${pct >= 0 ? '+' : ''}${pct.toFixed(1)}%`;
}

// ── component ─────────────────────────────────────────────────────────────────

export default function ReportsPage() {
  const { lang } = useLang();
  const [items, setItems] = useState<RecommendationItem[]>([]);
  const [disclaimer, setDisclaimer] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function fetchData() {
    setLoading(true);
    setError(null);
    try {
      const data = await getRecommendations(100);
      setItems(data.items);
      setDisclaimer(data.disclaimer);
    } catch (e) {
      setError(e instanceof Error ? e.message : t('error', lang));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    fetchData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <h2 className="text-2xl font-black uppercase tracking-wider">
          {t('recommendationJournal', lang)}
        </h2>
        <button
          onClick={fetchData}
          disabled={loading}
          className="neo-button flex items-center gap-2 px-4 py-2 text-sm font-bold uppercase tracking-wider bg-neo-surface border-[3px] border-neo-stroke hover:shadow-neo disabled:opacity-50"
        >
          <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
          {t('refresh', lang)}
        </button>
      </div>

      {/* Disclaimer */}
      {disclaimer && (
        <div className="flex items-start gap-3 border-[3px] border-neo-warning bg-neo-warning/10 px-4 py-3">
          <AlertTriangle size={18} className="text-neo-warning mt-0.5 shrink-0" />
          <p className="text-sm font-bold">{disclaimer}</p>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="neo-card p-4 text-neo-bearish font-bold text-center">
          {t('error', lang)}: {error}
        </div>
      )}

      {/* Table */}
      <NeoCard title={`${t('recommendationJournal', lang)} — ${items.length}`}>
        {loading && items.length === 0 ? (
          <div className="py-12 text-center text-neo-muted font-bold animate-pulse">
            {t('loading', lang)}
          </div>
        ) : items.length === 0 ? (
          <div className="py-12 text-center">
            <Minus size={48} className="mx-auto mb-4 text-neo-muted" />
            <p className="font-bold text-neo-muted">{t('noRecommendations', lang)}</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="neo-table w-full">
              <thead>
                <tr>
                  <th>{t('upcomingDate', lang)}</th>
                  <th>{t('ticker', lang)}</th>
                  <th>{t('recommendation', lang)}</th>
                  <th>{t('score', lang)}</th>
                  <th>{t('upside', lang)}</th>
                  <th>{t('price', lang)}</th>
                  <th>{t('targetPrice', lang)}</th>
                </tr>
              </thead>
              <tbody>
                {items.map((item) => {
                  const upPct = item.upside_pct !== null ? item.upside_pct * 100 : null;
                  return (
                    <tr key={item.id}>
                      <td className="font-mono text-sm text-neo-muted">{item.date}</td>
                      <td className="font-black">
                        <Link
                          href={`/stock/${item.ticker}`}
                          className="hover:underline text-neo-primary"
                        >
                          {item.ticker}
                        </Link>
                      </td>
                      <td>
                        <SignalBadge action={item.recommendation} />
                      </td>
                      <td
                        className={`font-mono font-bold ${
                          item.score !== null && item.score >= 60
                            ? 'text-neo-bullish'
                            : item.score !== null && item.score < 40
                              ? 'text-neo-bearish'
                              : 'text-neo-warning'
                        }`}
                      >
                        {item.score !== null ? `${item.score}/100` : '—'}
                      </td>
                      <td
                        className={`font-mono font-bold ${
                          upPct !== null && upPct >= 0
                            ? 'text-neo-bullish'
                            : upPct !== null
                              ? 'text-neo-bearish'
                              : 'text-neo-muted'
                        }`}
                      >
                        {fmtUpside(item.upside_pct)}
                      </td>
                      <td className="font-mono text-sm">{fmtVND(item.current_price)}</td>
                      <td className="font-mono text-sm">{fmtVND(item.target_price)}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </NeoCard>
    </div>
  );
}
