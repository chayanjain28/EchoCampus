import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';

const CATEGORIES = ['All', 'Hostel', 'Mess', 'WiFi', 'Transport', 'Academic', 'Infrastructure', 'Security', 'Other'];
const STATUSES   = ['All', 'Pending', 'In Progress', 'Resolved', 'Escalated', 'Rejected'];
const PRIORITIES = ['Low', 'Medium', 'High', 'Critical'];

const PRIORITY_COLORS = { Low: '#22c55e', Medium: '#f59e0b', High: '#f97316', Critical: '#ef4444' };
const STATUS_COLORS   = { Pending: '#f59e0b', 'In Progress': '#3b82f6', Resolved: '#22c55e', Escalated: '#f97316', Rejected: '#6b7280' };
const CATEGORY_ICONS  = { Hostel: '🏠', Mess: '🍽️', WiFi: '📶', Transport: '🚌', Academic: '📚', Infrastructure: '🏗️', Security: '🔒', Other: '📌' };

export default function StudentDashboard() {
  const { user, org, logout } = useAuth();
  const navigate = useNavigate();

  const [view, setView]           = useState('feed');   // feed | submit | my | analytics | notifications
  const [complaints, setComplaints] = useState([]);
  const [myComplaints, setMyComplaints] = useState([]);
  const [analytics, setAnalytics]   = useState(null);
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading]       = useState(false);
  const [toast, setToast]           = useState('');

  // Filters
  const [catFilter, setCatFilter]   = useState('All');
  const [statusFilter, setStatusFilter] = useState('All');
  const [search, setSearch]         = useState('');

  // Submit form
  const [form, setForm]             = useState({ title: '', description: '', anonymous: false });
  const [submitting, setSubmitting] = useState(false);

  const showToast = (msg) => { setToast(msg); setTimeout(() => setToast(''), 3500); };

  /* ─── Data Fetchers ───────────────────────────────────────────────────── */
  const fetchFeed = useCallback(async () => {
    setLoading(true);
    try {
      // All org complaints visible to students for "I Am Also Affected"
      const res = await api.get('/complaints/all');
      setComplaints(res.data);
    } catch { /* ignore */ } finally { setLoading(false); }
  }, []);

  const fetchMine = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.get('/complaints/');
      setMyComplaints(res.data);
    } catch { } finally { setLoading(false); }
  }, []);

  const fetchAnalytics = useCallback(async () => {
    try {
      const res = await api.get('/analytics/student');
      setAnalytics(res.data);
    } catch { }
  }, []);

  const fetchNotifications = useCallback(async () => {
    try {
      const res = await api.get('/notifications/');
      setNotifications(res.data);
    } catch { }
  }, []);

  useEffect(() => {
    fetchFeed();
    fetchMine();
    fetchAnalytics();
    fetchNotifications();
  }, []);

  /* ─── Handlers ────────────────────────────────────────────────────────── */
  const submitComplaint = async (e) => {
    e.preventDefault(); setSubmitting(true);
    try {
      await api.post('/complaints/', form);
      showToast('✅ Complaint submitted and analyzed by AI!');
      setForm({ title: '', description: '', anonymous: false });
      setView('my'); fetchMine();
    } catch (err) {
      showToast('❌ ' + (err?.response?.data?.detail || 'Submission failed'));
    } finally { setSubmitting(false); }
  };

  const toggleSupport = async (cid) => {
    try {
      const res = await api.post(`/complaints/${cid}/support`);
      showToast(res.data.action === 'added' ? '👊 Marked as affected!' : '✅ Support removed');
      fetchFeed();
    } catch { showToast('❌ Could not update support'); }
  };

  const markAllRead = async () => {
    await api.put('/notifications/read-all');
    fetchNotifications();
  };

  const unreadCount = notifications.filter(n => !n.is_read).length;

  /* ─── Filtered data ───────────────────────────────────────────────────── */
  const displayComplaints = complaints.filter(c => {
    const matchCat    = catFilter === 'All' || c.category === catFilter;
    const matchStatus = statusFilter === 'All' || c.status === statusFilter;
    const matchSearch = !search || c.title.toLowerCase().includes(search.toLowerCase());
    return matchCat && matchStatus && matchSearch;
  });

  /* ─── Render ──────────────────────────────────────────────────────────── */
  return (
    <div className="dash-layout">
      {/* Toast */}
      {toast && <div className="toast">{toast}</div>}

      {/* ── Sidebar ─────────────────────────────────────────────────────── */}
      <aside className="sidebar">
        <div className="sidebar-brand">
          <span className="brand-icon">🎓</span>
          <div>
            <div className="brand-name">EchoCampus <span>AI</span></div>
            <div className="brand-org">{org?.name || 'Campus'}</div>
          </div>
        </div>

        <div className="sidebar-user">
          <div className="user-avatar">{user?.name?.[0]?.toUpperCase()}</div>
          <div>
            <div className="user-name">{user?.name}</div>
            <div className="user-role">Student</div>
          </div>
        </div>

        <nav className="sidebar-nav">
          {[
            { id: 'feed',          label: 'Community Feed',    icon: '📢' },
            { id: 'submit',        label: 'Submit Complaint',  icon: '✍️' },
            { id: 'my',            label: 'My Complaints',     icon: '📋' },
            { id: 'analytics',     label: 'My Analytics',      icon: '📊' },
            { id: 'notifications', label: `Notifications ${unreadCount > 0 ? `(${unreadCount})` : ''}`, icon: '🔔' },
          ].map(item => (
            <button key={item.id} className={`nav-item ${view === item.id ? 'active' : ''}`} onClick={() => setView(item.id)}>
              <span>{item.icon}</span> {item.label}
            </button>
          ))}
        </nav>

        <div className="sidebar-footer">
          <div className="workspace-badge">
            <span>🔗</span>
            <div>
              <div className="ws-label">Workspace</div>
              <div className="ws-code">{org?.workspace_code}</div>
            </div>
          </div>
          <button className="logout-btn" onClick={() => { logout(); navigate('/login'); }}>🚪 Sign Out</button>
        </div>
      </aside>

      {/* ── Main ────────────────────────────────────────────────────────── */}
      <main className="dash-main">

        {/* ── Community Feed ─────────────────────────────────────────────── */}
        {view === 'feed' && (
          <div className="dash-section">
            <div className="section-header">
              <div>
                <h2>📢 Community Feed</h2>
                <p>See what your fellow students are reporting. Click "I'm Also Affected" to amplify important issues.</p>
              </div>
            </div>

            {/* Filters */}
            <div className="filter-bar">
              <input className="search-input" placeholder="🔍 Search complaints..." value={search} onChange={e => setSearch(e.target.value)} />
              <select className="filter-select" value={catFilter} onChange={e => setCatFilter(e.target.value)}>
                {CATEGORIES.map(c => <option key={c}>{c}</option>)}
              </select>
              <select className="filter-select" value={statusFilter} onChange={e => setStatusFilter(e.target.value)}>
                {STATUSES.map(s => <option key={s}>{s}</option>)}
              </select>
            </div>

            {loading ? (
              <div className="loading-wrap"><div className="spinner" /></div>
            ) : displayComplaints.length === 0 ? (
              <div className="empty-state">🎉 No complaints match your filters. Campus is all good!</div>
            ) : (
              <div className="complaint-grid">
                {displayComplaints.map(c => (
                  <ComplaintCard key={c.id} c={c} onSupport={toggleSupport} currentUserId={user?.id} />
                ))}
              </div>
            )}
          </div>
        )}

        {/* ── Submit Complaint ───────────────────────────────────────────── */}
        {view === 'submit' && (
          <div className="dash-section">
            <div className="section-header">
              <div>
                <h2>✍️ Submit a Complaint</h2>
                <p>Our AI will analyze your complaint, categorize it, assign severity, and route it automatically.</p>
              </div>
            </div>
            <div className="form-card">
              <form onSubmit={submitComplaint}>
                <div className="form-group">
                  <label>Complaint Title</label>
                  <div className="input-wrap">
                    <span className="input-icon">📝</span>
                    <input
                      placeholder="Brief title of your issue..."
                      value={form.title}
                      onChange={e => setForm({ ...form, title: e.target.value })}
                      required minLength={5}
                    />
                  </div>
                </div>

                <div className="form-group">
                  <label>Detailed Description</label>
                  <textarea
                    className="form-textarea"
                    placeholder="Describe the issue in detail. The more specific you are, the better AI can analyze and route it..."
                    value={form.description}
                    onChange={e => setForm({ ...form, description: e.target.value })}
                    required minLength={10}
                    rows={5}
                  />
                </div>

                <label className="anon-toggle">
                  <input type="checkbox" checked={form.anonymous} onChange={e => setForm({ ...form, anonymous: e.target.checked })} />
                  <span>Submit anonymously</span>
                  <span className="anon-hint">(your name won't be shown publicly)</span>
                </label>

                <div className="ai-notice">
                  <span>🤖</span>
                  <div>
                    <strong>AI-Powered Analysis</strong>
                    <p>Your complaint will be automatically categorized, prioritized (Low→Critical), scored for severity (0–100), and routed to the right department.</p>
                  </div>
                </div>

                <button type="submit" className="auth-btn" disabled={submitting}>
                  {submitting ? <span className="btn-spinner" /> : '🚀 Submit & Analyze'}
                </button>
              </form>
            </div>
          </div>
        )}

        {/* ── My Complaints ──────────────────────────────────────────────── */}
        {view === 'my' && (
          <div className="dash-section">
            <div className="section-header">
              <div>
                <h2>📋 My Complaints</h2>
                <p>Track all complaints you have submitted.</p>
              </div>
              <button className="btn-outline" onClick={fetchMine}>🔄 Refresh</button>
            </div>

            {myComplaints.length === 0 ? (
              <div className="empty-state">
                <p>📭 You haven't submitted any complaints yet.</p>
                <button className="auth-btn small" onClick={() => setView('submit')}>✍️ Submit First Complaint</button>
              </div>
            ) : (
              <div className="complaint-grid">
                {myComplaints.map(c => (
                  <ComplaintCard key={c.id} c={c} onSupport={toggleSupport} currentUserId={user?.id} mine />
                ))}
              </div>
            )}
          </div>
        )}

        {/* ── Analytics ─────────────────────────────────────────────────── */}
        {view === 'analytics' && analytics && (
          <div className="dash-section">
            <div className="section-header">
              <h2>📊 My Activity</h2>
            </div>
            <div className="stats-grid">
              <StatCard icon="📝" label="Complaints Filed"   value={analytics.my_complaints}       color="#6366f1" />
              <StatCard icon="✅" label="Resolved"           value={analytics.my_resolved}         color="#22c55e" />
              <StatCard icon="⏳" label="Pending"            value={analytics.my_pending}          color="#f59e0b" />
              <StatCard icon="👊" label="Issues Supported"   value={analytics.my_supported_issues} color="#ec4899" />
            </div>

            <div className="analytics-row">
              <div className="analytics-card">
                <h3>Campus Resolution Rate</h3>
                <div className="big-stat">{analytics.org_resolution_rate}%</div>
                <div className="progress-bar">
                  <div className="progress-fill" style={{ width: `${analytics.org_resolution_rate}%`, background: '#22c55e' }} />
                </div>
              </div>

              <div className="analytics-card">
                <h3>Campus Sentiment</h3>
                {Object.entries(analytics.org_sentiment_distribution || {}).map(([s, c]) => (
                  <div key={s} className="sentiment-row">
                    <span>{s}</span>
                    <div className="mini-bar">
                      <div className="mini-fill" style={{ width: `${Math.min((c / (analytics.my_complaints || 1)) * 100, 100)}%`, background: s === 'Negative' ? '#ef4444' : s === 'Positive' ? '#22c55e' : '#f59e0b' }} />
                    </div>
                    <span>{c}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="section-header" style={{ marginTop: '1.5rem' }}>
              <h3>Recent Activity</h3>
            </div>
            <div className="recent-table">
              {(analytics.recent_complaints || []).map(c => (
                <div key={c.id} className="table-row">
                  <span className="cat-icon">{CATEGORY_ICONS[c.category] || '📌'}</span>
                  <span className="row-title">{c.title}</span>
                  <span className="status-pill" style={{ background: `${STATUS_COLORS[c.status]}22`, color: STATUS_COLORS[c.status] }}>{c.status}</span>
                  <span className="priority-dot" style={{ background: PRIORITY_COLORS[c.priority] }} />
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ── Notifications ─────────────────────────────────────────────── */}
        {view === 'notifications' && (
          <div className="dash-section">
            <div className="section-header">
              <h2>🔔 Notifications</h2>
              <button className="btn-outline" onClick={markAllRead}>✅ Mark All Read</button>
            </div>
            {notifications.length === 0 ? (
              <div className="empty-state">🔕 No notifications yet.</div>
            ) : (
              <div className="notif-list">
                {notifications.map(n => (
                  <div key={n.id} className={`notif-item ${n.is_read ? 'read' : 'unread'}`}>
                    <span className="notif-dot" />
                    <div>
                      <p>{n.message}</p>
                      <small>{new Date(n.created_at).toLocaleString()}</small>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}

/* ── Sub-components ──────────────────────────────────────────────────────── */

function ComplaintCard({ c, onSupport, currentUserId, mine = false }) {
  const isOwn = c.user_id === currentUserId;
  return (
    <div className="complaint-card">
      <div className="card-header">
        <div className="card-meta">
          <span className="cat-badge">{CATEGORY_ICONS[c.category] || '📌'} {c.category}</span>
          <span className="dept-badge">→ {c.assigned_department}</span>
        </div>
        <div className="card-right">
          <span className="priority-tag" style={{ background: `${PRIORITY_COLORS[c.priority]}22`, color: PRIORITY_COLORS[c.priority] }}>
            {c.priority}
          </span>
          <span className="status-tag" style={{ background: `${STATUS_COLORS[c.status]}22`, color: STATUS_COLORS[c.status] }}>
            {c.status}
          </span>
        </div>
      </div>

      <h3 className="card-title">{c.title}</h3>
      <p className="card-desc">{c.description.slice(0, 160)}{c.description.length > 160 ? '…' : ''}</p>

      {/* AI Scores */}
      <div className="score-row">
        <div className="score-item">
          <span className="score-label">Severity</span>
          <div className="score-bar">
            <div className="score-fill" style={{
              width: `${c.severity_score}%`,
              background: c.severity_score > 70 ? '#ef4444' : c.severity_score > 40 ? '#f59e0b' : '#22c55e'
            }} />
          </div>
          <span className="score-val">{c.severity_score}/100</span>
        </div>
        <div className="score-item">
          <span className="score-label">Impact</span>
          <span className="score-val impact">{c.impact_score.toFixed(1)}</span>
        </div>
      </div>

      {c.ai_recommendation && (
        <div className="ai-rec">
          <span>🤖</span>
          <p>{c.ai_recommendation}</p>
        </div>
      )}

      <div className="card-footer">
        <div className="footer-left">
          <span className="reporter">👤 {c.student_name}</span>
          <span className="date">🕐 {new Date(c.created_at).toLocaleDateString()}</span>
        </div>
        <div className="footer-actions">
          {c.support_count > 0 && <span className="support-count">👊 {c.support_count} affected</span>}
          {!isOwn && !mine && (
            <button
              className={`support-btn ${c.user_has_supported ? 'supported' : ''}`}
              onClick={() => onSupport(c.id)}
            >
              {c.user_has_supported ? '✅ Affected' : '👊 I\'m Also Affected'}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

function StatCard({ icon, label, value, color }) {
  return (
    <div className="stat-card" style={{ borderTopColor: color }}>
      <div className="stat-icon" style={{ color }}>{icon}</div>
      <div className="stat-value">{value ?? 0}</div>
      <div className="stat-label">{label}</div>
    </div>
  );
}
