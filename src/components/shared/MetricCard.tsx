import type { LucideIcon } from 'lucide-react';
import { Card } from '../ui/Card';

interface MetricCardProps {
  label: string;
  value: string | number;
  unit: string;
  icon?: LucideIcon;
  description?: string;
  status?: 'good' | 'acceptable' | 'poor';
  className?: string;
}

export function MetricCard({ label, value, unit, icon: Icon, description, status, className = '' }: MetricCardProps) {
  const statusColors = {
    good: 'bg-green-500',
    acceptable: 'bg-amber-500',
    poor: 'bg-red-500',
  };

  return (
    <Card padding="md" className={className}>
      <div className="flex items-start justify-between mb-2">
        <span className="text-sm text-slate-400 font-medium">{label}</span>
        {Icon && <Icon className="w-4 h-4 text-slate-500" />}
      </div>
      <div className="flex items-baseline gap-1 mb-2">
        <span className="text-2xl font-bold text-slate-100">{value}</span>
        <span className="text-sm text-slate-400">{unit}</span>
      </div>
      {(description || status) && (
        <div className="flex items-center gap-2 mt-auto">
          {status && (
            <div className={`w-2 h-2 rounded-full ${statusColors[status]}`} />
          )}
          {description && (
            <span className="text-xs text-slate-400">{description}</span>
          )}
        </div>
      )}
    </Card>
  );
}
