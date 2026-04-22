'use client';

import { cn } from '@/lib/utils';

interface NeoBadgeProps {
  children: React.ReactNode;
  status?: 'running' | 'halted' | 'paper' | 'live' | 'warning';
  className?: string;
}

export function NeoBadge({ children, status = 'paper', className }: NeoBadgeProps) {
  return (
    <span className={cn('neo-badge', status, className)}>
      {children}
    </span>
  );
}
