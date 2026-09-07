import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { apiFetch } from '../utils/api';

interface User {
  id: string;
  email: string;
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (token: string, user: User, rememberMe: boolean) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const logout = useCallback(() => {
    setUser(null);
    localStorage.removeItem('aerorecon3d_auth_token');
    sessionStorage.removeItem('aerorecon3d_auth_token');
  }, []);

  useEffect(() => {
    // Handle global unauthorized events from apiFetch
    const handleUnauthorized = () => {
      logout();
    };
    window.addEventListener('unauthorized', handleUnauthorized);
    return () => window.removeEventListener('unauthorized', handleUnauthorized);
  }, [logout]);

  useEffect(() => {
    const verifySession = async () => {
      const localToken = localStorage.getItem('aerorecon3d_auth_token');
      const sessionToken = sessionStorage.getItem('aerorecon3d_auth_token');
      const token = localToken || sessionToken;

      if (!token) {
        setIsLoading(false);
        return;
      }

      try {
        const response = await apiFetch('/auth/me');
        if (response.ok) {
          const userData = await response.json();
          setUser(userData);
        } else {
          logout();
        }
      } catch (error) {
        console.error('Session verification failed:', error);
        logout();
      } finally {
        setIsLoading(false);
      }
    };

    verifySession();
  }, [logout]);

  const login = (token: string, userData: User, rememberMe: boolean) => {
    setUser(userData);
    if (rememberMe) {
      localStorage.setItem('aerorecon3d_auth_token', token);
      sessionStorage.removeItem('aerorecon3d_auth_token');
    } else {
      sessionStorage.setItem('aerorecon3d_auth_token', token);
      localStorage.removeItem('aerorecon3d_auth_token');
    }
  };

  return (
    <AuthContext.Provider value={{ user, isAuthenticated: !!user, isLoading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

