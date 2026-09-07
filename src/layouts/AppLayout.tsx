import React, { useMemo } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import { Sidebar } from '../components/layout/Sidebar';
import { Header } from '../components/layout/Header';
import { MobileNav } from '../components/layout/MobileNav';
import { useIsMobile, useIsTablet, useIsDesktop, useSidebar } from '../hooks';
import { useSettings } from '../contexts/SettingsContext';

export const AppLayout: React.FC = () => {
  const isMobile = useIsMobile();
  const isTablet = useIsTablet();
  const isDesktop = useIsDesktop();
  const sidebar = useSidebar();
  const location = useLocation();

  const pageTitle = useMemo(() => {
    const path = location.pathname;
    if (path === '/' || path.startsWith('/dashboard')) return 'Dashboard';
    if (path.startsWith('/projects')) return 'Projects';
    if (path.startsWith('/reconstruction/new')) return 'New Reconstruction';
    if (path.startsWith('/processing')) return 'Processing Tasks';
    if (path.startsWith('/viewer')) return '3D Model Viewer';
    if (path.startsWith('/accuracy')) return 'Accuracy Analysis';
    if (path.startsWith('/reports')) return 'Reports';
    if (path.startsWith('/settings')) return 'Settings';
    return 'AERO RECON-3D';
  }, [location.pathname]);

  const { settings } = useSettings();
  const isCompact = !isMobile && (settings.compactSidebar || (isTablet && !isDesktop));

  let contentMarginClass = '';
  let mainPaddingClass = 'p-4 pt-20 pb-24 min-h-screen';

  if (!isMobile) {
    contentMarginClass = isCompact ? 'ml-[72px]' : 'ml-[260px]';
    mainPaddingClass = 'p-6 pt-22 min-h-screen';
  }

  return (
    <div className="min-h-screen bg-navy-900 text-slate-100 flex flex-col font-sans">
      <Sidebar isOpen={sidebar.isOpen} onClose={sidebar.close} />
      
      <div className={`flex flex-col flex-1 transition-all duration-300 ${contentMarginClass}`}>
        <Header onMenuClick={sidebar.toggle} pageTitle={pageTitle} />
        
        <main className={`flex-1 overflow-x-hidden ${mainPaddingClass}`}>
          <Outlet />
        </main>
      </div>
      
      {isMobile && <MobileNav />}
    </div>
  );
};
