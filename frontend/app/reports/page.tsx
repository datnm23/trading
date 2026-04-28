'use client';

import { useState, useEffect, useMemo } from 'react';
import { useTrades } from '@/hooks/useTrades';
import { useLang } from '@/components/layout/LangProvider';
import { NeoCard } from '@/components/ui/NeoCard';
import { NeoMetric } from '@/components/ui/NeoMetric';
import { t } from '@/lib/i18n';
import { API_BASE_URL } from '@/lib/api';
import { Calendar, TrendingUp, Download } from 'lucide-react';

export default function ReportsPage() {
  const { lang } = useLang();
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const { trades, loading } = useTrades({ limit: 1000 });

  // Filter by date range
  const filteredTrades = useMemo(() => {
    if (!startDate && !endDate) return trades;
    return trades.filter((t) => {
      const ts = new Date(t.timestamp);
      if (startDate && ts < new Date(startDate)) return false;
      if (endDate && ts > new Date(endDate + 'T23:59:59')) return false;
      return true;
    });
  }, [trades, startDate, endDate]);

  // Calculate stats
  const stats = useMemo(() => {
    const total = filteredTrades.length;
    if (total === 0) {
      return { total: 0, wins: 0, losses: 0, winrate: 0, totalPnl: 0, avgPnl: 0, returnPct: 0 };
    }
    const wins = filteredTrades.filter((t) => t.pnl > 0).length;
    const losses = filteredTrades.filter((t) => t.pnl < 0).length;
    const totalPnl = filteredTrades.reduce((sum, t) => sum + t.pnl, 0);
    return {
      total,
      wins,
      losses,
      winrate: wins / total,
      totalPnl,
      avgPnl: totalPnl / total,
      returnPct: filteredTrades.reduce((sum, t) => sum + (t.pnl_pct || 0), 0) / total,
    };
  }, [filteredTrades]);

  // Group by date
  const byDate = useMemo(() => {
    const map: Record<string, typeof trades> = {};
    for (const trade of filteredTrades) {
      const date = trade.timestamp?.split('T')[0] || 'unknown';
      if (!map[date]) map[date] = [];
      map[date].push(trade);
    }
    return Object.entries(map).sort((a, b) => b[0].localeCompare(a[0]));
  }, [filteredTrades]);

  const handleExport = () => {
    const params = new URLSearchParams();
    params.set('format', 'csv');
    if (startDate) params.set('start_date', startDate);
    if (endDate) params.set('end_date', endDate);
    window.open(`${API_BASE_URL}/api/v1/trades/export?${params}`, '_blank');
  };

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-black uppercase tracking-wider">{t('dailyReports', lang)}</h2>

      {/* Stats Row */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <NeoCard>
          <NeoMetric label={t('trades', lang)} value={stats.total} variant="neutral" />
        </NeoCard>
        <NeoCard>
          <NeoMetric
            label={t('winrate', lang)}
            value={`${(stats.winrate * 100).toFixed(1)}%`}
            variant={stats.winrate >= 0.5 ? 'bullish' : 'bearish'}
          />
        </NeoCard>
        <NeoCard>
          <NeoMetric
            label={t('totalPnL', lang)}
            value={stats.totalPnl.toFixed(2)}
            prefix="$"
            variant={stats.totalPnl >= 0 ? 'bullish' : 'bearish'}
          />
        </NeoCard>
        <NeoCard>
          <NeoMetric
            label={t('return', lang)}
            value={`${(stats.returnPct * 100).toFixed(2)}%`}
            variant={stats.returnPct >= 0 ? 'bullish' : 'bearish'}
          />
        </NeoCard>
      </div>

      {/* Date Filter + Export */}
      <NeoCard>
        <div className="flex flex-wrap items-center gap-4">
          <div className="flex items-center gap-2">
            <Calendar size={18} />
            <input
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              className="border-[3px] border-neo-stroke px-3 py-2 bg-neo-surface font-mono text-sm"
            />
            <span className="text-neo-muted">to</span>
            <input
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              className="border-[3px] border-neo-stroke px-3 py-2 bg-neo-surface font-mono text-sm"
            />
          </div>
          <button
            onClick={handleExport}
            className="flex items-center gap-2 px-4 py-2 bg-neo-accent text-white font-bold uppercase text-sm border-[3px] border-neo-stroke hover:opacity-80"
          >
            <Download size={16} />
            Export CSV
          </button>
          {loading && <span className="text-sm text-neo-muted">Loading...</span>}
        </div>
      </NeoCard>

      {/* Daily Breakdown */}
      <NeoCard title={`Trade History (${filteredTrades.length})`}>
        {byDate.length > 0 ? (
          <div className="space-y-4">
            {byDate.map(([date, dayTrades]) => {
              const dayPnl = dayTrades.reduce((s, t) => s + t.pnl, 0);
              const dayWins = dayTrades.filter((t) => t.pnl > 0).length;
              return (
                <div key={date} className="border-2 border-neo-stroke p-4">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-mono font-bold">{date}</span>
                    <span className={`font-mono font-bold ${dayPnl >= 0 ? 'text-neo-bullish' : 'text-neo-bearish'}`}>
                      {dayPnl >= 0 ? '+' : ''}${dayPnl.toFixed(2)} ({dayWins}/{dayTrades.length})
                    </span>
                  </div>
                  <div className="overflow-x-auto">
                    <table className="neo-table text-sm">
                      <thead>
                        <tr>
                          <th>Symbol</th>
                          <th>Side</th>
                          <th>P&L</th>
                          <th>Sub-Strat</th>
                          <th>Reason</th>
                        </tr>
                      </thead>
                      <tbody>
                        {dayTrades.map((trade, i) => (
                          <tr key={`${trade.id}-${i}`}>
                            <td className="font-mono">{trade.symbol}</td>
                            <td className={trade.side === 'long' || trade.side === 'buy' ? 'text-neo-bullish font-bold' : 'text-neo-bearish font-bold'}>
                              {trade.side?.toUpperCase()}
                            </td>
                            <td className={`font-mono ${trade.pnl >= 0 ? 'text-neo-bullish' : 'text-neo-bearish'}`}>
                              {trade.pnl >= 0 ? '+' : ''}${trade.pnl.toFixed(2)}
                            </td>
                            <td className="font-mono text-xs text-neo-accent">
                              {trade.sub_strategy || '-'}
                            </td>
                            <td className="text-xs font-mono uppercase">{trade.exit_reason}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <div className="text-center py-12 text-neo-muted">
            <TrendingUp size={48} className="mx-auto mb-4" />
            <p className="font-bold uppercase">{t('noStrategyData', lang)}</p>
            <p className="text-sm mt-2">{t('startBotsHint', lang)}</p>
          </div>
        )}
      </NeoCard>
    </div>
  );
}
