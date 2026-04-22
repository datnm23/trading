'use client';

import { useSocketIO } from '@/hooks/useSocketIO';
import { useLang } from './LangProvider';
import { ThemeToggle } from './ThemeToggle';
import { LanguageToggle } from './LanguageToggle';
import { t } from '@/lib/i18n';
import { Activity } from 'lucide-react';

export function Header() {
  const { connected } = useSocketIO();
  const { lang } = useLang();

  return (
    <header className="border-b-[3px] border-neo-stroke bg-neo-surface">
      <div className="flex items-center justify-between px-6 py-4">
        <div className="flex items-center gap-3">
          <div className="w-3 h-3 bg-neo-primary border-2 border-neo-stroke" />
          <h1 className="text-xl font-black uppercase tracking-wider">
            Hybrid Trading
          </h1>
        </div>
        
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <Activity size={16} className={connected ? 'text-neo-bullish' : 'text-neo-bearish'} />
            <span className="text-sm font-bold font-mono uppercase">
              {connected ? t('connected', lang) : t('disconnected', lang)}
            </span>
          </div>
          <LanguageToggle />
          <ThemeToggle />
        </div>
      </div>
    </header>
  );
}
