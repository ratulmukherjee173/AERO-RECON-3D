import { X, CheckCircle, AlertCircle, Info, AlertTriangle } from 'lucide-react';

export type ToastType = 'success' | 'error' | 'info' | 'warning';

export interface ToastItem {
  id: string;
  message: string;
  type: ToastType;
  duration?: number;
}

interface ToastProps {
  toasts: ToastItem[];
  onRemove: (id: string) => void;
}

const typeStyles = {
  success: { border: 'border-l-green-500', icon: CheckCircle, iconColor: 'text-green-500' },
  error: { border: 'border-l-red-500', icon: AlertCircle, iconColor: 'text-red-500' },
  info: { border: 'border-l-blue-500', icon: Info, iconColor: 'text-blue-500' },
  warning: { border: 'border-l-amber-500', icon: AlertTriangle, iconColor: 'text-amber-500' },
};

export function Toast({ toasts, onRemove }: ToastProps) {
  return (
    <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2">
      {toasts.map((toast) => {
        const { border, icon: Icon, iconColor } = typeStyles[toast.type];
        
        return (
          <div 
            key={toast.id}
            className={`flex items-start gap-3 bg-navy-800 border border-navy-600/50 border-l-4 ${border} rounded-lg p-4 shadow-xl w-80 animate-in slide-in-from-right-full fade-in duration-300`}
          >
            <Icon className={`w-5 h-5 shrink-0 ${iconColor}`} />
            <p className="text-sm text-slate-200 flex-1">{toast.message}</p>
            <button 
              onClick={() => onRemove(toast.id)}
              className="text-slate-400 hover:text-slate-200 transition-colors shrink-0"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        );
      })}
    </div>
  );
}
