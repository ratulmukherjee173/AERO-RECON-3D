import { createContext, useContext, useState, useEffect } from 'react';
import type { ReactNode } from 'react';
import { safeGetStorage, safeSetStorage } from '../utils/storage';

export interface SettingsState {
  darkMode: boolean;
  accentColor: string;
  compactSidebar: boolean;
  showDemoBadges: boolean;
  notifications: {
    processingComplete: boolean;
    processingErrors: boolean;
    reportReady: boolean;
    lowStorage: boolean;
    systemUpdates: boolean;
  };
  processingDefaults: {
    qualityMode: string;
    outputs: {
      pointCloud: boolean;
      texturedMesh: boolean;
      digitalSurfaceModel: boolean;
      orthographicMap: boolean;
    };
    autoGenerateReports: boolean;
    hardwareAcceleration: boolean;
  };
}

const defaultSettings: SettingsState = {
  darkMode: true,
  accentColor: 'bg-blue-500',
  compactSidebar: false,
  showDemoBadges: true,
  notifications: {
    processingComplete: true,
    processingErrors: true,
    reportReady: true,
    lowStorage: true,
    systemUpdates: false,
  },
  processingDefaults: {
    qualityMode: 'Standard (Balanced)',
    outputs: {
      pointCloud: true,
      texturedMesh: true,
      digitalSurfaceModel: false,
      orthographicMap: false,
    },
    autoGenerateReports: true,
    hardwareAcceleration: true,
  }
};

interface SettingsContextType {
  settings: SettingsState;
  updateSettings: (newSettings: Partial<SettingsState>) => void;
  resetSettings: () => void;
}

const SettingsContext = createContext<SettingsContextType | undefined>(undefined);

export function SettingsProvider({ children }: { children: ReactNode }) {
  const [settings, setSettings] = useState<SettingsState>(() => {
    try {
      const saved = safeGetStorage('aero_recon_settings');
      if (saved) {
        return { ...defaultSettings, ...JSON.parse(saved) };
      }
    } catch (e) {
      console.warn('Failed to parse settings from localStorage', e);
    }
    return defaultSettings;
  });

  useEffect(() => {
    safeSetStorage('aero_recon_settings', JSON.stringify(settings));
    
    // Apply global dark mode class to body if necessary
    if (settings.darkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }

    // Apply global accent mapping to body
    document.body.setAttribute('data-accent', settings.accentColor);
  }, [settings]);

  const updateSettings = (newSettings: Partial<SettingsState>) => {
    setSettings(prev => ({ ...prev, ...newSettings }));
  };

  const resetSettings = () => {
    setSettings(defaultSettings);
  };

  return (
    <SettingsContext.Provider value={{ settings, updateSettings, resetSettings }}>
      {children}
    </SettingsContext.Provider>
  );
}

export function useSettings() {
  const context = useContext(SettingsContext);
  if (context === undefined) {
    throw new Error('useSettings must be used within a SettingsProvider');
  }
  return context;
}
