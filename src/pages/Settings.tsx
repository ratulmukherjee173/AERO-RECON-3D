import { useState } from 'react';
import { 
  User, Palette, Bell, Cpu, HardDrive, 
  Save, AlertTriangle, RotateCcw
} from 'lucide-react';
import { useSettings } from '../contexts/SettingsContext';

export default function Settings() {
  const { settings, updateSettings, resetSettings } = useSettings();
  const [activeTab, setActiveTab] = useState('profile');

  const tabs = [
    { id: 'profile', label: 'Profile', icon: User },
    { id: 'appearance', label: 'Appearance', icon: Palette },
    { id: 'notifications', label: 'Notifications', icon: Bell },
    { id: 'processing', label: 'Processing Defaults', icon: Cpu },
    { id: 'storage', label: 'Data & Storage', icon: HardDrive },
  ];

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <h1 className="text-xl md:text-2xl font-bold text-slate-100">Settings</h1>

      <div className="flex flex-col md:flex-row gap-6">
        {/* Tab Navigation */}
        <div className="md:w-56 shrink-0">
          <div className="bg-navy-800 border border-navy-600/50 rounded-xl p-2 flex flex-row md:flex-col overflow-x-auto md:overflow-visible gap-1 hide-scrollbar">
            {tabs.map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm font-medium transition-colors whitespace-nowrap md:whitespace-normal text-left ${
                  activeTab === tab.id 
                    ? 'bg-blue-600/10 text-blue-400' 
                    : 'text-slate-400 hover:text-slate-200 hover:bg-navy-700/50'
                }`}
              >
                <tab.icon size={18} className={activeTab === tab.id ? 'text-blue-400' : 'text-slate-500'} />
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        {/* Tab Content */}
        <div className="flex-1">
          <div className="bg-navy-800 border border-navy-600/50 rounded-xl p-6 min-h-[400px]">
            
            {activeTab === 'profile' && (
              <div className="max-w-2xl space-y-8 animate-fade-in">
                <div>
                  <h2 className="text-lg font-semibold text-slate-100 mb-1">Profile Information</h2>
                  <p className="text-sm text-slate-400">Update your account details and organization info.</p>
                </div>
                
                <div className="flex items-center gap-6">
                  <div className="w-20 h-20 rounded-full bg-blue-600 flex items-center justify-center text-2xl font-bold text-white shadow-lg">
                    AS
                  </div>
                  <button className="px-4 py-2 bg-navy-700 hover:bg-navy-600 border border-navy-500 rounded-lg text-sm font-medium text-slate-200 transition-colors">
                    Change Avatar
                  </button>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-slate-300">Full Name</label>
                    <input type="text" defaultValue="Alex Smith" className="w-full bg-navy-900 border border-navy-600 rounded-lg px-4 py-2.5 text-slate-100 focus:border-blue-500 focus:outline-none transition-colors" />
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-slate-300">Email Address</label>
                    <input type="email" defaultValue="alex@aerorecon.demo" className="w-full bg-navy-900 border border-navy-600 rounded-lg px-4 py-2.5 text-slate-100 focus:border-blue-500 focus:outline-none transition-colors" />
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-slate-300">Role</label>
                    <input type="text" defaultValue="Admin (Demo)" disabled className="w-full bg-navy-900/50 border border-navy-700 rounded-lg px-4 py-2.5 text-slate-500 cursor-not-allowed" />
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-slate-300">Organization</label>
                    <input type="text" defaultValue="GeoSpatial Tech Corp" className="w-full bg-navy-900 border border-navy-600 rounded-lg px-4 py-2.5 text-slate-100 focus:border-blue-500 focus:outline-none transition-colors" />
                  </div>
                </div>

                <button className="px-6 py-2.5 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-sm font-medium transition-colors flex items-center gap-2">
                  <Save size={16} /> Save Changes
                </button>
              </div>
            )}

            {activeTab === 'appearance' && (
              <div className="max-w-2xl space-y-8 animate-fade-in">
                <div className="flex justify-between items-start">
                  <div>
                    <h2 className="text-lg font-semibold text-slate-100 mb-1">Appearance & Interface</h2>
                    <p className="text-sm text-slate-400">Customize how AERO RECON-3D looks on your device.</p>
                  </div>
                  <button onClick={resetSettings} className="flex items-center gap-2 text-xs font-medium text-slate-400 hover:text-cyan-400 transition-colors">
                    <RotateCcw size={14} /> Reset Defaults
                  </button>
                </div>
                
                <div className="space-y-6">
                  <div className="flex items-center justify-between p-4 bg-navy-900 rounded-lg border border-navy-700 cursor-pointer hover:border-blue-500/50 transition-colors" onClick={() => updateSettings({ darkMode: !settings.darkMode })}>
                    <div>
                      <div className="font-medium text-slate-200">Dark Mode</div>
                      <div className="text-xs text-slate-400">Aero Recon runs in dark mode by default for better image analysis.</div>
                    </div>
                    <div className={`w-11 h-6 rounded-full relative transition-colors duration-300 ${settings.darkMode ? 'bg-blue-600' : 'bg-navy-700'}`}>
                      <div className={`w-5 h-5 rounded-full absolute top-0.5 shadow-sm transition-all duration-300 ${settings.darkMode ? 'bg-white right-0.5' : 'bg-slate-400 left-0.5'}`} />
                    </div>
                  </div>
                  
                  <div className="p-4 bg-navy-900 rounded-lg border border-navy-700">
                    <div className="font-medium text-slate-200 mb-3">Accent Color</div>
                    <div className="flex gap-4">
                      {[
                        { color: 'bg-blue-500', label: 'Blue' },
                        { color: 'bg-cyan-500', label: 'Cyan' },
                        { color: 'bg-purple-500', label: 'Purple' },
                        { color: 'bg-green-500', label: 'Green' }
                      ].map((c) => (
                        <button 
                          key={c.color} 
                          onClick={() => updateSettings({ accentColor: c.color })}
                          className={`w-8 h-8 rounded-full ${c.color} transition-all duration-300 ${settings.accentColor === c.color ? 'ring-2 ring-white ring-offset-2 ring-offset-navy-900 scale-110 shadow-[0_0_15px_rgba(255,255,255,0.3)]' : 'opacity-70 hover:opacity-100 hover:scale-110'}`} 
                          title={c.label}
                        />
                      ))}
                    </div>
                  </div>

                  <div className="flex items-center justify-between p-4 bg-navy-900 rounded-lg border border-navy-700 cursor-pointer hover:border-blue-500/50 transition-colors" onClick={() => updateSettings({ compactSidebar: !settings.compactSidebar })}>
                    <div>
                      <div className="font-medium text-slate-200">Compact Sidebar</div>
                      <div className="text-xs text-slate-400">Minimize the desktop sidebar to icons only.</div>
                    </div>
                    <div className={`w-11 h-6 rounded-full relative transition-colors duration-300 ${settings.compactSidebar ? 'bg-blue-600' : 'bg-navy-700'}`}>
                      <div className={`w-5 h-5 rounded-full absolute top-0.5 shadow-sm transition-all duration-300 ${settings.compactSidebar ? 'bg-white right-0.5' : 'bg-slate-400 left-0.5'}`} />
                    </div>
                  </div>

                  <div className="flex items-center justify-between p-4 bg-navy-900 rounded-lg border border-navy-700 cursor-pointer hover:border-blue-500/50 transition-colors" onClick={() => updateSettings({ showDemoBadges: !settings.showDemoBadges })}>
                    <div>
                      <div className="font-medium text-slate-200">Show Demo Badges</div>
                      <div className="text-xs text-slate-400">Display "DEMO DATA" indicators on applicable components.</div>
                    </div>
                    <div className={`w-11 h-6 rounded-full relative transition-colors duration-300 ${settings.showDemoBadges ? 'bg-blue-600' : 'bg-navy-700'}`}>
                      <div className={`w-5 h-5 rounded-full absolute top-0.5 shadow-sm transition-all duration-300 ${settings.showDemoBadges ? 'bg-white right-0.5' : 'bg-slate-400 left-0.5'}`} />
                    </div>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'notifications' && (
              <div className="max-w-2xl space-y-8 animate-fade-in">
                <div>
                  <h2 className="text-lg font-semibold text-slate-100 mb-1">Notification Preferences</h2>
                  <p className="text-sm text-slate-400">Manage when and how you are notified about processing status.</p>
                </div>
                
                <div className="space-y-4">
                  {[
                    { key: 'processingComplete' as const, title: 'Processing Complete', desc: 'Get notified when a 3D reconstruction finishes successfully.' },
                    { key: 'processingErrors' as const, title: 'Processing Errors', desc: 'Alerts if a reconstruction fails or encounters issues.' },
                    { key: 'reportReady' as const, title: 'Report Ready', desc: 'Notification when an accuracy or quality report is generated.' },
                    { key: 'lowStorage' as const, title: 'Low Storage', desc: 'Warnings when workspace storage exceeds 90% capacity.' },
                    { key: 'systemUpdates' as const, title: 'System Updates', desc: 'News about AERO RECON-3D updates and new features.' },
                  ].map((item) => (
                    <div 
                      key={item.key} 
                      className="flex items-center justify-between p-4 bg-navy-900 rounded-lg border border-navy-700 cursor-pointer hover:border-blue-500/50 transition-colors"
                      onClick={() => updateSettings({ 
                        notifications: { ...settings.notifications, [item.key]: !settings.notifications[item.key] } 
                      })}
                    >
                      <div>
                        <div className="font-medium text-slate-200">{item.title}</div>
                        <div className="text-xs text-slate-400 mt-0.5">{item.desc}</div>
                      </div>
                      <div className={`w-11 h-6 rounded-full relative transition-colors duration-300 ${settings.notifications[item.key] ? 'bg-blue-600' : 'bg-navy-700'}`}>
                        <div className={`w-5 h-5 rounded-full absolute top-0.5 shadow-sm transition-all duration-300 ${settings.notifications[item.key] ? 'bg-white right-0.5' : 'bg-slate-400 left-0.5'}`} />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {activeTab === 'processing' && (
              <div className="max-w-2xl space-y-8 animate-fade-in">
                <div>
                  <h2 className="text-lg font-semibold text-slate-100 mb-1">Processing Defaults</h2>
                  <p className="text-sm text-slate-400">Set standard parameters for new reconstruction tasks.</p>
                </div>
                
                <div className="space-y-6">
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-slate-300">Default Quality Mode</label>
                    <select 
                      value={settings.processingDefaults.qualityMode}
                      onChange={(e) => updateSettings({ 
                        processingDefaults: { ...settings.processingDefaults, qualityMode: e.target.value } 
                      })}
                      className="w-full bg-navy-900 border border-navy-600 rounded-lg px-4 py-2.5 text-slate-200 focus:outline-none focus:border-blue-500 cursor-pointer"
                    >
                      <option value="Preview (Fast)">Preview (Fast)</option>
                      <option value="Standard (Balanced)">Standard (Balanced)</option>
                      <option value="High Accuracy (Maximum)">High Accuracy (Maximum)</option>
                    </select>
                  </div>

                  <div className="space-y-3">
                    <label className="text-sm font-medium text-slate-300">Default Output Generation</label>
                    <div className="bg-navy-900 p-4 rounded-lg border border-navy-700 space-y-3">
                      {[
                        { key: 'pointCloud' as const, label: 'Point Cloud (LAS/LAZ)' },
                        { key: 'texturedMesh' as const, label: 'Textured Mesh (OBJ/GLTF)' },
                        { key: 'digitalSurfaceModel' as const, label: 'Digital Surface Model (TIFF)' },
                        { key: 'orthographicMap' as const, label: 'Orthographic Map (GeoTIFF)' }
                      ].map((item) => (
                        <label key={item.key} className="flex items-center gap-3 cursor-pointer">
                          <input 
                            type="checkbox" 
                            checked={settings.processingDefaults.outputs[item.key]}
                            onChange={(e) => updateSettings({
                              processingDefaults: { 
                                ...settings.processingDefaults, 
                                outputs: { ...settings.processingDefaults.outputs, [item.key]: e.target.checked }
                              }
                            })}
                            className="appearance-none w-5 h-5 border-2 border-navy-600 rounded bg-navy-900 checked:bg-blue-600 checked:border-blue-600 cursor-pointer flex items-center justify-center after:content-['✓'] after:text-white after:text-sm after:hidden checked:after:block transition-all" 
                          />
                          <span className="text-sm text-slate-300">{item.label}</span>
                        </label>
                      ))}
                    </div>
                  </div>

                  <div 
                    className="flex items-center justify-between p-4 bg-navy-900 rounded-lg border border-navy-700 cursor-pointer hover:border-blue-500/50 transition-colors"
                    onClick={() => updateSettings({
                      processingDefaults: { ...settings.processingDefaults, autoGenerateReports: !settings.processingDefaults.autoGenerateReports }
                    })}
                  >
                    <div>
                      <div className="font-medium text-slate-200">Auto-Generate Reports</div>
                      <div className="text-xs text-slate-400">Automatically create quality reports when processing finishes.</div>
                    </div>
                    <div className={`w-11 h-6 rounded-full relative transition-colors duration-300 ${settings.processingDefaults.autoGenerateReports ? 'bg-blue-600' : 'bg-navy-700'}`}>
                      <div className={`w-5 h-5 rounded-full absolute top-0.5 shadow-sm transition-all duration-300 ${settings.processingDefaults.autoGenerateReports ? 'bg-white right-0.5' : 'bg-slate-400 left-0.5'}`} />
                    </div>
                  </div>

                  <div 
                    className="flex items-center justify-between p-4 bg-navy-900 rounded-lg border border-navy-700 cursor-pointer hover:border-blue-500/50 transition-colors"
                    onClick={() => updateSettings({
                      processingDefaults: { ...settings.processingDefaults, hardwareAcceleration: !settings.processingDefaults.hardwareAcceleration }
                    })}
                  >
                    <div>
                      <div className="font-medium text-slate-200">Hardware Acceleration</div>
                      <div className="text-xs text-slate-400">Use GPU for faster processing (requires supported hardware).</div>
                    </div>
                    <div className={`w-11 h-6 rounded-full relative transition-colors duration-300 ${settings.processingDefaults.hardwareAcceleration ? 'bg-blue-600' : 'bg-navy-700'}`}>
                      <div className={`w-5 h-5 rounded-full absolute top-0.5 shadow-sm transition-all duration-300 ${settings.processingDefaults.hardwareAcceleration ? 'bg-white right-0.5' : 'bg-slate-400 left-0.5'}`} />
                    </div>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'storage' && (
              <div className="max-w-2xl space-y-8 animate-fade-in">
                <div>
                  <h2 className="text-lg font-semibold text-slate-100 mb-1">Data & Storage Management</h2>
                  <p className="text-sm text-slate-400">Manage your workspace storage and cache.</p>
                </div>
                
                <div className="bg-navy-900 border border-navy-700 rounded-xl p-5">
                  <div className="flex justify-between items-end mb-2">
                    <div>
                      <h3 className="font-medium text-slate-200">Workspace Storage</h3>
                      <p className="text-xs text-slate-400 mt-1">12.4 GB used of 50 GB</p>
                    </div>
                    <div className="text-sm font-semibold text-blue-400">24%</div>
                  </div>
                  <div className="h-2.5 bg-navy-800 rounded-full overflow-hidden mt-3 mb-4">
                    <div className="h-full flex">
                      <div className="bg-blue-500 w-[60%]" title="Models: 7.4 GB"></div>
                      <div className="bg-purple-500 w-[25%]" title="Source Video: 3.1 GB"></div>
                      <div className="bg-cyan-500 w-[15%]" title="Cache: 1.9 GB"></div>
                    </div>
                  </div>
                  <div className="flex gap-4 text-xs text-slate-400">
                    <div className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-blue-500"></span> Models</div>
                    <div className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-purple-500"></span> Videos</div>
                    <div className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-cyan-500"></span> Cache</div>
                  </div>
                </div>

                <div className="flex gap-4">
                  <button className="px-4 py-2 bg-navy-900 border border-navy-600 hover:bg-navy-700 text-slate-200 rounded-lg text-sm font-medium transition-colors">
                    Clear Cache (1.9 GB)
                  </button>
                  <button className="px-4 py-2 bg-navy-900 border border-navy-600 hover:bg-navy-700 text-slate-200 rounded-lg text-sm font-medium transition-colors">
                    Export All Data
                  </button>
                </div>

                <div className="pt-6 border-t border-navy-700">
                  <h3 className="text-red-400 font-medium flex items-center gap-2 mb-2">
                    <AlertTriangle size={16} /> Danger Zone
                  </h3>
                  <p className="text-sm text-slate-400 mb-4">Permanently delete all projects, models, and data from this workspace. This action cannot be undone.</p>
                  <button className="px-4 py-2 bg-red-500/10 hover:bg-red-500/20 text-red-400 border border-red-500/30 rounded-lg text-sm font-medium transition-colors">
                    Delete All Workspace Data
                  </button>
                </div>
              </div>
            )}

          </div>
        </div>
      </div>
    </div>
  );
}
