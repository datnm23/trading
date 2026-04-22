'use client';

import { createContext, useContext, useState, useCallback, ReactNode, useEffect } from 'react';

export type Lang = 'vi' | 'en';

interface LangContextType {
  lang: Lang;
  setLang: (l: Lang) => void;
  toggleLang: () => void;
}

const LangContext = createContext<LangContextType>({
  lang: 'vi',
  setLang: () => {},
  toggleLang: () => {},
});

const STORAGE_KEY = 'trading-lang';

export function LangProvider({ children }: { children: ReactNode }) {
  const [lang, setLangState] = useState<Lang>('vi');
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored === 'vi' || stored === 'en') {
      setLangState(stored);
      document.documentElement.lang = stored;
    }
    setMounted(true);
  }, []);

  const setLang = useCallback((l: Lang) => {
    setLangState(l);
    localStorage.setItem(STORAGE_KEY, l);
    document.documentElement.lang = l;
  }, []);

  const toggleLang = useCallback(() => {
    const next = lang === 'vi' ? 'en' : 'vi';
    setLang(next);
  }, [lang, setLang]);

  return (
    <LangContext.Provider value={{ lang, setLang, toggleLang }}>
      {children}
    </LangContext.Provider>
  );
}

export function useLang() {
  return useContext(LangContext);
}
