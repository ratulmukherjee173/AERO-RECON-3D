
interface ProgressBarProps {
  value: number;
  size?: 'sm' | 'md';
  color?: 'blue' | 'cyan' | 'green' | 'amber' | 'red';
  showLabel?: boolean;
  label?: string;
  className?: string;
}

export function ProgressBar({ 
  value, 
  size = 'md', 
  color = 'blue', 
  showLabel = false, 
  label,
  className = ''
}: ProgressBarProps) {
  const boundedValue = Math.min(100, Math.max(0, value));
  
  const sizeClasses = {
    sm: 'h-1.5',
    md: 'h-2.5',
  };

  const colorClasses = {
    blue: 'bg-blue-500',
    cyan: 'bg-cyan-500',
    green: 'bg-green-500',
    amber: 'bg-amber-500',
    red: 'bg-red-500',
  };

  return (
    <div className={`w-full ${className}`}>
      {(showLabel || label) && (
        <div className="flex justify-between items-center mb-1.5 text-xs text-slate-400 font-medium">
          {label && <span>{label}</span>}
          {showLabel && <span>{Math.round(boundedValue)}%</span>}
        </div>
      )}
      <div className={`w-full bg-navy-700 rounded-full overflow-hidden ${sizeClasses[size]}`}>
        <div 
          className={`h-full rounded-full transition-all duration-500 ease-out ${colorClasses[color]}`}
          style={{ width: `${boundedValue}%` }}
        />
      </div>
    </div>
  );
}
