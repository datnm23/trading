'use client';

import { cn } from '@/lib/utils';

interface NeoCardProps {
  children: React.ReactNode;
  className?: string;
  title?: string;
  titleClassName?: string;
  onClick?: () => void;
}

export function NeoCard({ children, className, title, titleClassName, onClick }: NeoCardProps) {
  return (
    <div
      className={cn('neo-card p-6', className)}
      onClick={onClick}
      role={onClick ? 'button' : undefined}
      tabIndex={onClick ? 0 : undefined}
    >
      {title && (
        <h3 className={cn('text-lg font-bold uppercase tracking-wider mb-4 border-b-2 border-neo-stroke pb-2', titleClassName)}>
          {title}
        </h3>
      )}
      {children}
    </div>
  );
}
