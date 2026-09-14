import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ArrowRight,
  Plus,
  Clock,
  CheckCircle2,
  AlertCircle,
  Activity,
  FileText,
  Loader2
} from 'lucide-react';
import { getIncidents, getIncidentTimeline } from '../../services/api';
import './CitizenDashboardPage.css';

export default function CitizenDashboardPage() {
  const navigate = useNavigate();
  const citizenId = localStorage.getItem('ct_user_id');

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [stats, setStats] = useState({ active: 0, inProgress: 0, resolved: 0 });
  const [activeReports, setActiveReports] = useState([]);
  const [recentActivity, setRecentActivity] = useState([]);

  useEffect(() => {
    if (!citizenId) {
      navigate('/login');
      return;
    }

    async function loadDashboard() {
      try {
        setLoading(true);
        const response = await getIncidents(0, 100, citizenId);
        const incidents = response?.data || [];

        // Calculate stats
        let activeCount = 0;
        let inProgressCount = 0;
        let resolvedCount = 0;

        const activeList = [];

        incidents.forEach(inc => {
          const st = (inc.status || '').toLowerCase();
          if (st === 'resolved' || st === 'closed') {
            resolvedCount++;
          } else {
            activeCount++;
            if (st === 'active' || st === 'under_review') {
              inProgressCount++;
            }
            activeList.push(inc);
          }
        });

        setStats({ active: activeCount, inProgress: inProgressCount, resolved: resolvedCount });
        setActiveReports(activeList.sort((a,b) => new Date(b.created_at) - new Date(a.created_at)).slice(0, 5));

        // Load timeline for top 3 recent incidents
        const recent = [...incidents].sort((a, b) => new Date(b.created_at) - new Date(a.created_at)).slice(0, 3);
        const activityItems = [];

        for (const inc of recent) {
          try {
             const tl = await getIncidentTimeline(inc.id);
             if (tl && tl.length > 0) {
                const lastEvent = tl[tl.length - 1];
                activityItems.push({
                   id: lastEvent.id,
                   time: new Date(lastEvent.created_at).toLocaleString(),
                   title: lastEvent.description || `Status changed to ${lastEvent.to_status}`,
                   reportId: inc.reference_number || inc.id.substring(0, 8),
                   incidentId: inc.id,
                   timestamp: new Date(lastEvent.created_at).getTime()
                });
             }
          } catch(e) {
             console.error("Failed to load timeline for", inc.id);
          }
        }

        activityItems.sort((a, b) => b.timestamp - a.timestamp);
        setRecentActivity(activityItems.slice(0, 5));

      } catch (err) {
        console.error("Dashboard error:", err);
        setError("Failed to load dashboard data. Please try again later.");
      } finally {
        setLoading(false);
      }
    }

    loadDashboard();
  }, [citizenId, navigate]);

  if (loading) {
    return (
      <div className="citizen-dash-container" style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '60vh' }}>
        <Loader2 className="spinner" size={32} style={{ animation: 'spin 1s linear infinite', color: '#3B82F6' }} />
      </div>
    );
  }

  if (error) {
    return (
      <div className="citizen-dash-container" style={{ padding: '2rem', color: '#EF4444' }}>
        <AlertCircle size={24} style={{ marginBottom: '1rem' }} />
        <p>{error}</p>
      </div>
    );
  }

  return (
    <div className="citizen-dash-container">
      {/* 3 Metric Stat Cards */}
      <div className="citizen-stats-row">
        <div className="citizen-stat-card">
          <span className="citizen-stat-value">{stats.active}</span>
          <span className="citizen-stat-label">Active Reports</span>
        </div>

        <div className="citizen-stat-card">
          <span className="citizen-stat-value">{stats.inProgress}</span>
          <span className="citizen-stat-label">In Progress</span>
        </div>

        <div className="citizen-stat-card">
          <span className="citizen-stat-value">{stats.resolved}</span>
          <span className="citizen-stat-label">Resolved</span>
        </div>
      </div>

      {/* Main 2-column Grid */}
      <div className="citizen-dash-grid">
        {/* Left Column: Your Active Reports */}
        <section className="citizen-dash-panel active-reports-panel">
          <div className="citizen-panel-header">
            <h2 className="citizen-panel-title">Your Active Reports</h2>
            <p className="citizen-panel-subtitle">Track the issues currently awaiting action or verification.</p>
          </div>

          <div className="citizen-active-reports-list">
            {activeReports.length === 0 ? (
              <div style={{ padding: '2rem', textAlign: 'center', color: '#94A3B8' }}>
                <CheckCircle2 size={32} style={{ margin: '0 auto 1rem auto', opacity: 0.5 }} />
                <p>No active reports at the moment.</p>
              </div>
            ) : (
              activeReports.map((report) => {
                const st = (report.status || '').toLowerCase();
                const isAmber = st === 'active' || st === 'under_review';

                return (
                  <div
                    key={report.id}
                    className="citizen-report-card"
                    onClick={() => navigate(`/citizen/track?id=${report.id}`)}
                  >
                    <div className="citizen-report-card-left">
                      <span className={`citizen-status-pill ${isAmber ? 'amber' : 'blue'}`}>
                        {report.status}
                      </span>
                      <h3 className="citizen-report-card-title">{report.title || (report.issue_type + ' Issue')}</h3>
                      <span className="citizen-report-card-meta">
                        {report.issue_type} • {new Date(report.created_at).toLocaleDateString()}
                      </span>
                    </div>

                    <div className="citizen-report-card-right">
                      <span className="citizen-report-dept">{report.authority?.name || 'Pending Assignment'}</span>
                      <span className="citizen-report-id">{report.reference_number || report.id.substring(0, 8)}</span>
                      <ArrowRight size={16} className="citizen-arrow-icon" />
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </section>

        {/* Right Column: Recent Activity */}
        <section className="citizen-dash-panel recent-activity-panel">
          <div className="citizen-panel-header">
            <h2 className="citizen-panel-title">Recent Activity</h2>
            <p className="citizen-panel-subtitle">Latest updates on your reports</p>
          </div>

          <div className="citizen-activity-timeline">
            {recentActivity.length === 0 ? (
              <div style={{ padding: '2rem', textAlign: 'center', color: '#94A3B8' }}>
                <Activity size={32} style={{ margin: '0 auto 1rem auto', opacity: 0.5 }} />
                <p>No recent activity.</p>
              </div>
            ) : (
              recentActivity.map((act) => (
                <div key={act.id} className="citizen-activity-item">
                  <div className="citizen-activity-dot-col">
                    <div className="citizen-activity-dot"></div>
                    <div className="citizen-activity-line"></div>
                  </div>

                  <div className="citizen-activity-content">
                    <span className="citizen-activity-time">{act.time}</span>
                    <p className="citizen-activity-text">{act.title}</p>
                    <span
                      className="citizen-activity-tag"
                      onClick={() => navigate(`/citizen/track?id=${act.incidentId}`)}
                      style={{ cursor: 'pointer' }}
                    >
                      {act.reportId}
                    </span>
                  </div>
                </div>
              ))
            )}
          </div>
        </section>
      </div>

      {/* Bottom CTA Card */}
      <div className="citizen-need-report-card">
        <div className="need-report-text">
          <h3 className="need-report-title">Need to report something?</h3>
          <p className="need-report-desc">Capture evidence, add a description, and we will route it to the right authority.</p>
        </div>

        <button
          type="button"
          className="need-report-btn"
          onClick={() => navigate('/citizen/report')}
        >
          <Plus size={16} />
          <span>Report an Issue</span>
        </button>
      </div>
    </div>
  );
}
