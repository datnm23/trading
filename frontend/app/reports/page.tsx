'use client';

import { useLang } from '@/components/layout/LangProvider';
import { NeoCard } from '@/components/ui/NeoCard';
import { NeoMetric } from '@/components/ui/NeoMetric';
import { t } from '@/lib/i18n';
import { Calendar, TrendingUp } from 'lucide-react';

export default function ReportsPage() {
  const { lang } = useLang();

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-black uppercase tracking-wider">{t('dailyReports', lang)}</h2>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <NeoCard>
          <NeoMetric label={t('trades', lang)} value="0" variant="neutral" />
        </NeoCard>
        <NeoCard>
          <NeoMetric label={t('winrate', lang)} value="0%" variant="neutral" />
        </NeoCard>
        <NeoCard>
          <NeoMetric label={t('totalPnL', lang)} value="$0.00" variant="neutral" />
        </NeoCard>
        <NeoCard>
          <NeoMetric label={t('return', lang)} value="0.00%" variant="neutral" />
        </NeoCard>
      </div>

      <NeoCard title={t('dailyReports', lang)}>
        <div className="flex items-center gap-4 mb-6">
          <Calendar size={20} />
          <input
            type="date"
            className="border-[3px] border-neo-stroke px-4 py-2 bg-neo-surface font-mono"
          />
        </div>
        <div className="text-center py-12 text-neo-muted">
          <TrendingUp size={48} className="mx-auto mb-4" />
          <p className="font-bold uppercase">{t('noStrategyData', lang)}</p>
          <p className="text-sm mt-2">{t('startBotsHint', lang)}</p>
        </div>
      </NeoCard>
    </div>
  );
}
