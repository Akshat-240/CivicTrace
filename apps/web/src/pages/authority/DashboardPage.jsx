import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Loader2 } from 'lucide-react';
import PageHeader from '../../components/layout/PageHeader';
import PriorityBadge from '../../components/common/PriorityBadge';
import Modal from '../../components/common/Modal';
import { getIncidents, getIncident, getCurrentUser } from '../../services/api';
import './DashboardPage.css';

const DashboardPage = () => {
  const navigate = useNavigate();
  const [selectedIncident, setSelectedIncident] = useState(null);

  const [incidents, setIncidents] = useState([]);
  const [loading, setLoading] = useState(true);

  const normalizeIncidentListItem = (item) => ({
    realId: item.id,
    id: item.reference_number || (item.id ? item.id.substring(0, 8).toUpperCase() : 'UNKNOWN'),
    title: item.title || (item.issue_type ? item.issue_type.replace(/_/g, ' ').toUpperCase() : 'Incident'),
    category: item.issue_type ? item.issue_type.replace(/_/g, ' ').toUpperCase() : 'General',
    zone: 'Not assigned',
    location: item.location?.address_raw || item.location?.street || 'Not available',
    subLocation: '',
    priority: item.priority_level ? item.priority_level.toUpperCase() : 'Pending',
    status: item.status ? item.status.replace(/_/g, ' ').toUpperCase() : 'OPEN',
    accountability_state: item.accountability_state || 'Not available',
    slaRemaining: item.accountability_state ? item.accountability_state.toUpperCase() : 'Not available',
    description: 'Description not available in list view.',
    assignedTeam: item.authority?.name || 'Not assigned',
    reportedAt: item.created_at ? new Date(item.created_at).toLocaleString() : 'Unknown',
  });

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        const user = await getCurrentUser();
        const authId = user?.authority_id;
        if (!authId) throw new Error("No authority ID found for user.");

        const res = await getIncidents(0, 100, null, authId);
        const myIncidents = res?.data || [];
        const mapped = myIncidents.map(normalizeIncidentListItem);
        setIncidents(mapped);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  const handleIncidentClick = async (incident) => {
    setSelectedIncident({ ...incident, description: 'Loading...', zone: 'Loading...' });
    try {
      const detail = await getIncident(incident.realId);
      setSelectedIncident({
        ...incident,
        zone: detail.jurisdiction?.name || 'Not assigned',
        description: detail.description || 'No description provided.',
        assignedTeam: detail.authority?.name || 'Not assigned',
      });
    } catch (e) {
      console.error("Failed to load incident detail", e);
      setSelectedIncident({
        ...incident,
        description: 'Failed to load details.',
        zone: 'Not available'
      });
    }
  };

  const priorityQueueIncidents = incidents.filter(inc => inc.priority === 'HIGH' || inc.priority === 'CRITICAL').slice(0, 5);

  const dynStats = {
    criticalHigh: incidents.filter(i => i.priority === 'HIGH' || i.priority === 'CRITICAL').length,
    openIncidents: incidents.filter(i => i.status !== 'RESOLVED' && i.status !== 'CLOSED').length,
    slaAtRisk: incidents.filter(i => i.accountability_state === 'due' || i.accountability_state === 'overdue' || i.accountability_state === 'escalation_eligible').length,
    verificationPending: incidents.filter(i => i.status === 'UNDER_REVIEW').length
  };

  const slaMetrics = {
    onTrack: incidents.filter(i => i.accountability_state === 'pending').length,
    dueSoon: incidents.filter(i => i.accountability_state === 'due').length,
    overdue: incidents.filter(i => i.accountability_state === 'overdue' || i.accountability_state === 'escalation_eligible').length,
    humanReview: incidents.filter(i => i.status === 'UNDER_REVIEW').length
  };

  return (
    <div className="ct-dashboard-page">
      <PageHeader
        title="Authority Dashboard"
        subtitle="Monitor incoming incidents, assignments, SLA risk and verification work."
      />

      {/* Top 4 Metrics Summary Card */}
      <div className="ct-metrics-card">
        <div className="ct-metric-col">
          <div className="ct-metric-value">{loading ? '-' : dynStats.criticalHigh}</div>
          <div className="ct-metric-label">Critical / High</div>
        </div>
        <div className="ct-metric-col">
          <div className="ct-metric-value">{loading ? '-' : dynStats.openIncidents}</div>
          <div className="ct-metric-label">Open Incidents</div>
        </div>
        <div className="ct-metric-col">
          <div className="ct-metric-value">{loading ? '-' : dynStats.slaAtRisk}</div>
          <div className="ct-metric-label">SLA At Risk</div>
        </div>
        <div className="ct-metric-col">
          <div className="ct-metric-value">{loading ? '-' : dynStats.verificationPending}</div>
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
            {loading ? (
              <div style={{ display: 'flex', justifyContent: 'center', padding: '2rem' }}>
                <Loader2 className="animate-spin" size={24} />
              </div>
            ) : priorityQueueIncidents.length > 0 ? priorityQueueIncidents.map((incident) => (
              <div
                key={incident.id}
                className="ct-priority-row"
                onClick={() => handleIncidentClick(incident)}
              >
                <div className="ct-row-id">{incident.id}</div>
                <div className="ct-row-title">{incident.title}</div>
                <div className="ct-row-right">
                  <PriorityBadge priority={incident.priority} />
                  <span className="ct-row-sla">{incident.slaRemaining}</span>
                </div>
              </div>
            )) : (
              <p style={{ padding: '1rem', color: '#6b7280', fontSize: '0.9rem', textAlign: 'center' }}>No high priority incidents.</p>
            )}
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
              <span className="ct-sla-num ct-text-green">{loading ? '-' : slaMetrics.onTrack}</span>
            </div>
            <div className="ct-sla-row">
              <span className="ct-sla-name">Due soon</span>
              <span className="ct-sla-num ct-text-orange">{loading ? '-' : slaMetrics.dueSoon}</span>
            </div>
            <div className="ct-sla-row">
              <span className="ct-sla-name">Overdue</span>
              <span className="ct-sla-num ct-text-red">{loading ? '-' : slaMetrics.overdue}</span>
            </div>
            <div className="ct-sla-row">
              <span className="ct-sla-name">Human review</span>
              <span className="ct-sla-num ct-text-blue">{loading ? '-' : slaMetrics.humanReview}</span>
            </div>
          </div>

          <div className="ct-recent-activity">
            <div className="ct-activity-title">Recent activity</div>
            <ul className="ct-activity-list">
              <li className="ct-activity-item" style={{ color: '#6b7280' }}>Timeline events not implemented globally</li>
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

