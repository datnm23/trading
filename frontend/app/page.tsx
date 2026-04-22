'use client';

import { useSocketIO } from '@/hooks/useSocketIO';
import { useLang } from '@/components/layout/LangProvider';
import { NeoCard } from '@/components/ui/NeoCard';
import { NeoMetric } from '@/components/ui/NeoMetric';
import { NeoBadge } from '@/components/ui/NeoBadge';
import { NeoButton } from '@/components/ui/NeoButton';
import { PortfolioRebalancer } from '@/components/charts/PortfolioRebalancer';
import { EquityCurveChart } from '@/components/charts/EquityCurveChart';
import { t } from '@/lib/i18n';
import { RefreshCw } from 'lucide-react';

export default function OverviewPage() {
  const { state, connected, reconnect } = useSocketIO();
  const { lang } = useLang();

  const strategies = state?.strategies || [];
  const totalEquity = strategies.reduce((sum, s) => sum + s.equity, 0);
  const avgReturn = strategies.length > 0
    ? strategies.reduce((sum, s) => sum + s.return_pct, 0) / strategies.length
    : 0;
  const totalPositions = strategies.reduce((sum, s) => sum + s.open_positions, 0);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-black uppercase tracking-wider">{t('overview', lang)}</h2>
        <div className="flex items-center gap-2">
          <NeoBadge status={connected ? 'running' : 'halted'}>
            {connected ? t('live', lang) : t('offline', lang)}
          </NeoBadge>
          <NeoButton size="sm" onClick={reconnect}>
            <RefreshCw size={14} className="mr-1" /> {t('refresh', lang)}
          </NeoButton>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <NeoCard>
          <NeoMetric
            label={t('totalEquity', lang)}
            value={totalEquity.toLocaleString('en-US', { minimumFractionDigits: 2 })}
            prefix="$"
            variant="neutral"
          />
        </NeoCard>
        <NeoCard>
          <NeoMetric
            label={t('avgReturn', lang)}
            value={`${(avgReturn * 100).toFixed(2)}%`}
            variant={avgReturn >= 0 ? 'bullish' : 'bearish'}
          />
        </NeoCard>
        <NeoCard>
          <NeoMetric
            label={t('openPositions', lang)}
            value={totalPositions}
            variant="neutral"
          />
        </NeoCard>
      </div>

      {/* Equity Curve */}
      <NeoCard title={t('equityCurves', lang)}>
        <EquityCurveChart data={state?.equity_history || []} />
      </NeoCard>

      {/* Portfolio Rebalancer */}
      <PortfolioRebalancer />

      {/* Strategies Table */}
      <NeoCard title={t('strategyPerformance', lang)}>
        <div className="overflow-x-auto">
          <table className="neo-table">
            <thead>
              <tr>
                <th>{t('strategy', lang)}</th>
                <th>{t('equity', lang)}</th>
                <th>{t('return', lang)}</th>
                <th>{t('positions', lang)}</th>
                <th>{t('status', lang)}</th>
              </tr>
            </thead>
            <tbody>
              {strategies.map((strategy) => (
                <tr key={strategy.name}>
                  <td className="font-bold">{strategy.name}</td>
                  <td className="font-mono">${strategy.equity.toLocaleString('en-US', { minimumFractionDigits: 2 })}</td>
                  <td className={strategy.return_pct >= 0 ? 'text-neo-bullish font-bold' : 'text-neo-bearish font-bold'}>
                    {strategy.return_pct >= 0 ? '+' : ''}{(strategy.return_pct * 100).toFixed(2)}%
                  </td>
                  <td className="font-mono">{strategy.open_positions}</td>
                  <td>
                    <NeoBadge status={strategy.running ? 'running' : 'halted'}>
                      {strategy.running ? t('running', lang) : t('stopped', lang)}
                    </NeoBadge>
                  </td>
                </tr>
              ))}
              {strategies.length === 0 && (
                <tr>
                  <td colSpan={5} className="text-center text-neo-muted py-8">
                    {t('noStrategies', lang)}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </NeoCard>

      {/* Last Update */}
      {state?.timestamp && (
        <div className="text-sm text-neo-muted font-mono">
          {t('lastUpdate', lang)}: {new Date(state.timestamp).toLocaleString()}
        </div>
      )}
    </div>
  );
}
