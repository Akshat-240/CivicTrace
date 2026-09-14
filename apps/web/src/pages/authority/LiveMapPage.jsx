import React, { useState, useEffect } from 'react';
import PageHeader from '../../components/layout/PageHeader';
import PriorityBadge from '../../components/common/PriorityBadge';
import Modal from '../../components/common/Modal';
import { getIncidents, getCurrentUser } from '../../services/api';
import './LiveMapPage.css';

const LiveMapPage = () => {
  const [activeIncident, setActiveIncident] = useState(null);
  const [showEscalationModal, setShowEscalationModal] = useState(false);
  const [incidents, setIncidents] = useState([]);

  useEffect(() => {
    async function loadData() {
      try {
        const user = await getCurrentUser();
        const authId = user?.authority_id;
        if (!authId) return;
        const res = await getIncidents(0, 100, null, authId);
        setIncidents(res?.data || []);
      } catch (err) {
        console.error(err);
      }
    }
    loadData();
  }, []);

  const stats = {
    critical: incidents.filter(i => i.priority_level === 'critical').length,
    high: incidents.filter(i => i.priority_level === 'high').length,
    medium: incidents.filter(i => i.priority_level === 'medium').length,
    overdue: incidents.filter(i => i.accountability_state === 'overdue').length,
  };

  const escalationQueue = incidents
    .filter(i => ['critical', 'high'].includes(i.priority_level) || i.accountability_state === 'overdue')
    .slice(0, 5)
    .map(item => ({
      id: item.reference_number || (item.id ? item.id.substring(0, 8).toUpperCase() : 'UNKNOWN'),
      title: item.title || item.issue_type?.replace(/_/g, ' ')?.toUpperCase() || 'Incident',
      zone: item.jurisdiction?.name || 'Unknown Zone',
      assignedTeam: item.authority?.name || 'Not assigned',
      priority: item.priority_level?.toUpperCase() || 'PENDING',
      slaRemaining: item.accountability_state ? item.accountability_state.toUpperCase() : 'Not available',
    }));

  const mapMarkers = [
    {
      id: "CT-INC-024",
      title: "Large pothole on MG Road",
      color: "#2563EB",
      top: "28%",
      left: "26%",
      priority: "HIGH",
      status: "In Progress",
      sla: "18h remaining",
      zone: "Hazratganj"
    },
    {
      id: "CT-INC-021",
      title: "Main line water leakage",
      color: "#DC2626",
      top: "32%",
      left: "74%",
      priority: "CRITICAL",
      status: "Assigned",
      sla: "2h remaining (At Risk)",
      zone: "Aliganj"
    },
    {
      id: "CT-INC-019",
      title: "Streetlight not working",
      color: "#D97706",
      top: "54%",
      left: "48%",
      priority: "MEDIUM",
      status: "Awaiting Verification",
      sla: "31h remaining",
      zone: "Gomti Nagar"
    },
    {
      id: "CT-INC-017",
      title: "Garbage accumulation",
      color: "#DC2626",
      top: "75%",
      left: "24%",
      priority: "HIGH",
      status: "Open",
      sla: "7h remaining",
      zone: "Indira Nagar"
    },
    {
      id: "CT-INC-016",
      title: "Broken drain cover",
      color: "#2563EB",
      top: "68%",
      left: "81%",
      priority: "MEDIUM",
      status: "Open",
      sla: "24h remaining",
      zone: "Mahanagar"
    }
  ];

  return (
    <div className="ct-livemap-page">
      <PageHeader
        title="Live Map + SLA Monitor"
        subtitle="See where incidents are concentrated and which deadlines are at risk."
      />

      <div className="ct-livemap-grid">
        {/* Left: Live Incident Map */}
        <div className="ct-card ct-map-card">
          <div className="ct-card-head">
            <h2 className="ct-card-title">Live Incident Map</h2>
            <p className="ct-card-desc">Click markers to inspect incident status and SLA risk</p>
          </div>

          <div className="ct-map-viewport">
            <div className="ct-map-watermark">MAP</div>
            <div className="ct-map-grid-overlay"></div>

            {/* City Landmarks for realism */}
            <div className="ct-map-landmark" style={{ top: '24%', left: '22%' }}>Hazratganj</div>
            <div className="ct-map-landmark" style={{ top: '26%', left: '70%' }}>Aliganj</div>
            <div className="ct-map-landmark" style={{ top: '44%', left: '36%' }}>Gomti Nagar</div>
            <div className="ct-map-landmark" style={{ top: '70%', left: '20%' }}>Indira Nagar</div>
            <div className="ct-map-landmark" style={{ top: '64%', left: '76%' }}>Mahanagar</div>

            {mapMarkers.map((marker) => (
              <div
                key={marker.id}
                className="ct-marker-node"
                style={{ top: marker.top, left: marker.left }}
                onClick={() => setActiveIncident(marker)}
              >
                <div
                  className="ct-marker-dot"
                  style={{ backgroundColor: marker.color }}
                />

                {activeIncident?.id === marker.id && (
                  <div className="ct-marker-popover" onClick={(e) => e.stopPropagation()}>
                    <div className="ct-popover-top">
                      <span className="ct-popover-id">{marker.id}</span>
                      <PriorityBadge priority={marker.priority} />
                    </div>
                    <div className="ct-popover-title">{marker.title}</div>
                    <div className="ct-popover-meta">{marker.zone} · {marker.status}</div>
                    <div className="ct-popover-sla">{marker.sla}</div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Right: SLA Monitor */}
        <div className="ct-card ct-slamonitor-card">
          <div className="ct-card-head">
            <h2 className="ct-card-title">SLA Monitor</h2>
          </div>

          <div className="ct-sla-stats-list">
            <div className="ct-sla-stat-item">
              <div className="ct-sla-stat-label">Critical</div>
              <div className="ct-sla-stat-val ct-stat-red">{stats.critical}</div>
            </div>

            <div className="ct-sla-stat-item">
              <div className="ct-sla-stat-label">High</div>
              <div className="ct-sla-stat-val ct-stat-orange">{stats.high}</div>
            </div>

            <div className="ct-sla-stat-item">
              <div className="ct-sla-stat-label">Medium</div>
              <div className="ct-sla-stat-val ct-stat-green">{stats.medium}</div>
            </div>

            <div className="ct-sla-stat-item">
              <div className="ct-sla-stat-label">Overdue</div>
              <div className="ct-sla-stat-val ct-stat-red">{stats.overdue}</div>
            </div>
          </div>

          <div className="ct-sla-action-box">
            <button
              type="button"
              className="ct-btn-escalation"
              onClick={() => setShowEscalationModal(true)}
            >
              View escalation queue
            </button>
          </div>
        </div>
      </div>

      {/* Escalation Queue Modal */}
      <Modal
        isOpen={showEscalationModal}
        onClose={() => setShowEscalationModal(false)}
        title="SLA Escalation Queue"
      >
        <div className="ct-escalation-modal">
          <p className="ct-escalation-intro">
            The following incidents have breached or are critically approaching breach thresholds.
          </p>

          <div className="ct-escalation-list">
            {escalationQueue.map((inc) => (
              <div key={inc.id} className="ct-escalation-row">
                <div className="ct-esc-left">
                  <div className="ct-esc-id">{inc.id}</div>
                  <div className="ct-esc-title">{inc.title}</div>
                  <div className="ct-esc-meta">{inc.zone} · Assigned: {inc.assignedTeam || 'None'}</div>
                </div>
                <div className="ct-esc-right">
                  <PriorityBadge priority={inc.priority} />
                  <span className="ct-esc-sla">{inc.slaRemaining}</span>
                </div>
              </div>
            ))}
          </div>

          <div className="ct-modal-actions">
            <button
              type="button"
              className="btn btn-outline"
              onClick={() => setShowEscalationModal(false)}
            >
              Close
            </button>
            <button
              type="button"
              className="btn btn-primary"
              onClick={() => {
                alert("Emergency notification broadcasted to Zonal Commissioner & Field Supervisors.");
                setShowEscalationModal(false);
              }}
            >
              Broadcast Urgent Alert
            </button>
          </div>
        </div>
      </Modal>
    </div>
  );
};

export default LiveMapPage;
