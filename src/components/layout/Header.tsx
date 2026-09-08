import React, { useState, useEffect, useRef } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Menu, Search, Bell, User, Settings as SettingsIcon, LogOut, LogIn } from 'lucide-react';
import { mockNotifications } from '../../data/mock';
import { Logo } from '../shared/Logo';
import { useSettings } from '../../contexts/SettingsContext';
import { useIsMobile, useIsTablet, useIsDesktop } from '../../hooks';
import { useAuth } from '../../contexts/AuthContext';

interface HeaderProps {
  onMenuClick: () => void;
  pageTitle: string;
}

export const Header: React.FC<HeaderProps> = ({ onMenuClick, pageTitle }) => {

  const [showNotifications, setShowNotifications] = useState(false);
  const [showProfile, setShowProfile] = useState(false);
  const { settings } = useSettings();
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const isMobile = useIsMobile();
  const isTablet = useIsTablet();
  const isDesktop = useIsDesktop();

  const isCompact = !isMobile && (settings.compactSidebar || (isTablet && !isDesktop));
  
  const notifRef = useRef<HTMLDivElement>(null);
  const profileRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (notifRef.current && !notifRef.current.contains(event.target as Node)) {
        setShowNotifications(false);
      }
      if (profileRef.current && !profileRef.current.contains(event.target as Node)) {
        setShowProfile(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleLogout = () => {
    logout();
    setShowProfile(false);
    navigate('/dashboard');
  };

  return (
    <header className={`fixed top-0 right-0 left-0 ${!isMobile ? (isCompact ? 'left-[72px]' : 'left-[260px]') : ''} bg-navy-950/80 backdrop-blur-md border-b border-navy-700 h-16 z-40 transition-all duration-300 shadow-sm`}>
      <div className="flex items-center justify-between h-full px-4 lg:px-6">
        <div className="flex items-center gap-4">
          <button 
            onClick={onMenuClick}
            className="md:hidden text-slate-400 hover:text-cyan-400 transition-colors"
          >
            <Menu className="w-6 h-6" />
          </button>
          <div className="md:hidden flex items-center shrink-0">
            <Logo size="sm" />
          </div>
          <h1 className="text-[13px] font-bold tracking-widest uppercase text-slate-100 hidden sm:block">
            {pageTitle}
          </h1>
        </div>

        <div className="flex items-center gap-3">
          <div className="hidden md:flex relative">
            <Search className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
            <input 
              type="text" 
              placeholder="Search..." 
              className="bg-navy-900 border border-navy-700 rounded-lg pl-9 pr-3 py-2 w-64 text-xs text-slate-200 placeholder-slate-500 outline-none focus:border-cyan-500/50 focus:ring-1 focus:ring-cyan-500/30 transition-all shadow-inner"
            />
          </div>

          <button className="md:hidden p-2 rounded-lg text-slate-400 hover:text-cyan-400 hover:bg-navy-900 transition-colors">
            <Search className="w-5 h-5" />
          </button>

          <div className="relative" ref={notifRef}>
            <button 
              onClick={() => setShowNotifications(!showNotifications)}
              className="p-2 rounded-lg text-slate-400 hover:text-cyan-400 hover:bg-navy-900 transition-colors relative"
            >
              <Bell className="w-5 h-5" />
              <span className="absolute w-2 h-2 bg-cyan-500 rounded-full top-1.5 right-1.5 border border-navy-950 shadow-[0_0_5px_rgba(34,211,238,0.5)]"></span>
            </button>
            
            {showNotifications && (
              <div className="absolute right-0 top-12 w-80 bg-navy-900 border border-navy-700 rounded-xl shadow-[0_10px_30px_rgba(0,0,0,0.5)] p-0 overflow-hidden z-50">
                <div className="px-4 py-3 border-b border-navy-700 bg-navy-950">
                  <h3 className="text-[10px] font-bold tracking-widest uppercase text-slate-100">Notifications</h3>
                </div>
                <div className="max-h-80 overflow-y-auto hide-scrollbar">
                  {mockNotifications?.length > 0 ? (
                    mockNotifications.map((notif: any) => (
                      <div key={notif.id} className="px-4 py-3 hover:bg-navy-800/80 border-b border-navy-700/50 last:border-b-0 cursor-pointer transition-colors">
                        <div className="flex gap-3">
                          <div className={`w-2 h-2 mt-1.5 rounded-full shrink-0 ${notif.read ? 'bg-slate-600' : 'bg-cyan-500 shadow-[0_0_5px_rgba(34,211,238,0.5)]'}`}></div>
                          <div>
                            <p className="text-xs font-bold tracking-wide text-slate-200">{notif.title}</p>
                            <p className="text-[11px] text-slate-400 mt-0.5 line-clamp-2 leading-relaxed">{notif.message}</p>
                            <p className="text-[9px] font-mono tracking-widest text-slate-500 mt-1">{notif.time}</p>
                          </div>
                        </div>
                      </div>
                    ))
                  ) : (
                    <div className="px-4 py-6 text-center text-slate-500 text-xs font-medium uppercase tracking-widest">
                      No new notifications
                    </div>
                  )}
                </div>
                <div className="px-4 py-2.5 border-t border-navy-700 bg-[#050A15] text-center">
                  <button className="text-[10px] text-cyan-500 hover:text-cyan-400 font-bold uppercase tracking-widest transition-colors">View all</button>
                </div>
              </div>
            )}
          </div>

          <div className="relative ml-2" ref={profileRef}>
            {user ? (
              <>
                <button 
                  onClick={() => setShowProfile(!showProfile)}
                  className="bg-[#0A1224] border border-navy-700 rounded-full w-9 h-9 flex items-center justify-center text-[10px] font-bold text-cyan-400 hover:bg-navy-800 hover:border-cyan-500/50 transition-all shadow-[0_0_10px_rgba(34,211,238,0.1)] uppercase"
                >
                  {user.name ? user.name.slice(0, 2) : user.email.slice(0, 2)}
                </button>
                
                {showProfile && (
                  <div className="absolute right-0 top-12 w-56 bg-[#0A1224] border border-navy-700 rounded-xl shadow-[0_10px_30px_rgba(0,0,0,0.5)] py-2 z-50">
                    <div className="px-4 py-3 mb-2 border-b border-navy-700/50 bg-[#050A15]/50">
                      <p className="text-xs font-bold tracking-wide text-slate-100">{user.name || 'User'}</p>
                      <p className="text-[10px] font-mono text-slate-400 mt-0.5">{user.email}</p>
                    </div>
                    
                    <Link to="/settings" onClick={() => setShowProfile(false)} className="flex items-center gap-2 px-4 py-2 text-xs font-semibold tracking-wide text-slate-300 hover:text-cyan-400 hover:bg-navy-800 transition-colors">
                      <User className="w-4 h-4" />
                      Profile
                    </Link>
                    <Link to="/settings" onClick={() => setShowProfile(false)} className="flex items-center gap-2 px-4 py-2 text-xs font-semibold tracking-wide text-slate-300 hover:text-cyan-400 hover:bg-navy-800 transition-colors">
                      <SettingsIcon className="w-4 h-4" />
                      Settings
                    </Link>
                    
                    <div className="my-1 border-t border-navy-700/50"></div>
                    
                    <button onClick={handleLogout} className="w-full flex items-center gap-2 px-4 py-2 text-xs font-semibold tracking-wide text-rose-400 hover:bg-rose-500/10 transition-colors">
                      <LogOut className="w-4 h-4" />
                      Sign Out
                    </button>
                  </div>
                )}
              </>
            ) : (
              <Link 
                to="/login"
                className="flex items-center gap-2 px-4 py-2 bg-cyan-500/10 text-cyan-400 rounded-lg border border-cyan-500/30 hover:bg-cyan-500 hover:text-navy-950 font-bold text-xs tracking-widest transition-all"
              >
                <LogIn className="w-4 h-4" />
                SIGN IN
              </Link>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};
