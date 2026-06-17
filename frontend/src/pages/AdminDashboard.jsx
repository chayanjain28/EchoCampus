import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';
import {
  Chart as ChartJS,
  ArcElement, Tooltip, Legend, CategoryScale, LinearScale,
  BarElement, LineElement, PointElement, Title, Filler
} from 'chart.js';
import { Doughnut, Bar, Line } from 'react-chartjs-2';

ChartJS.register(ArcElement, Tooltip, Legend, CategoryScale, LinearScale, BarElement, LineElement, PointElement, Title, Filler);

const PRIORITY_COLORS = { Low: '#22c55e', Medium: '#f59e0b', High: '#f97316', Critical: '#ef4444' };
const STATUS_COLORS   = { Pending: '#f59e0b', 'In Progress': '#3b82f6', Resolved: '#22c55e', Escalated: '#f97316', Rejected: '#6b7280' };
const CATEGORY_ICONS  = { Hostel: '🏠', Mess: '🍽️', WiFi: '📶', Transport: '🚌', Academic: '📚', Infrastructure: '🏗️', Security: '🔒', Other: '📌' };

const CHART_COLORS = ['#6366f1','#ec4899','#f59e0b','#22c55e','#3b82f6','#f97316','#8b5cf6','#14b8a6'];

export default function AdminDashboard() {
  const { user, org, logout, refreshOrg } = useAuth();
  const navigate = useNavigate();

  const [view, setView]                 = useState('overview');
  const [data, setData]                 = useState(null);
  const [complaints, setComplaints]     = useState([]);
  const [feedback, setFeedback]         = useState([]);
  const [users, setUsers]               = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading]           = useState(true);
  const [toast, setToast]               = useState('');
  const [selectedComplaint, setSelected] = useState(null);
  const [statusUpdateMap, setStatusMap] = useState({});

  // Filters
  const [catFilter, setCatFilter]       = useState('All');
  const [statusFilter, setStatusFilter] = useState('All');
  const [deptFilter, setDeptFilter]     = useState('All');
  const [search, setSearch]             = useState('');

  // Org settings
  const [orgForm, setOrgForm] = useState({ organization_name: '', organization_type: '', description: '' });
  const [inviteCode, setInviteCode] = useState(org?.invite_code || '');

  const showToast = (msg) => { setToast(msg); setTimeout(() => setToast(''), 3500); };

  /* ─── Data Fetchers ─────────────────────────────────────────────────── */
  const fetchAll = useCallback(async () => {
    setLoading(true);
    try {
      const [dashRes, compRes, fbRes, usrRes, notifRes] = await Promise.all([
        api.get('/analytics/dashboard'),
        api.get('/complaints/all'),
        api.get('/feedback/'),
        api.get('/auth/users'),
        api.get('/notifications/'),
      ]);
      setData(dashRes.data);
      setComplaints(compRes.data);
      setFeedback(fbRes.data);
      setUsers(usrRes.data);
      setNotifications(notifRes.data);
      setInviteCode(org?.invite_code || '');
      setOrgForm({ organization_name: org?.name || '', organization_type: org?.type || '', description: org?.description || '' });
    } catch (err) {
      console.error(err);
    } finally { setLoading(false); }
  }, [org]);

  useEffect(() => { fetchAll(); }, []);

  /* ─── Handlers ──────────────────────────────────────────────────────── */
  const updateStatus = async (id) => {
    const entry = statusUpdateMap[id];
    if (!entry?.status) return;
    try {
      await api.put(`/complaints/${id}/status`, { status: entry.status, assigned_to: entry.assigned_to });
      showToast('✅ Complaint status updated!');
      fetchAll();
      setSelected(null);
    } catch { showToast('❌ Update failed'); }
  };

  const saveOrgSettings = async (e) => {
    e.preventDefault();
    try {
      await api.put('/auth/organization/settings', orgForm);
      await refreshOrg();
      showToast('✅ Organization settings saved!');
    } catch { showToast('❌ Failed to save settings'); }
  };

  const regenerateInvite = async () => {
    try {
      const res = await api.post('/auth/organization/regenerate-invite');
      setInviteCode(res.data.invite_code);
      await refreshOrg();
      showToast('🔑 New invite code generated!');
    } catch { showToast('❌ Failed to regenerate'); }
  };

  /* ─── Filtered complaints ───────────────────────────────────────────── */
  const displayed = complaints.filter(c => {
    const mc = catFilter === 'All' || c.category === catFilter;
    const ms = statusFilter === 'All' || c.status === statusFilter;
    const md = deptFilter === 'All' || c.assigned_department === deptFilter;
    const mq = !search || c.title.toLowerCase().includes(search.toLowerCase());
    return mc && ms && md && mq;
  });

  const departments = [...new Set(complaints.map(c => c.assigned_department))];
  const unread = notifications.filter(n => !n.is_read).length;

  if (loading) return <div className="full-loading"><div className="spinner-lg" /><p>Loading Dashboard…</p></div>;

  return (
    <div className="dash-layout">
      {toast && <div className="toast">{toast}</div>}
      {selectedComplaint && <ComplaintModal c={selectedComplaint} onClose={() => setSelected(null)} statusMap={statusUpdateMap} setStatusMap={setStatusMap} onUpdate={updateStatus} />}

      {/* ── Sidebar ─────────────────────────────────────────────────────── */}
      <aside className="sidebar">
        <div className="sidebar-brand">
          <span className="brand-icon">🎓</span>
          <div>
            <div className="brand-name">EchoCampus <span>AI</span></div>
            <div className="brand-org">{org?.name}</div>
          </div>
        </div>

        <div className="sidebar-user">
          <div className="user-avatar admin-avatar">{user?.name?.[0]?.toUpperCase()}</div>
          <div>
            <div className="user-name">{user?.name}</div>
            <div className="user-role">Administrator</div>
          </div>
        </div>

        <nav className="sidebar-nav">
          {[
            { id: 'overview',      label: 'Overview',         icon: '📊' },
            { id: 'complaints',    label: 'Complaints',        icon: '📋' },
            { id: 'analytics',     label: 'Analytics',         icon: '📈' },
            { id: 'feedback',      label: 'Feedback',          icon: '⭐' },
            { id: 'users',         label: 'Team Members',      icon: '👥' },
            { id: 'settings',      label: 'Workspace Settings',icon: '⚙️' },
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
          <div className="invite-badge">
            <span>🔑</span>
            <div>
              <div className="ws-label">Invite Code</div>
              <div className="ws-code invite">{inviteCode}</div>
            </div>
          </div>
          <button className="logout-btn" onClick={() => { logout(); navigate('/login'); }}>🚪 Sign Out</button>
        </div>
      </aside>

      {/* ── Main ──────────────────────────────────────────────────────── */}
      <main className="dash-main">

        {/* ── Overview ──────────────────────────────────────────────── */}
        {view === 'overview' && data && (
          <div className="dash-section">
            <div className="section-header">
              <div>
                <h2>📊 Campus Intelligence Overview</h2>
                <p>Real-time welfare metrics for <strong>{org?.name}</strong></p>
              </div>
              <button className="btn-outline" onClick={fetchAll}>🔄 Refresh</button>
            </div>

            {/* Health Scores */}
            <div className="health-row">
              <HealthMeter label="Campus Health" value={data.campus_health_score} color="#22c55e" icon="🏥" />
              <HealthMeter label="Admin Efficiency" value={data.admin_efficiency_score} color="#6366f1" icon="⚡" />
              <HealthMeter label="Resolution Rate" value={data.resolution_rate} color="#f59e0b" icon="✅" />
              <HealthMeter label="Student Satisfaction" value={Math.round(data.student_satisfaction_index / 5 * 100)} color="#ec4899" icon="😊" />
            </div>

            {/* Key Stats */}
            <div className="stats-grid">
              <StatCard icon="📝" label="Total Complaints"     value={data.total_complaints}           color="#6366f1" />
              <StatCard icon="👥" label="Registered Students"  value={data.total_students}             color="#3b82f6" />
              <StatCard icon="✅" label="Resolved"             value={data.resolved_complaints}         color="#22c55e" />
              <StatCard icon="⚠️" label="Escalated"            value={data.escalated_complaints_count} color="#ef4444" />
              <StatCard icon="👊" label="Students Affected"    value={data.total_affected_students}    color="#ec4899" />
              <StatCard icon="🔁" label="Duplicate Groups"     value={data.duplicate_groups_count}     color="#f59e0b" />
              <StatCard icon="⏱️" label="Avg Resolution (hrs)" value={data.avg_resolution_time_hours}  color="#14b8a6" />
              <StatCard icon="🎯" label="Most Reported"        value={data.most_reported_service}      color="#8b5cf6" isText />
            </div>

            {/* High Impact Issues */}
            {data.high_impact_issues?.length > 0 && (
              <div className="high-impact-section">
                <h3>🔥 High Impact Issues (Action Required)</h3>
                <div className="impact-list">
                  {data.high_impact_issues.map(issue => (
                    <div key={issue.id} className="impact-item">
                      <span className="cat-icon">{CATEGORY_ICONS[issue.category] || '📌'}</span>
                      <div className="impact-info">
                        <strong>{issue.title}</strong>
                        <span className="priority-tag" style={{ background: `${PRIORITY_COLORS[issue.priority]}22`, color: PRIORITY_COLORS[issue.priority] }}>{issue.priority}</span>
                      </div>
                      <div className="impact-score-bar">
                        <div className="impact-fill" style={{ width: `${Math.min(issue.impact_score, 100)}%`, background: '#ef4444' }} />
                        <span>{issue.impact_score.toFixed(1)}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* CSSI */}
            <div className="cssi-section">
              <h3>📊 Campus Service Satisfaction Index (CSSI)</h3>
              <div className="cssi-grid">
                {(data.cssi || []).map(item => (
                  <div key={item.category} className="cssi-card">
                    <div className="cssi-icon">{CATEGORY_ICONS[item.category]}</div>
                    <div className="cssi-label">{item.category}</div>
                    <div className="cssi-score" style={{ color: item.score > 70 ? '#22c55e' : item.score > 40 ? '#f59e0b' : '#ef4444' }}>
                      {item.score}%
                    </div>
                    <div className="cssi-bar">
                      <div className="cssi-fill" style={{
                        width: `${item.score}%`,
                        background: item.score > 70 ? '#22c55e' : item.score > 40 ? '#f59e0b' : '#ef4444'
                      }} />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Department Workload */}
            {data.department_workload?.length > 0 && (
              <div className="chart-row">
                <div className="chart-card">
                  <h3>Department Workload</h3>
                  <Bar
                    data={{
                      labels: data.department_workload.map(d => d.department.replace(' Department','').replace(' Office','')),
                      datasets: [{ label: 'Complaints', data: data.department_workload.map(d => d.count), backgroundColor: CHART_COLORS, borderRadius: 6 }]
                    }}
                    options={{ responsive: true, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true, ticks: { color: '#94a3b8' } }, x: { ticks: { color: '#94a3b8' } } } }}
                  />
                </div>

                <div className="chart-card">
                  <h3>Monthly Trend</h3>
                  <Line
                    data={{
                      labels: (data.monthly_trend || []).map(m => m.month),
                      datasets: [{
                        label: 'Complaints',
                        data: (data.monthly_trend || []).map(m => m.count),
                        borderColor: '#6366f1', backgroundColor: 'rgba(99,102,241,0.15)',
                        tension: 0.4, fill: true, pointBackgroundColor: '#6366f1'
                      }]
                    }}
                    options={{ responsive: true, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true, ticks: { color: '#94a3b8' } }, x: { ticks: { color: '#94a3b8' } } } }}
                  />
                </div>
              </div>
            )}

            <div className="chart-row">
              <div className="chart-card small">
                <h3>Category Distribution</h3>
                <Doughnut
                  data={{
                    labels: Object.keys(data.category_distribution || {}),
                    datasets: [{ data: Object.values(data.category_distribution || {}), backgroundColor: CHART_COLORS, borderWidth: 0 }]
                  }}
                  options={{ responsive: true, plugins: { legend: { position: 'right', labels: { color: '#94a3b8', font: { size: 11 } } } } }}
                />
              </div>

              <div className="chart-card small">
                <h3>Priority Breakdown</h3>
                <Doughnut
                  data={{
                    labels: Object.keys(data.priority_distribution || {}),
                    datasets: [{ data: Object.values(data.priority_distribution || {}), backgroundColor: ['#22c55e','#f59e0b','#f97316','#ef4444'], borderWidth: 0 }]
                  }}
                  options={{ responsive: true, plugins: { legend: { position: 'right', labels: { color: '#94a3b8', font: { size: 11 } } } } }}
                />
              </div>
            </div>
          </div>
        )}

        {/* ── Complaints Management ────────────────────────────────── */}
        {view === 'complaints' && (
          <div className="dash-section">
            <div className="section-header">
              <div>
                <h2>📋 Complaint Management</h2>
                <p>{complaints.length} total complaints in this workspace</p>
              </div>
              <button className="btn-outline" onClick={fetchAll}>🔄 Refresh</button>
            </div>

            <div className="filter-bar">
              <input className="search-input" placeholder="🔍 Search..." value={search} onChange={e => setSearch(e.target.value)} />
              <select className="filter-select" value={catFilter} onChange={e => setCatFilter(e.target.value)}>
                {['All','Hostel','Mess','WiFi','Transport','Academic','Infrastructure','Security','Other'].map(c => <option key={c}>{c}</option>)}
              </select>
              <select className="filter-select" value={statusFilter} onChange={e => setStatusFilter(e.target.value)}>
                {['All','Pending','In Progress','Resolved','Escalated','Rejected'].map(s => <option key={s}>{s}</option>)}
              </select>
              <select className="filter-select" value={deptFilter} onChange={e => setDeptFilter(e.target.value)}>
                <option value="All">All Depts</option>
                {departments.map(d => <option key={d}>{d}</option>)}
              </select>
            </div>

            <div className="admin-complaint-list">
              {displayed.map(c => (
                <AdminComplaintRow key={c.id} c={c} onClick={() => setSelected(c)} />
              ))}
              {displayed.length === 0 && <div className="empty-state">No complaints match filters.</div>}
            </div>
          </div>
        )}

        {/* ── Analytics ───────────────────────────────────────────── */}
        {view === 'analytics' && data && (
          <div className="dash-section">
            <div className="section-header"><h2>📈 Deep Analytics</h2></div>
            <div className="chart-row">
              <div className="chart-card">
                <h3>Sentiment Distribution</h3>
                <Doughnut
                  data={{
                    labels: Object.keys(data.sentiment_distribution || {}),
                    datasets: [{ data: Object.values(data.sentiment_distribution || {}), backgroundColor: ['#22c55e','#f59e0b','#ef4444'], borderWidth: 0 }]
                  }}
                  options={{ responsive: true, plugins: { legend: { position: 'right', labels: { color: '#94a3b8' } } } }}
                />
              </div>
              <div className="chart-card">
                <h3>Status Distribution</h3>
                <Bar
                  data={{
                    labels: Object.keys(data.status_distribution || {}),
                    datasets: [{ data: Object.values(data.status_distribution || {}), backgroundColor: ['#f59e0b','#3b82f6','#22c55e','#f97316','#6b7280'], borderRadius: 6 }]
                  }}
                  options={{ responsive: true, plugins: { legend: { display: false } }, scales: { y: { ticks: { color: '#94a3b8' } }, x: { ticks: { color: '#94a3b8' } } } }}
                />
              </div>
            </div>

            <div className="cssi-section" style={{ marginTop: '1.5rem' }}>
              <h3>Department Satisfaction (CSSI)</h3>
              <div className="cssi-table">
                {(data.cssi || []).map(item => (
                  <div key={item.category} className="cssi-row">
                    <span className="cssi-cat">{CATEGORY_ICONS[item.category]} {item.category}</span>
                    <div className="cssi-progress">
                      <div className="cssi-track">
                        <div className="cssi-fill" style={{
                          width: `${item.score}%`,
                          background: item.score > 70 ? 'linear-gradient(90deg,#22c55e,#16a34a)' : item.score > 40 ? 'linear-gradient(90deg,#f59e0b,#d97706)' : 'linear-gradient(90deg,#ef4444,#dc2626)'
                        }} />
                      </div>
                    </div>
                    <span className="cssi-val" style={{ color: item.score > 70 ? '#22c55e' : item.score > 40 ? '#f59e0b' : '#ef4444' }}>{item.score}%</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* ── Feedback ────────────────────────────────────────────── */}
        {view === 'feedback' && (
          <div className="dash-section">
            <div className="section-header"><h2>⭐ Student Feedback</h2></div>
            <div className="feedback-grid">
              {feedback.map(fb => (
                <div key={fb.id} className="feedback-card">
                  <div className="fb-header">
                    <span className="fb-student">{fb.student_name}</span>
                    <span className="fb-cat">{fb.category}</span>
                    <div className="stars">{'⭐'.repeat(fb.rating)}{'☆'.repeat(5 - fb.rating)}</div>
                  </div>
                  <p className="fb-msg">{fb.message}</p>
                  <small className="fb-date">{new Date(fb.created_at).toLocaleDateString()}</small>
                </div>
              ))}
              {feedback.length === 0 && <div className="empty-state">No feedback yet.</div>}
            </div>
          </div>
        )}

        {/* ── Users ───────────────────────────────────────────────── */}
        {view === 'users' && (
          <div className="dash-section">
            <div className="section-header">
              <div>
                <h2>👥 Team Members</h2>
                <p>{users.length} members in {org?.name}</p>
              </div>
            </div>
            <div className="users-table">
              <div className="table-head">
                <span>Name</span><span>Email</span><span>Role</span><span>Joined</span>
              </div>
              {users.map(u => (
                <div key={u.id} className="table-row">
                  <span><div className="user-avatar-sm">{u.name?.[0]?.toUpperCase()}</div> {u.name}</span>
                  <span>{u.email}</span>
                  <span><span className={`role-badge role-${u.role}`}>{u.role}</span></span>
                  <span>{new Date(u.created_at).toLocaleDateString()}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ── Workspace Settings ──────────────────────────────────── */}
        {view === 'settings' && (
          <div className="dash-section">
            <div className="section-header"><h2>⚙️ Workspace Settings</h2></div>
            <div className="settings-grid">
              <div className="settings-card">
                <h3>Organization Details</h3>
                <form onSubmit={saveOrgSettings} className="auth-form">
                  <div className="form-group">
                    <label>Organization Name</label>
                    <div className="input-wrap">
                      <span className="input-icon">🏛️</span>
                      <input value={orgForm.organization_name} onChange={e => setOrgForm({...orgForm, organization_name: e.target.value})} />
                    </div>
                  </div>
                  <div className="form-group">
                    <label>Organization Type</label>
                    <div className="input-wrap">
                      <span className="input-icon">📋</span>
                      <select value={orgForm.organization_type} onChange={e => setOrgForm({...orgForm, organization_type: e.target.value})}>
                        {['University','College','School','Hostel','Student Club','Coaching Institute'].map(t => <option key={t}>{t}</option>)}
                      </select>
                    </div>
                  </div>
                  <div className="form-group">
                    <label>Description</label>
                    <textarea className="form-textarea" rows={3} value={orgForm.description} onChange={e => setOrgForm({...orgForm, description: e.target.value})} />
                  </div>
                  <button type="submit" className="auth-btn">💾 Save Settings</button>
                </form>
              </div>

              <div className="settings-card">
                <h3>Invite Code Management</h3>
                <p className="settings-hint">Share this invite code with students so they can join your workspace.</p>
                <div className="invite-display">
                  <span className="big-code">{inviteCode}</span>
                  <button className="btn-copy" onClick={() => { navigator.clipboard.writeText(inviteCode); showToast('📋 Copied!'); }}>📋 Copy</button>
                </div>
                <div className="workspace-info">
                  <div><strong>Workspace Code:</strong> <code>{org?.workspace_code}</code></div>
                  <div><strong>Organization Type:</strong> {org?.type}</div>
                  <div><strong>Members:</strong> {users.length}</div>
                </div>
                <button className="btn-danger" onClick={regenerateInvite}>🔄 Regenerate Invite Code</button>
                <p className="danger-hint">⚠️ Old invite code will stop working immediately.</p>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

/* ── Sub-components ──────────────────────────────────────────────────────── */

function AdminComplaintRow({ c, onClick }) {
  return (
    <div className="admin-complaint-row" onClick={onClick}>
      <div className="row-left">
        <span className="cat-icon">{CATEGORY_ICONS[c.category] || '📌'}</span>
        <div>
          <div className="row-title">{c.title}</div>
          <div className="row-meta">
            <span>{c.student_name}</span>
            <span>→ {c.assigned_department}</span>
            <span>👊 {c.support_count}</span>
            <span>📅 {new Date(c.created_at).toLocaleDateString()}</span>
          </div>
        </div>
      </div>
      <div className="row-right">
        <div className="severity-badge" style={{ background: c.severity_score > 70 ? '#ef444422' : c.severity_score > 40 ? '#f59e0b22' : '#22c55e22', color: c.severity_score > 70 ? '#ef4444' : c.severity_score > 40 ? '#f59e0b' : '#22c55e' }}>
          ⚡ {c.severity_score}
        </div>
        <span className="priority-tag" style={{ background: `${PRIORITY_COLORS[c.priority]}22`, color: PRIORITY_COLORS[c.priority] }}>{c.priority}</span>
        <span className="status-tag" style={{ background: `${STATUS_COLORS[c.status]}22`, color: STATUS_COLORS[c.status] }}>{c.status}</span>
        <span className="view-btn">→</span>
      </div>
    </div>
  );
}

function ComplaintModal({ c, onClose, statusMap, setStatusMap, onUpdate }) {
  const entry = statusMap[c.id] || { status: c.status, assigned_to: c.assigned_to || '' };
  const update = (field, val) => setStatusMap({ ...statusMap, [c.id]: { ...entry, [field]: val } });

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-card" onClick={e => e.stopPropagation()}>
        <button className="modal-close" onClick={onClose}>✕</button>
        <h2 className="modal-title">{c.title}</h2>

        <div className="modal-meta">
          <span className="cat-badge">{CATEGORY_ICONS[c.category]} {c.category}</span>
          <span className="dept-badge">→ {c.assigned_department}</span>
          <span className="priority-tag" style={{ background: `${PRIORITY_COLORS[c.priority]}22`, color: PRIORITY_COLORS[c.priority] }}>{c.priority}</span>
        </div>

        <p className="modal-desc">{c.description}</p>

        <div className="modal-scores">
          <div className="mscore"><label>Severity Score</label><div className="mscore-bar"><div className="mscore-fill" style={{ width: `${c.severity_score}%`, background: c.severity_score > 70 ? '#ef4444' : c.severity_score > 40 ? '#f59e0b' : '#22c55e' }} /></div><span>{c.severity_score}/100</span></div>
          <div className="mscore"><label>Impact Score</label><strong>{c.impact_score?.toFixed(1)}</strong></div>
          <div className="mscore"><label>Student Supporters</label><strong>👊 {c.support_count}</strong></div>
        </div>

        {c.ai_recommendation && (
          <div className="ai-rec modal-rec">
            <span>🤖 AI Recommendation</span>
            <p>{c.ai_recommendation}</p>
          </div>
        )}

        <div className="modal-form">
          <div className="form-group">
            <label>Update Status</label>
            <select className="filter-select full-w" value={entry.status} onChange={e => update('status', e.target.value)}>
              {['Pending','In Progress','Resolved','Escalated','Rejected'].map(s => <option key={s}>{s}</option>)}
            </select>
          </div>
          <div className="form-group">
            <label>Assign To</label>
            <div className="input-wrap">
              <span className="input-icon">👤</span>
              <input placeholder="Officer name..." value={entry.assigned_to} onChange={e => update('assigned_to', e.target.value)} />
            </div>
          </div>
          <button className="auth-btn" onClick={() => onUpdate(c.id)}>💾 Save Changes</button>
        </div>
      </div>
    </div>
  );
}

function HealthMeter({ label, value, color, icon }) {
  const clamp = Math.min(Math.max(value || 0, 0), 100);
  const r = 36, circ = 2 * Math.PI * r;
  const offset = circ - (clamp / 100) * circ;
  return (
    <div className="health-card">
      <svg width="90" height="90" viewBox="0 0 90 90">
        <circle cx="45" cy="45" r={r} fill="none" stroke="#1e293b" strokeWidth="8" />
        <circle cx="45" cy="45" r={r} fill="none" stroke={color} strokeWidth="8"
          strokeDasharray={circ} strokeDashoffset={offset}
          strokeLinecap="round" transform="rotate(-90 45 45)" style={{ transition: '0.6s ease' }} />
        <text x="45" y="49" textAnchor="middle" fill={color} fontSize="14" fontWeight="700">{clamp}%</text>
      </svg>
      <div className="health-icon">{icon}</div>
      <div className="health-label">{label}</div>
    </div>
  );
}

function StatCard({ icon, label, value, color, isText = false }) {
  return (
    <div className="stat-card" style={{ borderTopColor: color }}>
      <div className="stat-icon" style={{ color }}>{icon}</div>
      <div className="stat-value">{isText ? value : (value ?? 0)}</div>
      <div className="stat-label">{label}</div>
    </div>
  );
}
