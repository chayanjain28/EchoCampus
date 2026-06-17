import React, { createContext, useState, useEffect, useContext } from 'react';
import api from '../services/api';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser]         = useState(null);
  const [org, setOrg]           = useState(null);
  const [token, setToken]       = useState(localStorage.getItem('echo_token'));
  const [loading, setLoading]   = useState(true);

  /* ─── Bootstrap from localStorage ─────────────────────────────────────── */
  useEffect(() => {
    const init = async () => {
      const storedToken = localStorage.getItem('echo_token');
      const storedUser  = localStorage.getItem('echo_user');
      const storedOrg   = localStorage.getItem('echo_org');

      if (storedToken && storedUser) {
        try {
          setUser(JSON.parse(storedUser));
          setOrg(storedOrg ? JSON.parse(storedOrg) : null);
          setToken(storedToken);
          // Verify token still valid
          const res = await api.get('/auth/me');
          _applySession(res.data);
        } catch {
          _clearSession();
        }
      }
      setLoading(false);
    };
    init();
  }, []);

  /* ─── Helpers ───────────────────────────────────────────────────────────── */
  const _applySession = (data) => {
    const { access_token, user: u, organization: o } = data;
    localStorage.setItem('echo_token', access_token);
    localStorage.setItem('echo_user',  JSON.stringify(u));
    localStorage.setItem('echo_org',   JSON.stringify(o));
    setToken(access_token);
    setUser(u);
    setOrg(o);
  };

  const _clearSession = () => {
    localStorage.removeItem('echo_token');
    localStorage.removeItem('echo_user');
    localStorage.removeItem('echo_org');
    setToken(null);
    setUser(null);
    setOrg(null);
  };

  /* ─── Auth Actions ──────────────────────────────────────────────────────── */
  const login = async (workspace_code, email, password) => {
    const res = await api.post('/auth/login', { workspace_code, email, password });
    _applySession(res.data);
    return res.data;
  };

  const createWorkspace = async (payload) => {
    const res = await api.post('/auth/create-workspace', payload);
    _applySession(res.data);
    return res.data;
  };

  const joinWorkspace = async (payload) => {
    const res = await api.post('/auth/join-workspace', payload);
    _applySession(res.data);
    return res.data;
  };

  const logout = () => _clearSession();

  const refreshOrg = async () => {
    const res = await api.get('/auth/me');
    _applySession(res.data);
  };

  return (
    <AuthContext.Provider value={{
      user, org, token, loading,
      login, createWorkspace, joinWorkspace, logout, refreshOrg,
      isAdmin:      ['admin', 'super_admin'].includes(user?.role),
      isModerator:  ['moderator', 'admin', 'super_admin'].includes(user?.role),
    }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider');
  return ctx;
};

export default AuthContext;
