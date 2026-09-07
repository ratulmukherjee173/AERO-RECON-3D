// ============================================================
// AERO RECON-3D — Custom Hooks
// ============================================================

import { useState, useEffect, useCallback } from 'react';

/**
 * Media query hook for responsive design
 */
export function useMediaQuery(query: string): boolean {
  const [matches, setMatches] = useState(false);

  useEffect(() => {
    const media = window.matchMedia(query);
    setMatches(media.matches);

    const listener = (e: MediaQueryListEvent) => setMatches(e.matches);
    media.addEventListener('change', listener);
    return () => media.removeEventListener('change', listener);
  }, [query]);

  return matches;
}

/**
 * Convenient breakpoint hooks
 */
export function useIsMobile(): boolean {
  return !useMediaQuery('(min-width: 768px)');
}

export function useIsTablet(): boolean {
  const isMin768 = useMediaQuery('(min-width: 768px)');
  const isMax1279 = !useMediaQuery('(min-width: 1280px)');
  return isMin768 && isMax1279;
}

export function useIsDesktop(): boolean {
  return useMediaQuery('(min-width: 1280px)');
}

/**
 * Sidebar state management
 */
export function useSidebar() {
  const [isOpen, setIsOpen] = useState(false);
  const isMobile = useIsMobile();

  const toggle = useCallback(() => setIsOpen((prev) => !prev), []);
  const close = useCallback(() => setIsOpen(false), []);
  const open = useCallback(() => setIsOpen(true), []);

  // Auto-close on mobile when navigating
  useEffect(() => {
    if (!isMobile) {
      setIsOpen(false);
    }
  }, [isMobile]);

  return { isOpen, toggle, close, open };
}

/**
 * Toast notification system
 */
export interface Toast {
  id: string;
  message: string;
  type: 'success' | 'error' | 'info' | 'warning';
  duration?: number;
}

export function useToast() {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const addToast = useCallback(
    (message: string, type: Toast['type'] = 'info', duration = 4000) => {
      const id = Date.now().toString();
      setToasts((prev) => [...prev, { id, message, type, duration }]);
      if (duration > 0) {
        setTimeout(() => {
          setToasts((prev) => prev.filter((t) => t.id !== id));
        }, duration);
      }
    },
    []
  );

  const removeToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  return { toasts, addToast, removeToast };
}
