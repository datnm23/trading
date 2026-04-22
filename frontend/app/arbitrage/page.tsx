'use client';

import { useLang } from '@/components/layout/LangProvider';
import { ArbitrageMonitor } from '@/components/charts/ArbitrageMonitor';
import { t } from '@/lib/i18n';

export default function ArbitragePage() {
  const { lang } = useLang();

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-black uppercase tracking-wider">{t('arbitrageOpportunities', lang)}</h2>
      <ArbitrageMonitor />
    </div>
  );
}
