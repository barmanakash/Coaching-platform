import { createContext, useContext, useState, useCallback } from 'react';
import { login as loginApi, signup as signupApi } from '../services/api/authApi';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    const stored = localStorage.getItem('user');
    return stored ? JSON.parse(stored) : null;
  });

  const login = useCallback(async (email, password) => {
    const data = await loginApi(email, password);
    const userInfo = {
      userId: data.user_id,
      name: data.name,
      role: data.role,
    };
    localStorage.setItem('access_token', data.access_token);
    localStorage.setItem('user', JSON.stringify(userInfo));
    setUser(userInfo);
    return userInfo;
  }, []);

  const signup = useCallback(async ({ name, email, password, role, phone }) => {
    // Accounts start "pending" and require admin approval, so signup does
    // NOT log the user in — it just returns the confirmation message.
    return signupApi({ name, email, password, role, phone });
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');
    setUser(null);
  }, []);

  const value = {
    user,
    isAuthenticated: !!user,
    login,
    signup,
    logout,
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
