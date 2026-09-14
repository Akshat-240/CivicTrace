import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getIncidents } from '../../services/api';
import {
  Clock,
  AlertTriangle,
  CheckCircle2,
  Download,
  ArrowRight,
  ShieldAlert,
  ChevronRight
} from 'lucide-react';
import './AdminSLAMonitoringPage.css';


const mockAdminSLAPage = {
  rules: [
    { priority: 'CRITICAL', response: '2h', resolution: '6h', escalation: 'Zone', color: '#EF4444' },
    { priority: 'HIGH', response: '4h', resolution: '24h', escalation: 'Dept.', color: '#F97316' },
    { priority: 'MEDIUM', response: '8h', resolution: '3d', escalation: 'Dept.', color: '#EAB308' },
    { priority: 'LOW', response: '24h', resolution: '7d', escalation: 'Dept.', color: '#3B82F6' }
  ],
  escalationPath: [
    { level: 'L1', title: 'Department Officer', desc: 'First response & field dispatch' },
    { level: 'L2', title: 'Zone Officer', desc: 'Escalated if 50% SLA elapsed without action' },
    { level: 'L3', title: 'Municipal Officer', desc: 'Immediate review on SLA breach' },
    { level: 'L4', title: 'Higher Authority', desc: 'Administrative penalty & governance review' }
  ],
  evidenceDecisions: [
    { state: 'FULLY_RESOLVED', label: 'Closes incident & meets SLA', color: '#10B981' },
    { state: 'NOT_RESOLVED', label: 'Issue remains present', color: '#EF4444' },
    { state: 'NO_EVIDENCE', label: 'No evidence submitted / unusable', color: '#6B7280' },
    { state: 'HUMAN_REVIEW', label: 'Requires human review', color: '#F59E0B' }
  ]
};

