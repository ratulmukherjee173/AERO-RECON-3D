
interface StatusBadgeProps {
  status: string;
  className?: string;
}

export function StatusBadge({ status, className = '' }: StatusBadgeProps) {
  const normalizedStatus = status.toLowerCase();
  
  let color = 'bg-slate-500/10 text-slate-400 border-slate-500/20';
  let dotColor = 'bg-slate-400';

  if (['completed', 'ready', 'success'].includes(normalizedStatus)) {
    color = 'bg-green-500/10 text-green-500 border-green-500/20';
    dotColor = 'bg-green-500';
  } else if (['processing', 'generating', 'running', 'blue'].includes(normalizedStatus)) {
    color = 'bg-blue-500/10 text-blue-400 border-blue-500/20';
    dotColor = 'bg-blue-400';
  } else if (['failed', 'error'].includes(normalizedStatus)) {
    color = 'bg-red-500/10 text-red-400 border-red-500/20';
    dotColor = 'bg-red-500';
  } else if (['pending', 'waiting', 'warning'].includes(normalizedStatus)) {
    color = 'bg-amber-500/10 text-amber-400 border-amber-500/20';
    dotColor = 'bg-amber-500';
  }

  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border ${color} ${className}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${dotColor}`}></span>
      <span className="capitalize">{status}</span>
    </span>
  );
}
