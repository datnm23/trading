'use client';

import { useSocketIO } from '@/hooks/useSocketIO';
import { useLang } from '@/components/layout/LangProvider';
import { NeoCard } from '@/components/ui/NeoCard';
import { NeoMetric } from '@/components/ui/NeoMetric';
import { NeoButton } from '@/components/ui/NeoButton';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';
import { useState, useMemo, useCallback } from 'react';
import { t } from '@/lib/i18n';
import { API_BASE_URL } from '@/lib/api';
import { RefreshCw } from 'lucide-react';

const COLORS = ['#FDC800', '#B9FF66', '#FF6B6B'];

export function PortfolioRebalancer() {
  const { state } = useSocketIO();
  const { lang } = useLang();
  const [rebalancing, setRebalancing] = useState(false);
  const [lastRebalanced, setLastRebalanced] = useState<string | null>(null);

  const strategies = state?.strategies || [];
  const totalEquity = strategies.reduce((sum, s) => sum + s.equity, 0);

  // Compute real allocations from strategy equity
  const allocations = useMemo(() => {
    if (strategies.length === 0 || totalEquity <= 0) return [];

    // Sort by performance (return_pct) descending
    const sorted = [...strategies].sort((a, b) => b.return_pct - a.return_pct);

    // Compute recommended weights using softmax over returns
    // Better performing strategies get higher allocation
    const returns = sorted.map((s) => Math.max(s.return_pct, -0.5));
    const expReturns = returns.map((r) => Math.exp(r * 20)); // scale factor
    const sumExp = expReturns.reduce((a, b) => a + b, 0);

    return sorted.map((s, i) => {
      const current = (s.equity / totalEquity) * 100;
      const recommended = (expReturns[i] / sumExp) * 100;
      return {
        strategy: s.name,
        current,
        recommended,
        performance: s.return_pct,
      };
    });
  }, [strategies, totalEquity]);

  const pieData = allocations.map((a) => ({
    name: a.strategy,
    value: a.current,
  }));

  const handleRebalance = useCallback(async () => {
    setRebalancing(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/rebalance`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          allocations: allocations.map((a) => ({
            strategy: a.strategy,
            weight: a.recommended / 100,
          })),
        }),
      });
      if (res.ok) {
        setLastRebalanced(new Date().toLocaleString());
      }
    } catch (e) {
      console.error('Rebalance failed:', e);
    } finally {
      setRebalancing(false);
    }
  }, [allocations]);

  if (allocations.length === 0) {
    return (
      <NeoCard title={t('capitalAllocation', lang)}>
        <p className="text-center text-neo-muted py-8">{t('noStrategies', lang)}</p>
      </NeoCard>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-xl font-black uppercase tracking-wider">{t('capitalAllocation', lang)}</h3>
        <NeoButton onClick={handleRebalance} size="sm" disabled={rebalancing}>
          <RefreshCw size={14} className={`mr-2 ${rebalancing ? 'animate-spin' : ''}`} />
          {rebalancing ? t('loading', lang) : t('rebalance', lang)}
        </NeoButton>
      </div>

      {lastRebalanced && (
        <div className="text-xs text-neo-muted font-mono">
          {t('lastUpdate', lang)}: {lastRebalanced}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <NeoCard title={t('currentAllocation', lang)}>
          <div className="h-[250px]">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={100}
                  stroke="#000"
                  strokeWidth={3}
                  dataKey="value"
                >
                  {pieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    background: '#fff',
                    border: '3px solid #000',
                    boxShadow: '4px 4px 0 #000',
                    fontFamily: 'JetBrains Mono',
                  }}
                  formatter={(value: any) => [`${Number(value).toFixed(1)}%`, '']}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </NeoCard>

        <NeoCard title={t('strategyWeights', lang)}>
          <div className="space-y-4">
            {allocations.map((alloc) => (
              <div key={alloc.strategy} className="space-y-2">
                <div className="flex justify-between">
                  <span className="font-bold">{alloc.strategy}</span>
                  <span className="font-mono font-bold">{alloc.current.toFixed(1)}%</span>
                </div>
                <div className="h-6 bg-neo-bg border-2 border-neo-stroke relative">
                  <div
                    className="h-full bg-neo-primary transition-all"
                    style={{ width: `${Math.min(alloc.current, 100)}%` }}
                  />
                  <div
                    className="absolute top-0 h-full border-r-2 border-dashed border-neo-stroke"
                    style={{ left: `${Math.min(alloc.recommended, 100)}%` }}
                  />
                </div>
                <div className="flex justify-between text-xs">
                  <span className="text-neo-muted">{t('recommended', lang)}: {alloc.recommended.toFixed(1)}%</span>
                  <span className={alloc.performance >= 0 ? 'text-neo-bullish' : 'text-neo-bearish'}>
                    {alloc.performance >= 0 ? '+' : ''}{(alloc.performance * 100).toFixed(2)}%
                  </span>
                </div>
              </div>
            ))}
          </div>
        </NeoCard>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {allocations.map((alloc) => (
          <NeoCard key={alloc.strategy}>
            <NeoMetric
              label={alloc.strategy}
              value={`${alloc.current.toFixed(1)}%`}
              delta={Math.abs(alloc.current - alloc.recommended) < 1
                ? t('balanced', lang)
                : `→ ${alloc.recommended.toFixed(1)}%`}
              variant={alloc.performance >= 0 ? 'bullish' : 'bearish'}
            />
          </NeoCard>
        ))}
      </div>
    </div>
  );
}
