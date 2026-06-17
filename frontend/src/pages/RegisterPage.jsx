import React, { useState, useEffect } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const ORG_TYPES = ['University', 'College', 'School', 'Hostel', 'Student Club', 'Coaching Institute'];

export default function RegisterPage() {
  const { createWorkspace, joinWorkspace } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  // mode: 'create' = Admin creates new workspace | 'join' = Student joins existing
  const [mode, setMode] = useState(searchParams.get('mode') === 'create' ? 'create' : 'join');
  const [error, setError]     = useState('');
  const [loading, setLoading] = useState(false);
  const [showPwd, setShowPwd] = useState(false);

  /* ─── Join Form ─────────────────────────────────────────── */
  const [joinForm, setJoinForm] = useState({
    name: '', email: '', password: '', workspace_code: '', invite_code: ''
  });

  /* ─── Create Form ───────────────────────────────────────── */
  const [createForm, setCreateForm] = useState({
    admin_name: '', admin_email: '', admin_password: '',
    organization_name: '', organization_type: 'University', workspace_code: '', description: ''
  });

  const handleJoin   = (e) => setJoinForm({ ...joinForm, [e.target.name]: e.target.value });
  const handleCreate = (e) => setCreateForm({ ...createForm, [e.target.name]: e.target.value });

  const submitJoin = async (e) => {
    e.preventDefault(); setError(''); setLoading(true);
    try {
      const payload = { ...joinForm, workspace_code: joinForm.workspace_code.trim().toLowerCase(), invite_code: joinForm.invite_code.trim().toUpperCase() };
      await joinWorkspace(payload);
      navigate('/dashboard');
    } catch (err) {
      setError(err?.response?.data?.detail || 'Could not join workspace. Check your codes.');
    } finally { setLoading(false); }
  };

  const submitCreate = async (e) => {
    e.preventDefault(); setError(''); setLoading(true);
    try {
      const payload = { ...createForm, workspace_code: createForm.workspace_code.trim().toLowerCase() };
      await createWorkspace(payload);
      navigate('/admin');
    } catch (err) {
      setError(err?.response?.data?.detail || 'Could not create workspace.');
    } finally { setLoading(false); }
  };

  return (
    <div className="auth-bg">
      <div className="auth-card auth-card-wide">
        {/* Logo */}
        <div className="auth-logo">
          <div className="logo-icon">🎓</div>
          <h1 className="auth-brand">EchoCampus <span>AI</span></h1>
          <p className="auth-subtitle">Student Welfare & Campus Intelligence</p>
        </div>

        {/* Mode Tabs */}
        <div className="reg-tabs">
          <button className={`reg-tab ${mode === 'join' ? 'active' : ''}`} onClick={() => { setMode('join'); setError(''); }}>
            🔗 Join Workspace
          </button>
          <button className={`reg-tab ${mode === 'create' ? 'active' : ''}`} onClick={() => { setMode('create'); setError(''); }}>
            🏗️ Create Workspace
          </button>
        </div>

        {error && <div className="auth-error">⚠️ {error}</div>}

        {/* ─── Join Mode ─────────────────────────────────────────────────── */}
        {mode === 'join' && (
          <form onSubmit={submitJoin} className="auth-form">
            <p className="form-hint">Enter the Workspace Code and Invite Code given by your administrator.</p>

            <div className="form-row">
              <div className="form-group">
                <label>Workspace Code</label>
                <div className="input-wrap">
                  <span className="input-icon">🏫</span>
                  <input name="workspace_code" placeholder="e.g. medicaps" value={joinForm.workspace_code} onChange={handleJoin} required />
                </div>
              </div>
              <div className="form-group">
                <label>Invite Code</label>
                <div className="input-wrap">
                  <span className="input-icon">🔑</span>
                  <input name="invite_code" placeholder="e.g. MCPX92" value={joinForm.invite_code} onChange={handleJoin} required style={{ textTransform: 'uppercase' }} />
                </div>
              </div>
            </div>

            <div className="form-group">
              <label>Your Full Name</label>
              <div className="input-wrap">
                <span className="input-icon">👤</span>
                <input name="name" placeholder="Aarav Patel" value={joinForm.name} onChange={handleJoin} required />
              </div>
            </div>

            <div className="form-group">
              <label>Email Address</label>
              <div className="input-wrap">
                <span className="input-icon">✉️</span>
                <input name="email" type="email" placeholder="you@university.edu" value={joinForm.email} onChange={handleJoin} required />
              </div>
            </div>

            <div className="form-group">
              <label>Password</label>
              <div className="input-wrap">
                <span className="input-icon">🔒</span>
                <input name="password" type={showPwd ? 'text' : 'password'} placeholder="Create a password" value={joinForm.password} onChange={handleJoin} required minLength={6} />
                <button type="button" className="pwd-toggle" onClick={() => setShowPwd(!showPwd)}>{showPwd ? '🙈' : '👁️'}</button>
              </div>
            </div>

            <button type="submit" className="auth-btn" disabled={loading}>
              {loading ? <span className="btn-spinner" /> : 'Join Workspace'}
            </button>
          </form>
        )}

        {/* ─── Create Mode ───────────────────────────────────────────────── */}
        {mode === 'create' && (
          <form onSubmit={submitCreate} className="auth-form">
            <p className="form-hint">Create a new workspace for your institution. You will be the Administrator.</p>

            <div className="form-row">
              <div className="form-group">
                <label>Institution Name</label>
                <div className="input-wrap">
                  <span className="input-icon">🏛️</span>
                  <input name="organization_name" placeholder="Medicaps University" value={createForm.organization_name} onChange={handleCreate} required />
                </div>
              </div>
              <div className="form-group">
                <label>Organization Type</label>
                <div className="input-wrap">
                  <span className="input-icon">📋</span>
                  <select name="organization_type" value={createForm.organization_type} onChange={handleCreate} required>
                    {ORG_TYPES.map(t => <option key={t}>{t}</option>)}
                  </select>
                </div>
              </div>
            </div>

            <div className="form-group">
              <label>Workspace Code <span className="label-hint">(unique slug, lowercase, no spaces)</span></label>
              <div className="input-wrap">
                <span className="input-icon">🔗</span>
                <input name="workspace_code" placeholder="e.g. medicaps" value={createForm.workspace_code} onChange={handleCreate} required pattern="^[a-z0-9_-]+$" title="Lowercase letters, numbers, hyphens, underscores only" />
              </div>
            </div>

            <div className="form-group">
              <label>Description <span className="label-hint">(optional)</span></label>
              <div className="input-wrap">
                <span className="input-icon">📝</span>
                <input name="description" placeholder="Brief description of your institution" value={createForm.description} onChange={handleCreate} />
              </div>
            </div>

            <div className="form-divider">Administrator Account</div>

            <div className="form-group">
              <label>Admin Full Name</label>
              <div className="input-wrap">
                <span className="input-icon">👤</span>
                <input name="admin_name" placeholder="Dr. Rajesh Sharma" value={createForm.admin_name} onChange={handleCreate} required />
              </div>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label>Admin Email</label>
                <div className="input-wrap">
                  <span className="input-icon">✉️</span>
                  <input name="admin_email" type="email" placeholder="admin@university.edu" value={createForm.admin_email} onChange={handleCreate} required />
                </div>
              </div>
              <div className="form-group">
                <label>Admin Password</label>
                <div className="input-wrap">
                  <span className="input-icon">🔒</span>
                  <input name="admin_password" type={showPwd ? 'text' : 'password'} placeholder="Strong password" value={createForm.admin_password} onChange={handleCreate} required minLength={6} />
                  <button type="button" className="pwd-toggle" onClick={() => setShowPwd(!showPwd)}>{showPwd ? '🙈' : '👁️'}</button>
                </div>
              </div>
            </div>

            <button type="submit" className="auth-btn" disabled={loading}>
              {loading ? <span className="btn-spinner" /> : '🚀 Create Workspace'}
            </button>
          </form>
        )}

        <div className="auth-footer">
          <p>Already have an account? <Link to="/login">Sign In</Link></p>
          <Link to="/" className="back-home">← Back to Home</Link>
        </div>
      </div>
    </div>
  );
}
