// ============================================================
// AERO RECON-3D — Utility Functions
// ============================================================

/**
 * Format a date string to a localized display format
 */
export function formatDate(dateStr: string): string {
  const date = new Date(dateStr);
  return date.toLocaleDateString('en-IN', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}

/**
 * Format a number with commas for thousands separators
 */
export function formatNumber(num: number): string {
  return num.toLocaleString('en-IN');
}

/**
 * Get status color class based on project status
 */
export function getStatusColor(status: string): string {
  switch (status) {
    case 'completed':
      return 'bg-green-500/15 text-green-400 border-green-500/30';
    case 'processing':
      return 'bg-blue-500/15 text-blue-400 border-blue-500/30';
    case 'failed':
      return 'bg-red-500/15 text-red-400 border-red-500/30';
    case 'pending':
      return 'bg-amber-500/15 text-amber-400 border-amber-500/30';
    case 'ready':
      return 'bg-green-500/15 text-green-400 border-green-500/30';
    case 'generating':
      return 'bg-blue-500/15 text-blue-400 border-blue-500/30';
    default:
      return 'bg-slate-500/15 text-slate-400 border-slate-500/30';
  }
}

/**
 * Get status label
 */
export function getStatusLabel(status: string): string {
  return status.charAt(0).toUpperCase() + status.slice(1);
}

/**
 * Truncate text with ellipsis
 */
export function truncate(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength) + '…';
}

/**
 * Generate a CSS class string from conditions
 */
export function cn(...classes: (string | boolean | undefined | null)[]): string {
  return classes.filter(Boolean).join(' ');
}
