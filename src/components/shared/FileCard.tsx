import { Film, CheckCircle } from 'lucide-react';
import { Card } from '../ui/Card';
import { ProgressBar } from '../ui/ProgressBar';

interface FileCardProps {
  name: string;
  size?: string;
  duration?: string;
  resolution?: string;
  progress?: number;
  status?: 'uploading' | 'completed' | 'processing' | 'failed';
  className?: string;
}

export function FileCard({ 
  name, 
  size, 
  duration, 
  resolution, 
  progress, 
  status = 'completed',
  className = ''
}: FileCardProps) {
  return (
    <Card padding="sm" className={`flex flex-col gap-3 ${className}`}>
      <div className="flex items-start gap-3">
        <div className="bg-blue-500/10 p-2 rounded-lg shrink-0">
          <Film className="w-5 h-5 text-blue-500" />
        </div>
        <div className="flex-1 min-w-0">
          <h4 className="text-sm font-medium text-slate-200 truncate" title={name}>
            {name}
          </h4>
          <div className="flex items-center gap-2 text-xs text-slate-400 mt-1">
            {size && <span>{size}</span>}
            {size && duration && <span>•</span>}
            {duration && <span>{duration}</span>}
            {resolution && (size || duration) && <span>•</span>}
            {resolution && <span>{resolution}</span>}
          </div>
        </div>
        {status === 'completed' && (
          <CheckCircle className="w-5 h-5 text-green-500 shrink-0" />
        )}
      </div>
      {status === 'uploading' && progress !== undefined && (
        <ProgressBar value={progress} size="sm" showLabel label="Uploading..." />
      )}
    </Card>
  );
}