const AdminSLAMonitoringPage = () => {
  const navigate = useNavigate();
  const [selectedDept, setSelectedDept] = useState('All Departments');
  const [incidents, setIncidents] = useState([]);
  const [kpis, setKpis] = useState({ compliance: 0, breached: 0, atRisk: 0, open: 0 });

  const { rules, escalationPath, evidenceDecisions } = mockAdminSLAPage;

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await getIncidents(0, 500);
        const data = Array.isArray(response) ? response : (response.data || []);

        let complianceCount = 0;
        let breachedCount = 0;
        let atRiskCount = 0;
        let openCount = 0;

        const mapped = data.map(inc => {
          const isOpen = inc.status !== 'Resolved' && inc.status !== 'Closed';
          if (isOpen) openCount++;

          // Simulate SLA metrics
          let isBreached = false;
          let isAtRisk = false;
          if (isOpen) {
             const rand = Math.random();
             if (rand < 0.1) isBreached = true;
             else if (rand < 0.3) isAtRisk = true;
          } else {
             complianceCount++;
          }

          if (isBreached) breachedCount++;
          if (isAtRisk) atRiskCount++;

          return {
            id: inc.id || 'Unknown',
            rawId: inc.id,
            issue: inc.title || inc.category || 'Unknown Issue',
            ward: inc.address || 'Unknown Ward',
            department: inc.department || 'General',
            priority: inc.priority || 'Low',
            slaBreached: isBreached,
            slaAtRisk: isAtRisk,
            sla: isBreached ? 'Breached' : isAtRisk ? 'At Risk' : 'On Track'
          };
        });

        // Sort mapped so breached and at risk are at the top
        mapped.sort((a, b) => {
            if (a.slaBreached && !b.slaBreached) return -1;
            if (!a.slaBreached && b.slaBreached) return 1;
            if (a.slaAtRisk && !b.slaAtRisk) return -1;
            if (!a.slaAtRisk && b.slaAtRisk) return 1;
            return 0;
        });

        setIncidents(mapped);
        setKpis({
          compliance: data.length ? Math.round((complianceCount / data.length) * 100) : 100,
          breached: breachedCount,
          atRisk: atRiskCount,
          open: openCount
        });
      } catch (err) {
        console.error(err);
      }
    };
    fetchData();
  }, []);


  // Compute avg response time
  let totalHours = 0;
  let count = 0;
  incidents.forEach(inc => {
    if (inc.created_at && inc.updated_at && (inc.status === 'active' || inc.status === 'resolved')) {
      const created = new Date(inc.created_at);
      const updated = new Date(inc.updated_at);
      totalHours += (updated - created) / (1000 * 60 * 60);
      count++;
    }
  });
  const avgHrs = count > 0 ? totalHours / count : 2.23;
  const avgResponse = Math.floor(avgHrs) + 'h ' + Math.round((avgHrs % 1) * 60) + 'm';

  return (
    <div className="ct-admin-sla-page">
      {/* Filter and Export Bar */}
      <div className="ct-sla-filter-bar">
        <div className="ct-sla-filters-group">
          <span className="ct-filter-label">Reporting period</span>
          <select className="ct-sla-select">
            <option>Last 30 Days</option>
            <option>Last 7 Days</option>
            <option>Today</option>
          </select>

          <select
            value={selectedDept}
            onChange={(e) => setSelectedDept(e.target.value)}
            className="ct-sla-select"
          >
            <option>All Departments</option>
            <option>Roads Department</option>
            <option>Sanitation Department</option>
            <option>Electrical Department</option>
            <option>Water Supply</option>
          </select>

          <select className="ct-sla-select">
            <option>All Wards</option>
            <option>Ward 12</option>
            <option>Ward 8</option>
            <option>Ward 6</option>
          </select>

          <select className="ct-sla-select">
            <option>All Priorities</option>
            <option>Critical</option>
            <option>High</option>
            <option>Medium</option>
          </select>
        </div>

        <button
          type="button"
          className="ct-sla-export-btn"
          onClick={() => alert("Exporting SLA Compliance & Escalation Audit Report...")}
        >
          <Download size={15} />
          <span>Export SLA Report</span>
        </button>
      </div>

      {/* 5 KPI Metric Cards */}
      <div className="ct-sla-kpi-grid">
        <div className="ct-sla-kpi-card">
          <span className="ct-sla-dot green"></span>
          <div className="ct-sla-kpi-content">
            <span className="ct-sla-kpi-val">{kpis.compliance}%</span>
            <span className="ct-sla-kpi-lbl">SLA Compliance</span>
          </div>
        </div>

        <div className="ct-sla-kpi-card">
          <span className="ct-sla-dot red"></span>
          <div className="ct-sla-kpi-content">
            <span className="ct-sla-kpi-val">{kpis.breached}</span>
            <span className="ct-sla-kpi-lbl">SLA Breached</span>
          </div>
        </div>

        <div className="ct-sla-kpi-card">
          <span className="ct-sla-dot amber"></span>
          <div className="ct-sla-kpi-content">
            <span className="ct-sla-kpi-val">{kpis.atRisk}</span>
            <span className="ct-sla-kpi-lbl">At Risk</span>
          </div>
        </div>

        <div className="ct-sla-kpi-card">
          <span className="ct-sla-dot blue"></span>
          <div className="ct-sla-kpi-content">
            <span className="ct-sla-kpi-val">{kpis.open}</span>
            <span className="ct-sla-kpi-lbl">Open Incidents</span>
          </div>
        </div>

        <div className="ct-sla-kpi-card">
          <span className="ct-sla-dot teal"></span>
          <div className="ct-sla-kpi-content">
            <span className="ct-sla-kpi-val">{avgResponse}</span>
            <span className="ct-sla-kpi-lbl">Avg Response</span>
          </div>
        </div>
      </div>

      {/* Main Grid: Left Queue, Right SLA Config Rules */}
      <div className="ct-sla-main-grid">
        {/* Left: SLA Risk & Breach Queue */}
        <div className="ct-sla-card ct-sla-queue-box">
          <div className="ct-card-head">
            <h2 className="ct-card-title">SLA Risk & Breach Queue</h2>
            <p className="ct-card-subtitle">Incidents closest to breach, already overdue, or awaiting action</p>
          </div>

          <table className="ct-sla-table">
            <thead>
              <tr>
                <th>INCIDENT</th>
                <th>ISSUE / DEPARTMENT</th>
                <th>SLA STATE</th>
                <th>PRIORITY</th>
                <th className="text-right">ACTION</th>
              </tr>
            </thead>
            <tbody>
              {incidents.slice(0, 5).map((inc) => (
                <tr key={inc.id} onClick={() => navigate(`/admin/incidents/${inc.rawId}`)}>
                  <td className="font-bold text-primary">{inc.id}</td>
                  <td>
                    <div className="ct-table-issue-name">{inc.issue}</div>
                    <div className="ct-table-sub">{inc.ward} · {inc.department}</div>
                  </td>
                  <td>
                    <span className={`ct-sla-state-tag ${inc.slaBreached ? 'breached' : 'active'}`}>
                      {inc.slaBreached ? 'SLA breached' : inc.sla}
                    </span>
                  </td>
                  <td>
                    <span className={`ct-badge-pill ${inc.priority === 'Critical' ? 'badge-red' : inc.priority === 'High' ? 'badge-amber' : 'badge-yellow'}`}>
                      {inc.priority}
                    </span>
                  </td>
                  <td className="text-right" onClick={(e) => e.stopPropagation()}>
                    <button
                      type="button"
                      className="ct-sla-review-btn"
                      onClick={() => navigate(`/admin/incidents/${inc.rawId}`)}
                    >
                      <span>Review</span>
                      <ArrowRight size={13} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Right: Configurable Rules & Evidence */}
        <div className="ct-sla-rules-col">
          {/* Configurable Rules Card */}
          <div className="ct-sla-card">
            <h2 className="ct-card-title">Configurable SLA Rules</h2>
            <p className="ct-card-subtitle">MVP policy rules • not official government SLAs</p>

            <table className="ct-rules-table">
              <thead>
                <tr>
                  <th>PRIORITY</th>
                  <th>RESPONSE</th>
                  <th>RESOLUTION</th>
                  <th>ESCALATION</th>
                </tr>
              </thead>
              <tbody>
                {rules.map((rule) => (
                  <tr key={rule.priority}>
                    <td className="font-bold" style={{ color: rule.color }}>
                      ● {rule.priority}
                    </td>
                    <td>{rule.response}</td>
                    <td>{rule.resolution}</td>
                    <td>{rule.escalation}</td>
                  </tr>
                ))}
              </tbody>
            </table>

            <div className="ct-rules-footer-note">
              Due soon → notify. Deadline passed + unresolved → escalate.
            </div>

            <button
              type="button"
              className="ct-rules-config-btn"
              onClick={() => alert("Opening SLA Configuration Panel...")}
            >
              Authority-configured rules
            </button>
          </div>

          {/* Evidence -> SLA Decision */}
          <div className="ct-sla-card">
            <h2 className="ct-card-title">Evidence → SLA Decision</h2>
            <p className="ct-card-subtitle">
              Physical resolution evidence determines whether the incident can close.
            </p>

            <div className="ct-decision-pills">
              {evidenceDecisions.map((dec) => (
                <div key={dec.state} className="ct-decision-item">
                  <span className="ct-decision-pill-code" style={{ borderColor: dec.color, color: dec.color }}>
                    {dec.state}
                  </span>
                  <span className="ct-decision-pill-desc">{dec.label}</span>
                </div>
              ))}
            </div>

            <div className="ct-decision-warning">
              NOT_RESOLVED also keeps the incident open and triggers SLA escalation.
            </div>
          </div>
        </div>
      </div>

      {/* Automatic Escalation Path */}
      <div className="ct-sla-card ct-escalation-card">
        <div className="ct-escalation-header">
          <h2 className="ct-card-title">Automatic Escalation Path</h2>
          <p className="ct-card-subtitle">
            SLA breach creates an accountable escalation chain — not just a red badge.
          </p>
        </div>

        <div className="ct-escalation-stepper">
          {escalationPath.map((step, idx) => (
            <React.Fragment key={step.level}>
              <div className="ct-escalation-node">
                <div className="ct-node-level">{step.level}</div>
                <div className="ct-node-text-col">
                  <span className="ct-node-title">{step.title}</span>
                  <span className="ct-node-desc">{step.desc}</span>
                </div>
              </div>

              {idx < escalationPath.length - 1 && (
                <div className="ct-escalation-arrow">
                  <ArrowRight size={18} />
                </div>
              )}
            </React.Fragment>
          ))}
        </div>
      </div>
    </div>
  );
};

export default AdminSLAMonitoringPage;
