import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();

  const [form, setForm] = useState({ workspace_code: '', email: '', password: '' });
  const [error, setError]     = useState('');
  const [loading, setLoading] = useState(false);
  const [showPwd, setShowPwd] = useState(false);

  const handle = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  const submit = async (e) => {
    e.preventDefault();
    setError(''); setLoading(true);
    try {
      const data = await login(form.workspace_code.trim().toLowerCase(), form.email.trim(), form.password);
      const role = data.user?.role;
      navigate(role === 'admin' || role === 'super_admin' || role === 'moderator' ? '/admin' : '/dashboard');
    } catch (err) {
      setError(err?.response?.data?.detail || err?.message || 'Login failed. Please check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-bg">
      <div className="auth-card">
        {/* Logo */}
        <div className="auth-logo">
          <div className="logo-icon">🎓</div>
          <h1 className="auth-brand">EchoCampus <span>AI</span></h1>
          <p className="auth-subtitle">Sign in to your workspace</p>
        </div>

        {error && <div className="auth-error">⚠️ {error}</div>}

        <form onSubmit={submit} className="auth-form">
          <div className="form-group">
            <label>Workspace Code</label>
            <div className="input-wrap">
              <span className="input-icon">🏫</span>
              <input
                name="workspace_code"
                type="text"
                placeholder="e.g. medicaps"
                value={form.workspace_code}
                onChange={handle}
                required
                autoComplete="off"
              />
            </div>
          </div>

          <div className="form-group">
            <label>Email Address</label>
            <div className="input-wrap">
              <span className="input-icon">✉️</span>
              <input
                name="email"
                type="email"
                placeholder="you@university.edu"
                value={form.email}
                onChange={handle}
                required
              />
            </div>
          </div>

          <div className="form-group">
            <label>Password</label>
            <div className="input-wrap">
              <span className="input-icon">🔒</span>
              <input
                name="password"
                type={showPwd ? 'text' : 'password'}
                placeholder="Your password"
                value={form.password}
                onChange={handle}
                required
              />
              <button type="button" className="pwd-toggle" onClick={() => setShowPwd(!showPwd)}>
                {showPwd ? '🙈' : '👁️'}
              </button>
            </div>
          </div>

          <button type="submit" className="auth-btn" disabled={loading}>
            {loading ? <span className="btn-spinner" /> : 'Sign In'}
          </button>
        </form>

        <div className="auth-footer">
          <p>New to EchoCampus AI?</p>
          <div className="auth-links">
            <Link to="/register?mode=join">Join a Workspace</Link>
            <span>·</span>
            <Link to="/register?mode=create">Create Workspace</Link>
          </div>
          <Link to="/" className="back-home">← Back to Home</Link>
        </div>
      </div>

      {/* Demo hint */}
      <div className="demo-hint">
        <strong>Demo:</strong> workspace: <code>medicaps</code> · email: <code>admin@medicaps.edu</code> · pass: <code>Admin@123</code>
      </div>
    </div>
  );
}
