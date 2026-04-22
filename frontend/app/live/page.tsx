'use client';

import { useSocketIO } from '@/hooks/useSocketIO';
import { useLang } from '@/components/layout/LangProvider';
import { NeoCard } from '@/components/ui/NeoCard';
import { NeoMetric } from '@/components/ui/NeoMetric';
import { NeoBadge } from '@/components/ui/NeoBadge';
import { t } from '@/lib/i18n';
import { Activity, TrendingUp, TrendingDown } from 'lucide-react';

export default function LivePage() {
  const { state, connected } = useSocketIO();
  const { lang } = useLang();
  const strategies = state?.strategies || [];
  const positions = state?.positions || [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-black uppercase tracking-wider">{t('liveStatusTitle', lang)}</h2>
        <NeoBadge status={connected ? 'running' : 'halted'}>
          {connected ? t('connected', lang) : t('disconnected', lang)}
        </NeoBadge>
      </div>

      {/* Strategy Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {strategies.map((strategy) => (
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
                <span className="text-sm text-neo-muted font-mono ml-auto">
                  {strategy.mode === 'paper' ? t('paper', lang) : strategy.mode}
                </span>
              </div>
            </div>
          </NeoCard>
        ))}
      </div>

      {/* Positions Table */}
      {positions.length > 0 && (
        <NeoCard title={`${t('positions', lang)} (${positions.length})`}>
          <div className="overflow-x-auto">
            <table className="neo-table">
              <thead>
                <tr>
                  <th>{t('strategy', lang)}</th>
                  <th>Symbol</th>
                  <th>Side</th>
                  <th>Entry</th>
                  <th>Size</th>
                  <th>Current</th>
                  <th>Unrealized P&L</th>
                </tr>
              </thead>
              <tbody>
                {positions.map((pos, i) => (
                  <tr key={`${pos.symbol}-${pos.side}-${i}`}>
                    <td className="font-bold">{pos.strategy}</td>
                    <td className="font-mono">{pos.symbol}</td>
                    <td>
                      <span className={pos.side === 'long' || pos.side === 'buy' ? 'text-neo-bullish font-bold' : 'text-neo-bearish font-bold'}>
                        {pos.side.toUpperCase()}
                      </span>
                    </td>
                    <td className="font-mono">${pos.entry_price?.toLocaleString()}</td>
                    <td className="font-mono">{pos.size?.toFixed(6)}</td>
                    <td className="font-mono">{pos.current_price ? `$${pos.current_price.toLocaleString()}` : '-'}</td>
                    <td className="font-mono">
                      {pos.unrealized_pnl !== null && pos.unrealized_pnl !== undefined ? (
                        <span className={pos.unrealized_pnl >= 0 ? 'text-neo-bullish' : 'text-neo-bearish'}>
                          {pos.unrealized_pnl >= 0 ? <TrendingUp size={14} className="inline mr-1" /> : <TrendingDown size={14} className="inline mr-1" />}
                          ${pos.unrealized_pnl.toFixed(2)}
                        </span>
                      ) : '-'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </NeoCard>
      )}

      {strategies.length === 0 && (
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
