import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import LandingPage       from './pages/LandingPage';
import LoginPage         from './pages/LoginPage';
import RegisterPage      from './pages/RegisterPage';
import StudentDashboard  from './pages/StudentDashboard';
import AdminDashboard    from './pages/AdminDashboard';
import './index.css';

function PrivateRoute({ children, adminOnly = false }) {
  const { user, loading } = useAuth();
  if (loading) return <div className="full-loading"><div className="spinner-lg" /></div>;
  if (!user)   return <Navigate to="/login" replace />;
  if (adminOnly && !['admin','super_admin','moderator'].includes(user.role)) return <Navigate to="/dashboard" replace />;
  return children;
}

function SmartRedirect() {
  const { user } = useAuth();
  if (!user) return <Navigate to="/" replace />;
  return ['admin','super_admin','moderator'].includes(user.role)
    ? <Navigate to="/admin"     replace />
    : <Navigate to="/dashboard" replace />;
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/"          element={<LandingPage />} />
          <Route path="/login"     element={<LoginPage />} />
          <Route path="/register"  element={<RegisterPage />} />
          <Route path="/dashboard" element={<PrivateRoute><StudentDashboard /></PrivateRoute>} />
          <Route path="/admin"     element={<PrivateRoute adminOnly><AdminDashboard /></PrivateRoute>} />
          <Route path="/redirect"  element={<SmartRedirect />} />
          <Route path="*"          element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
