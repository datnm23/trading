'use client';

import { useTheme } from 'next-themes';
import { Moon, Sun } from 'lucide-react';
import { NeoButton } from '@/components/ui/NeoButton';

export function ThemeToggle() {
  const { theme, setTheme } = useTheme();

  return (
    <NeoButton
      variant="secondary"
      size="sm"
      onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
      className="p-2"
    >
      {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
    </NeoButton>
  );
}
