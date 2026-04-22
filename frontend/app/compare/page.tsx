'use client';

import { useSocketIO } from '@/hooks/useSocketIO';
import { useLang } from '@/components/layout/LangProvider';
import { NeoCard } from '@/components/ui/NeoCard';
import { NeoMetric } from '@/components/ui/NeoMetric';
import { PnLBarChart } from '@/components/charts/PnLBarChart';
import { t } from '@/lib/i18n';
import { TrendingUp, TrendingDown } from 'lucide-react';

export default function ComparePage() {
  const { state } = useSocketIO();
  const { lang } = useLang();
  const strategies = state?.strategies || [];

  const sorted = [...strategies].sort((a, b) => b.return_pct - a.return_pct);

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-black uppercase tracking-wider">{t('strategyComparison', lang)}</h2>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {sorted.map((strategy, index) => (
          <NeoCard key={strategy.name}>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-bold">{strategy.name}</h3>
              <span className="text-2xl font-black">
                {index === 0 ? '🥇' : index === 1 ? '🥈' : index === 2 ? '🥉' : ''}
              </span>
            </div>
            <div className="space-y-3">
              <NeoMetric
                label={t('equity', lang)}
                value={strategy.equity.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                prefix="$"
              />
              <NeoMetric
                label={t('return', lang)}
                value={`${(strategy.return_pct * 100).toFixed(2)}%`}
                variant={strategy.return_pct >= 0 ? 'bullish' : 'bearish'}
              />
              <div className="flex items-center gap-2 pt-2">
                {strategy.return_pct >= 0 ? (
                  <TrendingUp size={20} className="text-neo-bullish" />
                ) : (
                  <TrendingDown size={20} className="text-neo-bearish" />
                )}
                <span className="text-sm font-mono text-neo-muted">
                  {strategy.open_positions} {t('positions', lang).toLowerCase()}
                </span>
              </div>
            </div>
          </NeoCard>
        ))}
      </div>

      <NeoCard title={t('dailyPnL', lang)}>
        <PnLBarChart
          data={strategies.map((s) => ({
            strategy: s.name,
            pnl: s.daily_pnl ?? 0,
          }))}
        />
      </NeoCard>

      <NeoCard title={t('performanceRanking', lang)}>
        <div className="space-y-4">
          {sorted.map((strategy, index) => (
            <div key={strategy.name} className="flex items-center gap-4">
              <span className="text-2xl font-black w-8">{index + 1}</span>
              <div className="flex-1">
                <div className="flex justify-between mb-1">
                  <span className="font-bold">{strategy.name}</span>
                  <span className={strategy.return_pct >= 0 ? 'text-neo-bullish font-bold' : 'text-neo-bearish font-bold'}>
                    {strategy.return_pct >= 0 ? '+' : ''}{(strategy.return_pct * 100).toFixed(2)}%
                  </span>
                </div>
                <div className="h-4 bg-neo-bg border-2 border-neo-stroke relative">
                  <div
                    className={`h-full ${strategy.return_pct >= 0 ? 'bg-neo-bullish' : 'bg-neo-bearish'}`}
                    style={{ width: `${Math.min(Math.abs(strategy.return_pct) * 500, 100)}%` }}
                  />
                </div>
              </div>
            </div>
          ))}
          {sorted.length === 0 && (
            <p className="text-center text-neo-muted py-8">{t('noStrategyData', lang)}</p>
          )}
        </div>
      </NeoCard>
    </div>
  );
}
