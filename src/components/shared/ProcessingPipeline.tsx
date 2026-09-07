import { Check, Loader2, Clock } from 'lucide-react';

export interface ProcessingStage {
  id: string;
  name: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress?: number;
}

interface ProcessingPipelineProps {
  stages: ProcessingStage[];
  className?: string;
}

export function ProcessingPipeline({ stages, className = '' }: ProcessingPipelineProps) {
  return (
    <div className={`space-y-4 ${className}`}>
      {stages.map((stage, index) => {
        const isLast = index === stages.length - 1;
        
        let icon = <Clock className="w-4 h-4 text-slate-400" />;
        let iconBg = 'bg-navy-700 border border-navy-600';
        let textClass = 'text-slate-400';
        
        if (stage.status === 'completed') {
          icon = <Check className="w-4 h-4 text-green-500" />;
          iconBg = 'bg-green-500/10 border border-green-500/30';
          textClass = 'text-slate-200';
        } else if (stage.status === 'processing') {
          icon = <Loader2 className="w-4 h-4 text-blue-500 animate-spin" />;
          iconBg = 'bg-blue-500/10 border border-blue-500/30';
          textClass = 'text-blue-400';
        } else if (stage.status === 'failed') {
          iconBg = 'bg-red-500/10 border border-red-500/30';
          textClass = 'text-red-400';
        }

        return (
          <div key={stage.id} className="relative flex items-start gap-4">
            {!isLast && (
              <div className="absolute left-4 top-8 bottom-[-1rem] w-px bg-navy-600/50" />
            )}
            
            <div className={`relative z-10 flex items-center justify-center w-8 h-8 rounded-full shrink-0 ${iconBg}`}>
              {stage.status === 'pending' && <span className="text-xs font-medium text-slate-400">{index + 1}</span>}
              {stage.status !== 'pending' && icon}
            </div>
            
            <div className="flex-1 min-w-0 pt-1">
              <div className="flex items-center justify-between mb-1">
                <span className={`text-sm font-medium ${textClass}`}>{stage.name}</span>
                {stage.progress !== undefined && stage.status === 'processing' && (
                  <span className="text-xs text-blue-400">{Math.round(stage.progress)}%</span>
                )}
              </div>
              
              {stage.status === 'processing' && stage.progress !== undefined && (
                <div className="w-full bg-navy-700 rounded-full h-1.5 mt-2">
                  <div 
                    className="bg-blue-500 h-1.5 rounded-full transition-all duration-300"
                    style={{ width: `${stage.progress}%` }}
                  />
                </div>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
