'use client';

import { useMemo, useState } from 'react';
import { useSocketIO } from '@/hooks/useSocketIO';
import { useTrades, Trade } from '@/hooks/useTrades';
import { useLang } from '@/components/layout/LangProvider';
import { NeoCard } from '@/components/ui/NeoCard';
import { NeoMetric } from '@/components/ui/NeoMetric';
import { NeoBadge } from '@/components/ui/NeoBadge';
import { t } from '@/lib/i18n';
import { Activity, TrendingUp, TrendingDown, ArrowUpDown } from 'lucide-react';

function RegimeBadge({ regime }: { regime: string }) {
  const colorMap: Record<string, string> = {
    trending: 'text-neo-bullish',
    ranging: 'text-neo-warning',
    neutral: 'text-neo-muted',
    bull: 'text-neo-bullish',
    bear: 'text-neo-bearish',
  };
  return (
    <span className={`font-bold uppercase text-sm ${colorMap[regime] || 'text-neo-muted'}`}>
      {regime}
    </span>
  );
}

function calculateDuration(entryTime: string | null): string {
  if (!entryTime) return '-';
  const diff = Date.now() - new Date(entryTime).getTime();
  const hours = Math.floor(diff / 3600000);
  const mins = Math.floor((diff % 3600000) / 60000);
  if (hours < 24) return `${hours}h ${mins}m`;
  const days = Math.floor(hours / 24);
  const remHours = hours % 24;
  return remHours ? `${days}d ${remHours}h` : `${days}d`;
}

const SUB_STRATEGY_LABELS: Record<string, string> = {
  ema: 'EMA-Trend',
  breakout: 'Breakout',
  grid: 'Grid',
};

const TABLE_COLUMNS = [
  { key: 'symbol', label: 'Symbol' },
  { key: 'side', label: 'Side' },
  { key: 'entry_price', label: 'Entry' },
  { key: 'exit_price', label: 'Exit' },
  { key: 'size', label: 'Size' },
  { key: 'pnl', label: 'P&L' },
  { key: 'pnl_pct', label: 'P&L%' },
  { key: 'stop_price', label: 'Stop' },
  { key: 'target_price', label: 'Target' },
  { key: 'duration', label: 'Duration' },
  { key: 'exit_reason', label: 'Reason' },
  { key: 'sub_strategy', label: 'Sub-Strat' },
  { key: 'wiki_action', label: 'Wiki' },
  { key: 'regime', label: 'Regime' },
];

