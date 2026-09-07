import React from 'react';
import type { LucideIcon } from 'lucide-react';
import { Loader2 } from 'lucide-react';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  icon?: LucideIcon;
  iconPosition?: 'left' | 'right';
  loading?: boolean;
  children: React.ReactNode;
}

const variantStyles = {
  primary: 'bg-blue-600 hover:bg-blue-500 text-white shadow-lg shadow-blue-600/20',
  secondary: 'bg-navy-700 hover:bg-navy-600 text-slate-200 border border-navy-600',
  outline: 'border border-blue-500/50 text-blue-400 hover:bg-blue-500/10',
  ghost: 'text-slate-300 hover:bg-navy-700 hover:text-slate-100',
  danger: 'bg-red-600/10 border border-red-500/30 text-red-400 hover:bg-red-600/20',
};

const sizeStyles = {
  sm: 'px-3 py-1.5 text-sm rounded-md gap-1.5',
  md: 'px-4 py-2.5 text-sm rounded-lg gap-2',
  lg: 'px-6 py-3 text-base rounded-lg gap-2',
};

export function Button({ variant = 'primary', size = 'md', icon: Icon, iconPosition = 'left', loading, children, className = '', disabled, ...props }: ButtonProps) {
  return (
    <button
      className={`inline-flex items-center justify-center font-medium transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed ${variantStyles[variant]} ${sizeStyles[size]} ${className}`}
      disabled={disabled || loading}
      {...props}
    >
      {loading && <Loader2 className="size-4 animate-spin" />}
      {!loading && Icon && iconPosition === 'left' && <Icon className="size-4" />}
      {children}
      {!loading && Icon && iconPosition === 'right' && <Icon className="size-4" />}
    </button>
  );
}
