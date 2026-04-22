'use client';

import { cn } from '@/lib/utils';

interface NeoMetricProps {
  label: string;
  value: string | number;
  delta?: string | number;
  variant?: 'neutral' | 'bullish' | 'bearish';
  prefix?: string;
  suffix?: string;
}

export function NeoMetric({ 
  label, 
  value, 
  delta, 
  variant = 'neutral',
  prefix = '',
  suffix = '',
}: NeoMetricProps) {
  return (
    <div className={cn('neo-metric', variant)}>
      <div className="text-sm font-medium uppercase tracking-wider text-neo-muted mb-1">
        {label}
      </div>
      <div className="text-3xl font-black font-mono text-neo-text">
        {prefix}{value}{suffix}
      </div>
      {delta !== undefined && (
        <div className={cn(
          'text-sm font-bold font-mono mt-1',
          variant === 'bullish' && 'text-neo-bullish',
          variant === 'bearish' && 'text-neo-bearish',
          variant === 'neutral' && 'text-neo-muted',
        )}>
          {delta}
        </div>
      )}
    </div>
  );
}
