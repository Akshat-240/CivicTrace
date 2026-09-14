import React from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  ArrowRight, 
  Plus, 
  Clock, 
  CheckCircle2, 
  AlertCircle, 
  Activity,
  FileText
} from 'lucide-react';
import { 
  mockCitizenStats, 
  mockCitizenActiveReports, 
  mockCitizenActivity 
} from '../../data/mockData';
import './CitizenDashboardPage.css';

export default function CitizenDashboardPage() {
  const navigate = useNavigate();

  return (
    <div className="citizen-dash-container">
      {/* 3 Metric Stat Cards */}
      <div className="citizen-stats-row">
        <div className="citizen-stat-card">
          <span className="citizen-stat-value">{mockCitizenStats.activeReports}</span>
          <span className="citizen-stat-label">Active Reports</span>
        </div>

        <div className="citizen-stat-card">
          <span className="citizen-stat-value">{mockCitizenStats.inProgress}</span>
          <span className="citizen-stat-label">In Progress</span>
        </div>

        <div className="citizen-stat-card">
          <span className="citizen-stat-value">{mockCitizenStats.resolved}</span>
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
            {mockCitizenActiveReports.map((report) => (
              <div 
                key={report.id} 
                className="citizen-report-card"
                onClick={() => navigate('/citizen/track')}
              >
                <div className="citizen-report-card-left">
                  <span className={`citizen-status-pill ${report.status === 'In Progress' ? 'amber' : 'blue'}`}>
                    {report.status}
                  </span>
                  <h3 className="citizen-report-card-title">{report.title}</h3>
                  <span className="citizen-report-card-meta">
                    {report.category} · {report.reportedTime}
                  </span>
                </div>

                <div className="citizen-report-card-right">
                  <span className="citizen-report-dept">{report.department}</span>
                  <span className="citizen-report-id">{report.id}</span>
                  <ArrowRight size={16} className="citizen-arrow-icon" />
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Right Column: Recent Activity */}
        <section className="citizen-dash-panel recent-activity-panel">
          <div className="citizen-panel-header">
            <h2 className="citizen-panel-title">Recent Activity</h2>
            <p className="citizen-panel-subtitle">Latest updates on your reports</p>
          </div>

          <div className="citizen-activity-timeline">
            {mockCitizenActivity.map((act) => (
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
                    onClick={() => navigate('/citizen/track')}
                  >
                    {act.reportId}
                  </span>
                </div>
              </div>
            ))}
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
