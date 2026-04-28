'use client';

import { useState, useEffect } from 'react';
import { useLang } from '@/components/layout/LangProvider';
import { NeoCard } from '@/components/ui/NeoCard';
import { NeoMetric } from '@/components/ui/NeoMetric';
import { t } from '@/lib/i18n';
import { API_BASE_URL, apiHeaders } from '@/lib/api';
import { Award, Calendar, TrendingUp, TrendingDown, Zap, Trophy, AlertCircle } from 'lucide-react';

interface GraduationMetrics {
  days_traded: number;
  days_required: number;
  return_pct: number;
  max_drawdown_pct: number;
  sharpe: number;
  winrate: number;
  trade_count: number;
  total_pnl: number;
  gates: Record<string, boolean>;
  approved: boolean;
  message: string;
}

export default function GraduationPage() {
  const { lang } = useLang();
  const [metrics, setMetrics] = useState<GraduationMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/api/v1/graduation`, {
          headers: apiHeaders(),
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        setMetrics(data);
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Unknown error');
      } finally {
        setLoading(false);
      }
    };
    fetchMetrics();
    const interval = setInterval(fetchMetrics, 30000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="space-y-6">
        <h2 className="text-2xl font-black uppercase tracking-wider">{t('graduation', lang)}</h2>
        <NeoCard>
          <div className="text-center py-12 text-neo-muted font-bold animate-pulse">{t('loading', lang)}</div>
        </NeoCard>
      </div>
    );
  }

  if (error || !metrics) {
    return (
      <div className="space-y-6">
        <h2 className="text-2xl font-black uppercase tracking-wider">{t('graduation', lang)}</h2>
        <NeoCard>
          <div className="text-center py-12 text-neo-bearish font-bold">
            <AlertCircle size={48} className="mx-auto mb-4" />
            {error || 'Failed to load'}
          </div>
        </NeoCard>
      </div>
    );
  }

  const gates = [
    { key: 'days_traded', label: t('daysTraded', lang), value: `${metrics.days_traded}/${metrics.days_required}`, threshold: `${metrics.days_required} days`, pass: metrics.gates?.days_traded },
    { key: 'return_positive', label: t('returnPct', lang), value: `${metrics.return_pct >= 0 ? '+' : ''}${metrics.return_pct.toFixed(2)}%`, threshold: '> 0%', pass: metrics.gates?.return_positive },
    { key: 'drawdown', label: t('maxDrawdown', lang), value: `${metrics.max_drawdown_pct.toFixed(2)}%`, threshold: '< 10%', pass: metrics.gates?.drawdown },
    { key: 'sharpe', label: t('sharpeRatio', lang), value: metrics.sharpe.toFixed(3), threshold: '> 0.5', pass: metrics.gates?.sharpe },
    { key: 'winrate', label: t('winrate', lang), value: `${metrics.winrate.toFixed(1)}%`, threshold: '> 40%', pass: metrics.gates?.winrate },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-black uppercase tracking-wider">{t('graduation', lang)}</h2>
        {metrics.approved ? (
          <div className="flex items-center gap-2 bg-neo-bullish/20 px-4 py-2 border-2 border-neo-bullish">
            <Award size={20} className="text-neo-bullish" />
            <span className="text-sm font-black uppercase text-neo-bullish">{t('readyForLive', lang)}</span>
          </div>
        ) : (
          <div className="flex items-center gap-2 bg-neo-warning/20 px-4 py-2 border-2 border-neo-warning">
            <AlertCircle size={20} className="text-neo-warning" />
            <span className="text-sm font-black uppercase text-neo-warning">{t('paperTradingInProgress', lang)}</span>
          </div>
        )}
      </div>

      {/* Stats Row */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <NeoCard>
          <NeoMetric
            label={t('daysTraded', lang)}
            value={`${metrics.days_traded}/${metrics.days_required}`}
            variant={metrics.days_traded >= metrics.days_required ? 'bullish' : 'neutral'}
          />
        </NeoCard>
        <NeoCard>
          <NeoMetric
            label={t('totalPnL', lang)}
            value={`$${metrics.total_pnl.toLocaleString('en-US', { maximumFractionDigits: 2 })}`}
            variant={metrics.total_pnl >= 0 ? 'bullish' : 'bearish'}
          />
        </NeoCard>
        <NeoCard>
          <NeoMetric
            label={t('tradeCount', lang)}
            value={String(metrics.trade_count)}
            variant="neutral"
          />
        </NeoCard>
      </div>

      {/* Gates */}
      <NeoCard title={t('gates', lang)}>
        <div className="space-y-4">
          {gates.map((gate) => (
            <div key={gate.key} className="flex items-center justify-between py-3 border-b-2 border-neo-stroke last:border-0">
              <div className="flex items-center gap-3">
                {gate.pass ? (
                  <Trophy size={18} className="text-neo-bullish" />
                ) : (
                  <AlertCircle size={18} className="text-neo-warning" />
                )}
                <div>
                  <div className="font-bold text-sm">{gate.label}</div>
                  <div className="text-xs font-mono text-neo-muted">Threshold: {gate.threshold}</div>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <span className={`font-mono font-bold ${gate.pass ? 'text-neo-bullish' : 'text-neo-text'}`}>
                  {gate.value}
                </span>
                <span
                  className={`px-2 py-0.5 text-xs font-black uppercase border-2 ${
                    gate.pass
                      ? 'bg-neo-bullish/20 border-neo-bullish text-neo-bullish'
                      : 'bg-neo-warning/20 border-neo-warning text-neo-warning'
                  }`}
                >
                  {gate.pass ? t('approved', lang) : t('notApproved', lang)}
                </span>
              </div>
            </div>
          ))}
        </div>
      </NeoCard>

      {/* Message */}
      {metrics.days_traded === 0 && (
        <NeoCard>
          <div className="text-center py-8 text-neo-muted">
            <Calendar size={48} className="mx-auto mb-4" />
            <p className="font-bold uppercase">{t('noTradesYet', lang)}</p>
            <p className="text-sm mt-2">Start paper trading to track graduation progress.</p>
          </div>
        </NeoCard>
      )}
    </div>
  );
}
