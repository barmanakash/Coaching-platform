import { createContext, useContext, useState, useCallback } from 'react';
import { login as loginApi } from '../services/api/authApi';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    const stored = localStorage.getItem('user');
    return stored ? JSON.parse(stored) : null;
  });

  const applySession = useCallback((data) => {
    const userInfo = {
      userId: data.user_id,
      name: data.name,
      role: data.role,
      instituteId: data.institute_id || null,
      instituteName: data.institute_name || null,
    };
    localStorage.setItem('access_token', data.access_token);
    localStorage.setItem('user', JSON.stringify(userInfo));
    setUser(userInfo);
    return userInfo;
  }, []);

  const login = useCallback(async (email, password) => {
    const data = await loginApi(email, password);
    return applySession(data);
  }, [applySession]);

  // Used by the accept-invite page: the backend returns the same token
  // shape as /login, so a freshly-created account signs straight in.
  const setSessionFromInvite = useCallback((data) => applySession(data), [applySession]);

  const logout = useCallback(() => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');
    setUser(null);
  }, []);

  const updateInstituteName = useCallback((name) => {
    setUser((prev) => {
      if (!prev) return prev;
      const next = { ...prev, instituteName: name };
      localStorage.setItem('user', JSON.stringify(next));
      return next;
    });
  }, []);

  const value = {
    user,
    isAuthenticated: !!user,
    isSuperAdmin: user?.role === 'super_admin',
    login,
    setSessionFromInvite,
    logout,
    updateInstituteName,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
