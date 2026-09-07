import type { LucideIcon } from 'lucide-react';
import { Card } from './Card';

interface StatCardProps {
  label: string;
  value: string | number;
  icon: LucideIcon;
  change?: number;
  trend?: 'up' | 'down' | 'neutral';
  className?: string;
}

export function StatCard({ label, value, icon: Icon, change, trend = 'neutral', className = '' }: StatCardProps) {
  return (
    <Card className={`flex flex-col ${className}`} padding="md" hover>
      <div className="flex items-center justify-between mb-4">
        <span className="text-sm text-slate-400 font-medium">{label}</span>
        <div className="bg-blue-500/10 rounded-lg p-3">
          <Icon className="w-5 h-5 text-blue-500" />
        </div>
      </div>
      <div className="flex items-end justify-between">
        <span className="text-2xl font-bold text-slate-100">{value}</span>
        {change !== undefined && (
          <span className={`text-sm font-medium ${trend === 'up' || change > 0 ? 'text-green-500' : trend === 'down' || change < 0 ? 'text-red-500' : 'text-slate-400'}`}>
            {change > 0 ? '+' : ''}{change}
          </span>
        )}
      </div>
    </Card>
  );
}
