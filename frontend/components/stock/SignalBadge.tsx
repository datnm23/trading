'use client';

/**
 * SignalBadge — single source-of-truth badge for unified signal actions.
 * Maps SignalAction → NeoBadge status + Vietnamese label.
 *
 * Usage:
 *   <SignalBadge action="BUY" />
 *   <SignalBadge action="INSUFFICIENT" size="sm" />
 */

import { TrendingUp, TrendingDown, Minus, AlertTriangle } from 'lucide-react';
import { NeoBadge } from '@/components/ui/NeoBadge';
import type { SignalAction } from '@/lib/api';

interface SignalBadgeProps {
  action: SignalAction | string;
  /** Additional className forwarded to NeoBadge */
  className?: string;
}

/** Maps action → NeoBadge status (colour) */
export function actionStatus(action: string): 'running' | 'halted' | 'paper' | 'warning' {
  switch (action) {
    case 'BUY': return 'running';   // green
    case 'SELL': return 'halted';   // red
    case 'HOLD': return 'paper';    // neutral/grey
    default: return 'warning';      // yellow — INSUFFICIENT or unknown
  }
}

/** Vietnamese label for each action */
export function actionLabel(action: string): string {
  switch (action) {
    case 'BUY': return 'MUA';
    case 'SELL': return 'BÁN';
    case 'HOLD': return 'NẮM GIỮ';
    case 'INSUFFICIENT': return 'CHƯA ĐỦ DỮ LIỆU';
    default: return action;
  }
}

function ActionIcon({ action }: { action: string }) {
  switch (action) {
    case 'BUY':
      return <TrendingUp size={14} className="inline mr-1 text-neo-bullish" />;
    case 'SELL':
      return <TrendingDown size={14} className="inline mr-1 text-neo-bearish" />;
    case 'INSUFFICIENT':
      return <AlertTriangle size={14} className="inline mr-1 text-neo-warning" />;
    default:
      return <Minus size={14} className="inline mr-1 text-neo-muted" />;
  }
}

export function SignalBadge({ action, className }: SignalBadgeProps) {
  return (
    <NeoBadge status={actionStatus(action)} className={className}>
      <ActionIcon action={action} />
      {actionLabel(action)}
    </NeoBadge>
  );
}
