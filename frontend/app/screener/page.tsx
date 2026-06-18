'use client';

import { useState, useEffect, useMemo, useCallback } from 'react';
import Link from 'next/link';
import { useLang } from '@/components/layout/LangProvider';
import { NeoCard } from '@/components/ui/NeoCard';
import { NeoBadge } from '@/components/ui/NeoBadge';
import { t } from '@/lib/i18n';
import { getScreener, getSignals, type ScreenerItem, type CriterionDetail, type SignalItem } from '@/lib/api';
import { SignalBadge } from '@/components/stock/SignalBadge';
import { RefreshCw, AlertTriangle } from 'lucide-react';

// ── helpers ───────────────────────────────────────────────────────────────────

type SortKey = 'rank' | 'ticker' | 'score' | 'passed_count' | 'signalScore';
type SortDir = 'asc' | 'desc';

// ── component ─────────────────────────────────────────────────────────────────

export default function ScreenerPage() {
  const { lang } = useLang();

  const [items, setItems] = useState<ScreenerItem[]>([]);
  // signalMap: ticker → SignalItem for O(1) lookup
  const [signalMap, setSignalMap] = useState<Record<string, SignalItem>>({});
  const [disclaimer, setDisclaimer] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [search, setSearch] = useState('');
  const [sortKey, setSortKey] = useState<SortKey>('rank');
  const [sortDir, setSortDir] = useState<SortDir>('asc');

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      // Fetch screener (tech criteria) + unified signals in parallel
      const [screenerData, signalsData] = await Promise.all([getScreener(), getSignals()]);
      setItems(screenerData.items);
      setDisclaimer(screenerData.disclaimer);
      // Build ticker → signal lookup map
      const map: Record<string, SignalItem> = {};
      for (const sig of signalsData.items) {
        map[sig.ticker] = sig;
      }
      setSignalMap(map);
    } catch (e) {
      setError(e instanceof Error ? e.message : t('error', lang));
    } finally {
      setLoading(false);
    }
  }, [lang]);

  useEffect(() => { fetchData(); }, [fetchData]);

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    const source = q ? items.filter((i) => i.ticker.toLowerCase().includes(q)) : items;
    return [...source].sort((a, b) => {
      let diff = 0;
      if (sortKey === 'rank') diff = a.rank - b.rank;
      else if (sortKey === 'score') diff = a.score - b.score;
      else if (sortKey === 'passed_count') diff = a.passed_count - b.passed_count;
      else if (sortKey === 'signalScore') {
        const sa = signalMap[a.ticker]?.score ?? -1;
        const sb = signalMap[b.ticker]?.score ?? -1;
        diff = sa - sb;
      }
      else diff = a.ticker.localeCompare(b.ticker);
      return sortDir === 'asc' ? diff : -diff;
    });
  }, [items, search, sortKey, sortDir, signalMap]);

  function toggleSort(key: SortKey) {
    if (sortKey === key) {
      setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortKey(key);
      setSortDir(key === 'rank' ? 'asc' : 'desc');
    }
  }

  function SortIndicator({ col }: { col: SortKey }) {
    if (sortKey !== col) return <span className="text-neo-muted ml-1">↕</span>;
    return <span className="ml-1">{sortDir === 'asc' ? '↑' : '↓'}</span>;
  }

  // top-3 criteria labels for a ticker (first passed, then failed)
  function topCriteria(criteria: CriterionDetail[]): CriterionDetail[] {
    const passed = criteria.filter((c) => c.passed);
    const failed = criteria.filter((c) => !c.passed);
    return [...passed, ...failed].slice(0, 3);
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div className="flex items-center gap-3 flex-wrap">
          <h2 className="text-2xl font-black uppercase tracking-wider">
            {t('screener', lang)}
          </h2>
          <NeoBadge status="warning">
            {lang === 'vi' ? 'THỬ NGHIỆM · CHƯA VALIDATE' : 'EXPERIMENTAL · UNVALIDATED'}
          </NeoBadge>
        </div>
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
      <div className="flex items-start gap-3 border-[3px] border-neo-warning bg-neo-warning/10 px-4 py-3">
        <AlertTriangle size={18} className="text-neo-warning mt-0.5 shrink-0" />
        <p className="text-sm font-bold text-neo-text">
          {disclaimer || (lang === 'vi'
            ? 'Bộ lọc kỹ thuật THỬ NGHIỆM, chưa được validate đầy đủ (chưa loại bỏ survivorship bias, mẫu hạn chế). Chỉ mang tính tham khảo, KHÔNG phải lời khuyên đầu tư.'
            : 'EXPERIMENTAL technical screener, not yet fully validated (survivorship bias not removed, limited sample). For reference only, NOT investment advice.')}
        </p>
      </div>

      {/* Search */}
      <div className="flex items-center gap-3">
        <input
          type="text"
          placeholder={t('searchPlaceholder', lang)}
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="border-[3px] border-neo-stroke px-4 py-2 bg-neo-surface font-mono w-64 focus:outline-none focus:shadow-neo"
        />
        {search && (
          <span className="text-sm text-neo-muted font-mono">
            {filtered.length} {t('trades', lang)}
          </span>
        )}
      </div>

      {/* Table */}
      <NeoCard title={`${t('screener', lang)} — ${items.length} ${t('trades', lang)}`}>
        {error && (
          <div className="text-neo-bearish font-bold py-4 text-center">
            {t('error', lang)}: {error}
          </div>
        )}
        {loading && items.length === 0 ? (
          <div className="py-12 text-center text-neo-muted font-bold animate-pulse">
            {t('loading', lang)}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="neo-table">
              <thead>
                <tr>
                  <th
                    className="cursor-pointer select-none hover:text-neo-primary"
                    onClick={() => toggleSort('rank')}
                  >
                    # <SortIndicator col="rank" />
                  </th>
                  <th
                    className="cursor-pointer select-none hover:text-neo-primary"
                    onClick={() => toggleSort('ticker')}
                  >
                    {t('ticker', lang)} <SortIndicator col="ticker" />
                  </th>
                  <th
                    className="cursor-pointer select-none hover:text-neo-primary"
                    onClick={() => toggleSort('signalScore')}
                  >
                    {t('signalAction', lang)} <SortIndicator col="signalScore" />
                  </th>
                  <th
                    className="cursor-pointer select-none hover:text-neo-primary"
                    onClick={() => toggleSort('signalScore')}
                  >
                    {t('signalScore', lang)} <SortIndicator col="signalScore" />
                  </th>
                  <th
                    className="cursor-pointer select-none hover:text-neo-primary"
                    onClick={() => toggleSort('score')}
                  >
                    Tech Score <SortIndicator col="score" />
                  </th>
                  <th
                    className="cursor-pointer select-none hover:text-neo-primary"
                    onClick={() => toggleSort('passed_count')}
                  >
                    Passed <SortIndicator col="passed_count" />
                  </th>
                  <th>Key Criteria</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((item) => {
                  const sig = signalMap[item.ticker];
                  const top = topCriteria(item.criteria);
                  return (
                    <tr key={item.ticker}>
                      <td className="font-mono text-neo-muted">{item.rank}</td>
                      <td className="font-black tracking-wider">{item.ticker}</td>
                      {/* Unified signal action — headline */}
                      <td>
                        {sig
                          ? <SignalBadge action={sig.action} />
                          : <span className="text-neo-muted font-mono text-xs">—</span>
                        }
                      </td>
                      {/* Unified signal score */}
                      <td className="font-mono font-bold">
                        {sig != null ? (
                          <span className={
                            sig.score >= 60
                              ? 'text-neo-bullish'
                              : sig.score <= 30
                                ? 'text-neo-bearish'
                                : 'text-neo-warning'
                          }>
                            {sig.score.toFixed(1)}
                          </span>
                        ) : <span className="text-neo-muted">—</span>}
                      </td>
                      {/* Technical screener score */}
                      <td className="font-mono font-bold">
                        <span className={
                          item.score >= 0.7
                            ? 'text-neo-bullish'
                            : item.score <= 0.3
                              ? 'text-neo-bearish'
                              : 'text-neo-warning'
                        }>
                          {(item.score * 100).toFixed(1)}%
                        </span>
                      </td>
                      <td className="font-mono">{item.passed_count}</td>
                      <td>
                        <div className="flex flex-wrap gap-1">
                          {top.map((c) => (
                            <span
                              key={c.key}
                              title={c.label}
                              className={`text-xs font-mono px-1 border ${
                                c.passed
                                  ? 'border-neo-bullish text-neo-bullish'
                                  : 'border-neo-muted text-neo-muted line-through'
                              }`}
                            >
                              {c.key}
                            </span>
                          ))}
                        </div>
                      </td>
                      <td>
                        <Link
                          href={`/stock/${item.ticker}`}
                          className="neo-button px-3 py-1 text-xs font-bold uppercase tracking-wider bg-neo-surface border-[2px] border-neo-stroke hover:bg-neo-primary hover:shadow-neo"
                        >
                          Detail →
                        </Link>
                      </td>
                    </tr>
                  );
                })}
                {filtered.length === 0 && !loading && (
                  <tr>
                    <td colSpan={8} className="text-center text-neo-muted py-8">
                      {t('noStrategies', lang)}
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
