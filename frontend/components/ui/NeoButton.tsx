'use client';

import { cn } from '@/lib/utils';

interface NeoButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger';
  size?: 'sm' | 'md' | 'lg';
}

export function NeoButton({ 
  children, 
  className, 
  variant = 'primary',
  size = 'md',
  ...props 
}: NeoButtonProps) {
  const variantStyles = {
    primary: 'bg-neo-primary text-neo-stroke',
    secondary: 'bg-neo-surface text-neo-stroke',
    danger: 'bg-neo-bearish text-neo-stroke',
  };

  const sizeStyles = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-6 py-3 text-base',
    lg: 'px-8 py-4 text-lg',
  };

  return (
    <button
      className={cn(
        'neo-button',
        variantStyles[variant],
        sizeStyles[size],
        className
      )}
      {...props}
    >
      {children}
    </button>
  );
}
