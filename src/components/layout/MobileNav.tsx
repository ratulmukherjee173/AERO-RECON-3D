import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { LayoutDashboard, FolderKanban, PlusCircle, Box, MoreHorizontal, Cpu, Target, FileText, Settings, X } from 'lucide-react';

export const MobileNav: React.FC = () => {
  const location = useLocation();
  const [showMore, setShowMore] = useState(false);

  useEffect(() => {
    setShowMore(false);
  }, [location.pathname]);

  const isActive = (path: string) => {
    if (path === '/dashboard' && location.pathname === '/') return true;
    return location.pathname.startsWith(path);
  };

  const moreItems = [
    { label: 'Processing', icon: Cpu, path: '/processing' },
    { label: 'Accuracy', icon: Target, path: '/accuracy/demo-001' },
    { label: 'Reports', icon: FileText, path: '/reports' },
    { label: 'Settings', icon: Settings, path: '/settings' },
  ];

  return (
    <>
      {showMore && (
        <div 
          className="fixed inset-0 z-30 bg-black/50" 
          onClick={() => setShowMore(false)}
        />
      )}
      
      <div 
        className={`fixed bottom-16 left-0 right-0 bg-[#0A1224]/95 backdrop-blur-md border-t border-navy-700 p-4 z-30 transform transition-transform duration-300 ease-in-out shadow-[0_-10px_30px_rgba(0,0,0,0.5)] ${
          showMore ? 'translate-y-0' : 'translate-y-full'
        }`}
      >
        <div className="flex justify-between items-center mb-4 px-2">
          <h3 className="text-[10px] font-bold tracking-widest uppercase text-slate-400">More Options</h3>
          <button onClick={() => setShowMore(false)} className="text-slate-400 hover:text-cyan-400 transition-colors p-1">
            <X className="w-5 h-5" />
          </button>
        </div>
        <div className="grid grid-cols-2 gap-2">
          {moreItems.map((item) => {
            const Icon = item.icon;
            return (
              <Link
                key={item.path}
                to={item.path}
                onClick={() => setShowMore(false)}
                className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-all ${
                  isActive(item.path) 
                    ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 shadow-[0_0_10px_rgba(34,211,238,0.1)]' 
                    : 'text-slate-300 hover:bg-navy-800 border border-transparent'
                }`}
              >
                <Icon className="w-5 h-5" />
                <span className="text-[11px] font-bold tracking-wide uppercase">{item.label}</span>
              </Link>
            );
          })}
        </div>
      </div>

      <nav className="fixed bottom-0 left-0 right-0 h-16 bg-[#050A15]/90 backdrop-blur-md border-t border-navy-700 z-40 pb-safe shadow-[0_-5px_20px_rgba(0,0,0,0.5)]">
        <div className="grid grid-cols-5 items-center h-full">
          <Link to="/dashboard" className={`flex flex-col items-center gap-1 transition-colors ${isActive('/dashboard') ? 'text-cyan-400 drop-shadow-[0_0_5px_rgba(34,211,238,0.5)]' : 'text-slate-500 hover:text-slate-300'}`}>
            <LayoutDashboard className="w-5 h-5" />
            <span className="text-[9px] font-bold tracking-widest uppercase">Dashboard</span>
          </Link>
          
          <Link to="/projects" className={`flex flex-col items-center gap-1 transition-colors ${isActive('/projects') ? 'text-cyan-400 drop-shadow-[0_0_5px_rgba(34,211,238,0.5)]' : 'text-slate-500 hover:text-slate-300'}`}>
            <FolderKanban className="w-5 h-5" />
            <span className="text-[9px] font-bold tracking-widest uppercase">Projects</span>
          </Link>
          
          <Link to="/reconstruction/new" className="flex flex-col items-center justify-center group">
            <div className="bg-cyan-600 text-white rounded-full p-2.5 -mt-5 shadow-[0_0_15px_rgba(8,145,178,0.5)] ring-4 ring-[#050A15] flex items-center justify-center group-hover:bg-cyan-500 transition-colors">
              <PlusCircle className="w-6 h-6" />
            </div>
            <span className={`text-[9px] font-bold tracking-widest uppercase mt-1 ${isActive('/reconstruction/new') ? 'text-cyan-400' : 'text-slate-400 group-hover:text-cyan-400'}`}>New</span>
          </Link>
          
          <Link to="/viewer/demo-001" className={`flex flex-col items-center gap-1 transition-colors ${isActive('/viewer') ? 'text-cyan-400 drop-shadow-[0_0_5px_rgba(34,211,238,0.5)]' : 'text-slate-500 hover:text-slate-300'}`}>
            <Box className="w-5 h-5" />
            <span className="text-[9px] font-bold tracking-widest uppercase">Models</span>
          </Link>
          
          <button 
            onClick={() => setShowMore(!showMore)} 
            className={`flex flex-col items-center gap-1 transition-colors ${showMore ? 'text-cyan-400 drop-shadow-[0_0_5px_rgba(34,211,238,0.5)]' : 'text-slate-500 hover:text-slate-300'}`}
          >
            <MoreHorizontal className="w-5 h-5" />
            <span className="text-[9px] font-bold tracking-widest uppercase">More</span>
          </button>
        </div>
      </nav>
    </>
  );
};
