'use client';

import { useLang } from '@/components/layout/LangProvider';

export function LanguageToggle() {
  const { lang, toggleLang } = useLang();

  return (
    <button
      onClick={toggleLang}
      className="neo-button bg-neo-surface text-neo-stroke text-sm px-2 py-1 font-black uppercase tracking-wider"
      title={lang === 'vi' ? 'Switch to English' : 'Chuyển sang Tiếng Việt'}
    >
      {lang === 'vi' ? 'VI' : 'EN'}
    </button>
  );
}