export default function LivePage() {
  const { state, connected } = useSocketIO();
  const { trades: closedTrades, loading: tradesLoading } = useTrades({ limit: 50 });
  const { lang } = useLang();

  const strategies = state?.strategies || [];
  const positions = state?.positions || [];
  const subStrategies = strategies.filter((s: any) => s.meta);
  const displayStrategies = subStrategies.length > 0 ? subStrategies : strategies;
  const subStrategy = state?.sub_strategy;
  const currentRegime = state?.current_regime || 'unknown';
  const directionalRegime = state?.directional_regime || 'unknown';
  const regimeDistribution = state?.regime_distribution || {};

  // Sort & filter state
  const [sortField, setSortField] = useState<string>('timestamp');
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc');
  const [filterSubStrategy, setFilterSubStrategy] = useState<string>('');

  // Merge open positions + closed trades
  const allTrades = useMemo(() => {
    const openTrades: Trade[] = positions.map((pos: any) => ({
      id: `open-${pos.symbol}`,
      timestamp: pos.entry_time || new Date().toISOString(),
      symbol: pos.symbol,
      side: pos.side,
      entry_price: pos.entry_price,
      exit_price: null,
      size: pos.size,
      pnl: pos.unrealized_pnl || 0,
      pnl_pct: 0,
      duration: calculateDuration(pos.entry_time),
      exit_reason: 'Open',
      stop_price: pos.stop_price || null,
      target_price: null,
      sub_strategy: pos.meta?.ensemble_source || null,
      wiki_alignment: pos.meta?.wiki_alignment || null,
      wiki_action: null,
      regime: pos.meta?.regime || null,
      directional_regime: pos.meta?.directional_regime || null,
      status: 'open',
    }));
    return [...openTrades, ...closedTrades];
  }, [positions, closedTrades]);

  // Filter + sort
  const sortedTrades = useMemo(() => {
    let filtered = allTrades;
    if (filterSubStrategy) {
      filtered = filtered.filter((t) => t.sub_strategy === filterSubStrategy);
    }
    return filtered.sort((a, b) => {
      const aVal = (a as any)[sortField];
      const bVal = (b as any)[sortField];
      if (aVal === null || aVal === undefined) return 1;
      if (bVal === null || bVal === undefined) return -1;
      const cmp = aVal > bVal ? 1 : aVal < bVal ? -1 : 0;
      return sortDir === 'asc' ? cmp : -cmp;
    });
  }, [allTrades, filterSubStrategy, sortField, sortDir]);

  const toggleSort = (field: string) => {
    if (sortField === field) {
      setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortField(field);
      setSortDir('desc');
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-black uppercase tracking-wider">{t('liveStatusTitle', lang)}</h2>
        <NeoBadge status={connected ? 'running' : 'halted'}>
          {connected ? t('connected', lang) : t('disconnected', lang)}
        </NeoBadge>
      </div>

      {/* Regime Overview Bar */}
      <NeoCard>
        <div className="flex flex-wrap items-center gap-6">
          <div>
            <span className="text-xs font-bold uppercase text-neo-muted">Regime</span>
            <div className="mt-1"><RegimeBadge regime={currentRegime} /></div>
          </div>
          <div>
            <span className="text-xs font-bold uppercase text-neo-muted">Directional</span>
            <div className="mt-1"><RegimeBadge regime={directionalRegime} /></div>
          </div>
          <div>
            <span className="text-xs font-bold uppercase text-neo-muted">Wiki</span>
            <div className={`mt-1 font-mono font-bold ${subStrategy?.wiki_alignment && subStrategy.wiki_alignment >= 0.3 ? 'text-neo-bullish' : 'text-neo-muted'}`}>
              {subStrategy?.wiki_alignment !== undefined ? `${(subStrategy.wiki_alignment * 100).toFixed(0)}%` : 'N/A'}
            </div>
          </div>
          <div>
            <span className="text-xs font-bold uppercase text-neo-muted">Decision</span>
            <div className="mt-1 font-mono text-sm">{subStrategy?.final_decision || 'N/A'}</div>
          </div>
          {Object.keys(regimeDistribution).length > 0 && (
            <div className="ml-auto">
              <span className="text-xs font-bold uppercase text-neo-muted">History</span>
              <div className="mt-1 flex gap-2">
                {Object.entries(regimeDistribution).map(([regime, pct]) => (
                  <span key={regime} className="text-xs font-mono">
                    {regime}: {(pct as number * 100).toFixed(0)}%
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      </NeoCard>

      {/* Sub-Strategy Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {displayStrategies.map((strategy: any) => {
          const meta = strategy.meta || {};
          const isActive = meta.is_active_regime;
          const signal = meta.active_signal;
          const reasons = meta.rejection_reasons || [];
          return (
            <NeoCard key={strategy.name} title={strategy.name}>
              <div className="space-y-4">
                <NeoMetric
                  label={t('equity', lang)}
                  value={strategy.equity.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                  prefix="$"
                  variant={strategy.return_pct >= 0 ? 'bullish' : 'bearish'}
                />
                <NeoMetric
                  label={t('return', lang)}
                  value={`${(strategy.return_pct * 100).toFixed(2)}%`}
                  variant={strategy.return_pct >= 0 ? 'bullish' : 'bearish'}
                />
                <NeoMetric
                  label={t('positions', lang)}
                  value={strategy.open_positions}
                  variant="neutral"
                />
                <div className="flex items-center gap-2 mt-4">
                  <Activity size={16} className={strategy.running ? 'text-neo-bullish' : 'text-neo-bearish'} />
                  <span className="text-sm font-bold uppercase">
                    {strategy.running ? t('running', lang) : t('stopped', lang)}
                  </span>
                  {isActive && <span className="text-neo-bullish font-bold text-xs ml-auto">ACTIVE</span>}
                  <span className="text-sm text-neo-muted font-mono ml-auto">
                    {strategy.mode === 'paper' ? t('paper', lang) : strategy.mode}
                  </span>
                </div>
                <div className="pt-3 border-t-2 border-neo-stroke">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold uppercase text-neo-muted">Signal</span>
                    {signal ? (
                      <span className={`font-bold text-sm ${signal === 'buy' ? 'text-neo-bullish' : 'text-neo-bearish'}`}>
                        {signal.toUpperCase()}
                      </span>
                    ) : (
                      <span className="text-sm text-neo-muted">No signal</span>
                    )}
                  </div>
                  {reasons.length > 0 && (
                    <div className="mt-2 space-y-1">
                      {reasons.slice(0, 2).map((r: string, i: number) => (
                        <div key={i} className="text-xs font-mono text-neo-muted truncate" title={r}>
                          • {r}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </NeoCard>
          );
        })}
      </div>

      {/* Trade History */}
      <NeoCard title={`Trade History (${sortedTrades.length})`}>
        {/* Filter */}
        <div className="mb-4 flex items-center gap-3">
          <label className="text-xs font-bold uppercase text-neo-muted">Filter:</label>
          <select
            value={filterSubStrategy}
            onChange={(e) => setFilterSubStrategy(e.target.value)}
            className="bg-transparent border-2 border-neo-stroke rounded px-3 py-1 text-sm font-mono focus:outline-none focus:border-neo-accent"
          >
            <option value="">All Sub-Strategies</option>
            <option value="ema">EMA-Trend</option>
            <option value="breakout">Monthly-Breakout</option>
            <option value="grid">Grid-MeanReversion</option>
          </select>
          {tradesLoading && <span className="text-xs text-neo-muted">Loading...</span>}
        </div>

        <div className="overflow-x-auto">
          <table className="neo-table">
            <thead>
              <tr>
                {TABLE_COLUMNS.map((col) => (
                  <th
                    key={col.key}
                    onClick={() => toggleSort(col.key)}
                    className="cursor-pointer select-none hover:text-neo-accent whitespace-nowrap"
                  >
                    <span className="flex items-center gap-1">
                      {col.label}
                      <ArrowUpDown size={12} className={sortField === col.key ? 'text-neo-accent' : 'text-neo-muted opacity-50'} />
                    </span>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {sortedTrades.map((trade) => (
                <tr
                  key={trade.id}
                  className={trade.status === 'open' ? 'bg-neo-warning/10' : ''}
                >
                  <td className="font-mono font-bold whitespace-nowrap">
                    {trade.symbol}
                    {trade.status === 'open' && (
                      <span className="ml-1 text-xs text-neo-warning font-bold">●OPEN</span>
                    )}
                  </td>
                  <td>
                    <span className={trade.side === 'long' || trade.side === 'buy' ? 'text-neo-bullish font-bold' : 'text-neo-bearish font-bold'}>
                      {trade.side.toUpperCase()}
                    </span>
                  </td>
                  <td className="font-mono">${trade.entry_price.toLocaleString()}</td>
                  <td className="font-mono">
                    {trade.exit_price !== null && trade.exit_price !== undefined
                      ? `$${trade.exit_price.toLocaleString()}`
                      : <span className="text-neo-warning">—</span>}
                  </td>
                  <td className="font-mono">{trade.size.toFixed(4)}</td>
                  <td className={`font-mono ${trade.pnl >= 0 ? 'text-neo-bullish' : 'text-neo-bearish'}`}>
                    {trade.pnl >= 0 ? '+' : ''}${trade.pnl.toFixed(2)}
                  </td>
                  <td className={`font-mono ${trade.pnl_pct >= 0 ? 'text-neo-bullish' : 'text-neo-bearish'}`}>
                    {trade.pnl_pct >= 0 ? '+' : ''}{(trade.pnl_pct * 100).toFixed(2)}%
                  </td>
                  <td className="font-mono text-neo-muted">
                    {trade.stop_price ? `$${trade.stop_price.toLocaleString()}` : '—'}
                  </td>
                  <td className="font-mono text-neo-muted">
                    {trade.target_price ? `$${trade.target_price.toLocaleString()}` : '—'}
                  </td>
                  <td className="font-mono text-neo-muted">{trade.duration || '—'}</td>
                  <td className="text-xs font-mono uppercase">{trade.exit_reason}</td>
                  <td>
                    {trade.sub_strategy ? (
                      <span className="font-bold text-xs uppercase text-neo-accent">
                        {SUB_STRATEGY_LABELS[trade.sub_strategy] || trade.sub_strategy}
                      </span>
                    ) : (
                      <span className="text-neo-muted">—</span>
                    )}
                  </td>
                  <td>
                    {trade.wiki_action ? (
                      <span className={`text-xs font-mono ${trade.wiki_alignment && trade.wiki_alignment >= 0.3 ? 'text-neo-bullish' : 'text-neo-bearish'}`}>
                        {trade.wiki_action} ({(trade.wiki_alignment || 0).toFixed(2)})
                      </span>
                    ) : (
                      <span className="text-neo-muted">—</span>
                    )}
                  </td>
                  <td>
                    {trade.regime ? (
                      <span className={`text-xs font-bold uppercase ${trade.regime === 'trending' ? 'text-neo-bullish' : trade.regime === 'ranging' ? 'text-neo-warning' : 'text-neo-muted'}`}>
                        {trade.regime}
                      </span>
                    ) : (
                      <span className="text-neo-muted">—</span>
                    )}
                  </td>
                </tr>
              ))}
              {sortedTrades.length === 0 && (
                <tr>
                  <td colSpan={TABLE_COLUMNS.length} className="text-center text-neo-muted py-8">
                    No trades available
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </NeoCard>

      {displayStrategies.length === 0 && (
        <NeoCard>
          <div className="text-center py-12">
            <Activity size={48} className="mx-auto text-neo-muted mb-4" />
            <p className="text-neo-muted font-bold uppercase">{t('noActiveStrategies', lang)}</p>
            <p className="text-sm text-neo-muted mt-2">{t('startBotsHint', lang)}</p>
          </div>
        </NeoCard>
      )}
    </div>
  );
}
