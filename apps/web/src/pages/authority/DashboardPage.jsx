import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import PageHeader from '../../components/layout/PageHeader';
import PriorityBadge from '../../components/common/PriorityBadge';
import Modal from '../../components/common/Modal';
import { mockStats, mockIncidents } from '../../data/mockData';
import './DashboardPage.css';

const DashboardPage = () => {
  const navigate = useNavigate();
  const [selectedIncident, setSelectedIncident] = useState(null);

  const priorityQueueIncidents = mockIncidents.filter(inc => 
    ["CT-INC-024", "CT-INC-021", "CT-INC-019", "CT-INC-017"].includes(inc.id)
  );

  return (
    <div className="ct-dashboard-page">
      <PageHeader 
        title="Authority Dashboard"
        subtitle="Monitor incoming incidents, assignments, SLA risk and verification work."
      />

      {/* Top 4 Metrics Summary Card */}
      <div className="ct-metrics-card">
        <div className="ct-metric-col">
          <div className="ct-metric-value">{mockStats.criticalHigh}</div>
          <div className="ct-metric-label">Critical / High</div>
        </div>
        <div className="ct-metric-col">
          <div className="ct-metric-value">{mockStats.openIncidents}</div>
          <div className="ct-metric-label">Open Incidents</div>
        </div>
        <div className="ct-metric-col">
          <div className="ct-metric-value">{mockStats.slaAtRisk}</div>
          <div className="ct-metric-label">SLA At Risk</div>
        </div>
        <div className="ct-metric-col">
          <div className="ct-metric-value">{mockStats.verificationPending}</div>
          <div className="ct-metric-label">Verification Pending</div>
        </div>
      </div>

      {/* Two Column Section */}
      <div className="ct-dashboard-grid">
        {/* Left: Priority Queue */}
        <div className="ct-card ct-priority-card">
          <div className="ct-card-head">
            <h2 className="ct-card-title">Priority Queue</h2>
            <p className="ct-card-desc">Incidents requiring attention first</p>
          </div>

          <div className="ct-priority-list">
            {priorityQueueIncidents.map((incident) => (
              <div 
                key={incident.id} 
                className="ct-priority-row"
                onClick={() => setSelectedIncident(incident)}
              >
                <div className="ct-row-id">{incident.id}</div>
                <div className="ct-row-title">{incident.title}</div>
                <div className="ct-row-right">
                  <PriorityBadge priority={incident.priority} />
                  <span className="ct-row-sla">{incident.slaRemaining}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Right: SLA & Workflow */}
        <div className="ct-card ct-workflow-card">
          <div className="ct-card-head">
            <h2 className="ct-card-title">SLA & Workflow</h2>
          </div>

          <div className="ct-sla-table">
            <div className="ct-sla-row">
              <span className="ct-sla-name">On track</span>
              <span className="ct-sla-num ct-text-green">{mockStats.slaMetrics.onTrack}</span>
            </div>
            <div className="ct-sla-row">
              <span className="ct-sla-name">Due soon</span>
              <span className="ct-sla-num ct-text-orange">{mockStats.slaMetrics.dueSoon}</span>
            </div>
            <div className="ct-sla-row">
              <span className="ct-sla-name">Overdue</span>
              <span className="ct-sla-num ct-text-red">{mockStats.slaMetrics.overdue}</span>
            </div>
            <div className="ct-sla-row">
              <span className="ct-sla-name">Human review</span>
              <span className="ct-sla-num ct-text-blue">{mockStats.slaMetrics.humanReview}</span>
            </div>
          </div>

          <div className="ct-recent-activity">
            <div className="ct-activity-title">Recent activity</div>
            <ul className="ct-activity-list">
              {mockStats.recentActivity.map((act, index) => (
                <li key={index} className="ct-activity-item">{act}</li>
              ))}
            </ul>
          </div>
        </div>
      </div>

      {/* Incident Details Modal */}
      <Modal
        isOpen={!!selectedIncident}
        onClose={() => setSelectedIncident(null)}
        title={`Incident Details: ${selectedIncident?.id}`}
      >
        {selectedIncident && (
          <div className="ct-modal-incident">
            <div className="ct-modal-badges">
              <PriorityBadge priority={selectedIncident.priority} />
              <span className="ct-modal-status">{selectedIncident.status}</span>
              <span className="ct-modal-sla">{selectedIncident.slaRemaining}</span>
            </div>

            <h3 className="ct-modal-incident-title">{selectedIncident.title}</h3>
            <p className="ct-modal-desc">{selectedIncident.description}</p>

            <div className="ct-modal-grid">
              <div className="ct-modal-field">
                <span className="ct-field-label">Category</span>
                <span className="ct-field-value">{selectedIncident.category}</span>
              </div>
              <div className="ct-modal-field">
                <span className="ct-field-label">Zone</span>
                <span className="ct-field-value">{selectedIncident.zone}</span>
              </div>
              <div className="ct-modal-field">
                <span className="ct-field-label">Location</span>
                <span className="ct-field-value">{selectedIncident.location} ({selectedIncident.subLocation})</span>
              </div>
              <div className="ct-modal-field">
                <span className="ct-field-label">Assigned Team</span>
                <span className="ct-field-value">{selectedIncident.assignedTeam || 'Unassigned'}</span>
              </div>
              <div className="ct-modal-field">
                <span className="ct-field-label">Reported At</span>
                <span className="ct-field-value">{selectedIncident.reportedAt}</span>
              </div>
            </div>

            <div className="ct-modal-actions">
              <button 
                type="button" 
                className="btn btn-outline"
                onClick={() => setSelectedIncident(null)}
              >
                Close
              </button>
              <button 
                type="button" 
                className="btn btn-primary"
                onClick={() => {
                  setSelectedIncident(null);
                  navigate('/authority/assignment');
                }}
              >
                Assign Team / Officer
              </button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
};

export default DashboardPage;
