'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';
import { useLang } from './LangProvider';
import { t, TranslationKey } from '@/lib/i18n';
import {
  LayoutDashboard,
  Activity,
  BarChart3,
  Shield,
  FileText,
  BookOpen,
  ArrowRightLeft,
  CandlestickChart,
  Award,
} from 'lucide-react';

const navItems: { href: string; key: TranslationKey; icon: typeof LayoutDashboard }[] = [
  { href: '/', key: 'overview', icon: LayoutDashboard },
  { href: '/live', key: 'liveStatus', icon: Activity },
  { href: '/market', key: 'market', icon: CandlestickChart },
  { href: '/compare', key: 'compare', icon: BarChart3 },
  { href: '/risk', key: 'risk', icon: Shield },
  { href: '/reports', key: 'reports', icon: FileText },
  { href: '/arbitrage', key: 'arbitrage', icon: ArrowRightLeft },
  { href: '/graduation', key: 'graduation', icon: Award },
  { href: '/wiki', key: 'wiki', icon: BookOpen },
];

export function Sidebar() {
  const pathname = usePathname();
  const { lang } = useLang();

  return (
    <aside className="w-64 border-r-[3px] border-neo-stroke bg-neo-surface min-h-screen">
      <nav className="p-4 space-y-2">
        {navItems.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                'flex items-center gap-3 px-4 py-3 border-[3px] font-bold uppercase tracking-wider text-sm transition-all',
                isActive
                  ? 'bg-neo-primary border-neo-stroke text-neo-stroke translate-x-1 shadow-neo'
                  : 'bg-transparent border-transparent text-neo-text hover:bg-neo-bg hover:border-neo-stroke hover:shadow-neo'
              )}
            >
              <item.icon size={18} />
              {t(item.key, lang)}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
