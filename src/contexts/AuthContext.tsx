import React, { createContext, useContext, useState, useEffect } from 'react';
import { apiFetch } from '../utils/api';

interface User {
  id: string;
  email: string;
  name?: string;
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (token: string, user: User, rememberMe: boolean) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  isAuthenticated: false,
  isLoading: true,
  login: () => {},
  logout: () => {},
});

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const initAuth = async () => {
      const token = localStorage.getItem('token') || sessionStorage.getItem('token');
      if (token) {
        try {
          const res = await apiFetch('/auth/me');
          if (res.ok) {
            setUser(await res.json());
          } else {
            throw new Error("Failed to authenticate");
          }
        } catch (error) {
          console.error("Failed to restore session:", error);
          localStorage.removeItem('token');
          sessionStorage.removeItem('token');
        }
      }
      setIsLoading(false);
    };

    initAuth();
  }, []);

  const login = (token: string, userData: User, rememberMe: boolean) => {
    if (rememberMe) {
      localStorage.setItem('token', token);
    } else {
      sessionStorage.setItem('token', token);
    }
    setUser(userData);
  };

  const logout = () => {
    localStorage.removeItem('token');
    sessionStorage.removeItem('token');
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, isAuthenticated: !!user, isLoading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
