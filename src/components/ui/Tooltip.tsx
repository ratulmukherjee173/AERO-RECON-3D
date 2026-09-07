import React from 'react';

interface TooltipProps {
  content: string;
  children: React.ReactNode;
  position?: 'top' | 'bottom' | 'left' | 'right';
}

export function Tooltip({ content, children, position = 'top' }: TooltipProps) {
  const posClasses = {
    top: 'bottom-full left-1/2 -translate-x-1/2 mb-2',
    bottom: 'top-full left-1/2 -translate-x-1/2 mt-2',
    left: 'right-full top-1/2 -translate-y-1/2 mr-2',
    right: 'left-full top-1/2 -translate-y-1/2 ml-2',
  };

  const arrowClasses = {
    top: 'top-full left-1/2 -translate-x-1/2 -mt-1 border-t-navy-700',
    bottom: 'bottom-full left-1/2 -translate-x-1/2 -mb-1 border-b-navy-700',
    left: 'left-full top-1/2 -translate-y-1/2 -ml-1 border-l-navy-700',
    right: 'right-full top-1/2 -translate-y-1/2 -mr-1 border-r-navy-700',
  };

  return (
    <div className="relative group inline-block">
      {children}
      <div className={`absolute z-50 hidden group-hover:block w-max max-w-xs ${posClasses[position]}`}>
        <div className="bg-navy-700 text-slate-200 text-xs px-2 py-1 rounded shadow-lg">
          {content}
        </div>
        <div className={`absolute border-4 border-transparent ${arrowClasses[position]}`}></div>
      </div>
    </div>
  );
}
