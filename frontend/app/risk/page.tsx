'use client';

import { useLang } from '@/components/layout/LangProvider';
import { NeoCard } from '@/components/ui/NeoCard';
import { NeoMetric } from '@/components/ui/NeoMetric';
import { t } from '@/lib/i18n';
import { Shield, AlertTriangle, CheckCircle } from 'lucide-react';
import { NewsSentimentPanel } from '@/components/charts/NewsSentimentPanel';
import { MLDriftMonitor } from '@/components/charts/MLDriftMonitor';

export default function RiskPage() {
  const { lang } = useLang();

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-black uppercase tracking-wider">{t('riskMonitor', lang)}</h2>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <NeoCard>
          <div className="flex items-center gap-3 mb-4">
            <Shield size={24} className="text-neo-bullish" />
            <h3 className="text-lg font-bold uppercase">Trailing Stops</h3>
          </div>
          <div className="space-y-3">
            <div className="flex justify-between py-2 border-b-2 border-neo-stroke">
              <span className="text-neo-muted">{t('running', lang)}</span>
              <span className="font-mono font-bold">2</span>
            </div>
            <div className="flex justify-between py-2 border-b-2 border-neo-stroke">
              <span className="text-neo-muted">Hit Today</span>
              <span className="font-mono font-bold text-neo-bearish">0</span>
            </div>
          </div>
        </NeoCard>

        <NeoCard>
          <div className="flex items-center gap-3 mb-4">
            <AlertTriangle size={24} className="text-neo-primary" />
            <h3 className="text-lg font-bold uppercase">Partial Exits</h3>
          </div>
          <div className="space-y-3">
            <div className="flex justify-between py-2 border-b-2 border-neo-stroke">
              <span className="text-neo-muted">Triggered</span>
              <span className="font-mono font-bold">0</span>
            </div>
            <div className="flex justify-between py-2 border-b-2 border-neo-stroke">
              <span className="text-neo-muted">Profit Locked</span>
              <span className="font-mono font-bold text-neo-bullish">$0.00</span>
            </div>
          </div>
        </NeoCard>

        <NeoCard>
          <div className="flex items-center gap-3 mb-4">
            <CheckCircle size={24} className="text-neo-bullish" />
            <h3 className="text-lg font-bold uppercase">{t('correlationMatrix', lang)}</h3>
          </div>
          <div className="space-y-3">
            <div className="flex justify-between py-2 border-b-2 border-neo-stroke">
              <span className="text-neo-muted">Max Correlation</span>
              <span className="font-mono font-bold">0.00</span>
            </div>
            <div className="flex justify-between py-2 border-b-2 border-neo-stroke">
              <span className="text-neo-muted">Blocks Today</span>
              <span className="font-mono font-bold text-neo-bullish">0</span>
            </div>
          </div>
        </NeoCard>
      </div>

      {/* News Sentiment Panel */}
      <NewsSentimentPanel />

      {/* ML Drift Monitor */}
      <NeoCard title="ML Model Drift">
        <MLDriftMonitor />
      </NeoCard>
    </div>
  );
}
