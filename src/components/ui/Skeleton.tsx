
interface SkeletonProps {
  variant?: 'text' | 'card' | 'stat' | 'avatar' | 'table-row';
  className?: string;
}

export function Skeleton({ variant = 'text', className = '' }: SkeletonProps) {
  const baseClass = 'animate-pulse bg-navy-700/50 rounded';
  
  const variants = {
    text: 'h-4 w-3/4',
    card: 'h-48 w-full rounded-lg',
    stat: 'h-32 w-full rounded-lg',
    avatar: 'h-10 w-10 rounded-full',
    'table-row': 'h-12 w-full',
  };

  return (
    <div className={`${baseClass} ${variants[variant]} ${className}`} />
  );
}
