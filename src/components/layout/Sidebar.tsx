import React from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { LayoutDashboard, FolderKanban, PlusCircle, Cpu, Box, Target, FileText, Settings, X, LogOut } from 'lucide-react';
import { useIsMobile, useIsTablet, useIsDesktop } from '../../hooks';
import { useSettings } from '../../contexts/SettingsContext';
import { useAuth } from '../../contexts/AuthContext';
import { Logo } from '../shared/Logo';

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

const navItems = [
  { label: 'Dashboard', icon: LayoutDashboard, path: '/dashboard' },
  { label: 'Projects', icon: FolderKanban, path: '/projects' },
  { label: 'New Reconstruction', icon: PlusCircle, path: '/reconstruction/new' },
  { label: 'Processing', icon: Cpu, path: '/processing' },
  { label: '3D Models', icon: Box, path: '/viewer' },
  { label: 'Accuracy Analysis', icon: Target, path: '/accuracy' },
  { label: 'Reports', icon: FileText, path: '/reports' },
  { label: 'Settings', icon: Settings, path: '/settings' },
];

export const Sidebar: React.FC<SidebarProps> = ({ isOpen, onClose }) => {
  const location = useLocation();
  const navigate = useNavigate();
  const isMobile = useIsMobile();
  const isTablet = useIsTablet();
  const isDesktop = useIsDesktop();
  const { settings } = useSettings();
  
  const isCompact = !isMobile && (settings.compactSidebar || (isTablet && !isDesktop));

  const { logout } = useAuth();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const sidebarContent = (
    <div className="flex flex-col h-full bg-navy-950 border-r border-navy-600/30">
      <div className="px-5 py-5 flex items-center justify-between">
        {isCompact ? (
          <div className="w-full flex justify-center text-blue-500 font-bold text-xl">A</div>
        ) : (
          <Logo size="md" />
        )}
        {isMobile && (
          <button onClick={onClose} className="text-slate-400 hover:text-slate-100">
            <X className="w-6 h-6" />
          </button>
        )}
      </div>

      <nav className="flex-1 overflow-y-auto py-2">
        <ul className="space-y-1">
          {navItems.map((item) => {
            const isActive = location.pathname.startsWith(item.path) || (item.path === '/dashboard' && location.pathname === '/');
            const Icon = item.icon;
            
            return (
              <li key={item.path}>
                <Link
                  to={item.path}
                  onClick={() => {
                    if (isMobile) onClose();
                  }}
                  title={isCompact ? item.label : undefined}
                  className={`flex items-center gap-3 px-4 py-2.5 mx-3 rounded-lg transition-colors ${
                    isActive
                      ? 'bg-blue-600/10 text-blue-400 border-l-2 border-blue-500'
                      : 'text-sm text-slate-400 hover:text-slate-100 hover:bg-navy-800'
                  }`}
                >
                  <Icon className="w-5 h-5 shrink-0" />
                  {!isCompact && <span className="font-medium">{item.label}</span>}
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>

      <div className="border-t border-navy-600/30 p-4">
        <div className={`flex items-center ${isCompact ? 'justify-center' : 'gap-3'}`}>
          <div className="bg-blue-600 rounded-full w-9 h-9 flex items-center justify-center text-sm font-medium shrink-0 text-white">
            AS
          </div>
          {!isCompact && (
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-slate-100 truncate">Arjun Sharma</p>
              <p className="text-xs text-slate-400 truncate">Engineer</p>
            </div>
          )}
        </div>
        <button 
          onClick={handleLogout}
          title={isCompact ? 'Logout' : undefined}
          className={`mt-4 flex items-center gap-3 text-slate-400 hover:text-red-400 transition-colors w-full ${isCompact ? 'justify-center' : 'px-2'}`}
        >
          <LogOut className="w-5 h-5 shrink-0" />
          {!isCompact && <span className="text-sm font-medium">Logout</span>}
        </button>
      </div>
    </div>
  );

  if (isMobile) {
    return (
      <>
        {isOpen && (
          <div 
            className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm"
            onClick={onClose}
          />
        )}
        
        <div 
          className={`fixed inset-y-0 left-0 z-50 w-64 transform transition-transform duration-300 ease-in-out ${
            isOpen ? 'translate-x-0' : '-translate-x-full'
          }`}
        >
          {sidebarContent}
        </div>
      </>
    );
  }

  return (
    <aside className={`fixed left-0 top-0 bottom-0 z-40 ${isCompact ? 'w-[72px]' : 'w-[260px]'}`}>
      {sidebarContent}
    </aside>
  );
};
