import React from 'react';

interface CardProps {
  children: React.ReactNode;
  className?: string;
  padding?: 'none' | 'sm' | 'md' | 'lg';
  hover?: boolean;
}

export function Card({ children, className = '', padding = 'md', hover = false }: CardProps) {
  const paddingStyles = {
    none: 'p-0',
    sm: 'p-4',
    md: 'p-6',
    lg: 'p-8',
  };

  const hoverStyles = hover ? 'hover:border-navy-500 transition-colors duration-200' : '';

  return (
    <div className={`bg-navy-800 border border-navy-600/50 rounded-lg ${paddingStyles[padding]} ${hoverStyles} ${className}`}>
      {children}
    </div>
  );
}
