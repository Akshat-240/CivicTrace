import React, { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import PageHeader from '../../components/layout/PageHeader';
import PriorityBadge from '../../components/common/PriorityBadge';
import StatusBadge from '../../components/common/StatusBadge';
import Modal from '../../components/common/Modal';
import { mockIncidents } from '../../data/mockData';
import './IncidentsPage.css';

const IncidentsPage = () => {
  const navigate = useNavigate();
  const [searchTerm, setSearchTerm] = useState('');
  const [activeQuery, setActiveQuery] = useState('');
  const [selectedIncident, setSelectedIncident] = useState(null);

  const incidentsToDisplay = useMemo(() => {
    return mockIncidents.filter((inc) => {
      const q = activeQuery.toLowerCase();
      if (!q) return true;
      return (
        inc.id.toLowerCase().includes(q) ||
        inc.title.toLowerCase().includes(q) ||
        inc.category.toLowerCase().includes(q) ||
        inc.zone.toLowerCase().includes(q) ||
        inc.location.toLowerCase().includes(q)
      );
    });
  }, [activeQuery]);

  const handleSearch = (e) => {
    e.preventDefault();
    setActiveQuery(searchTerm);
  };

  return (
    <div className="ct-incidents-page">
      <PageHeader 
        title="Incidents"
        subtitle="Review and manage incidents routed to your authority."
      />

      {/* Top Search Bar */}
      <div className="ct-search-card">
        <span className="ct-search-label">Search incidents</span>
        <form className="ct-search-form" onSubmit={handleSearch}>
          <input 
            type="text"
            className="ct-search-input"
            placeholder="Search by ID, issue or location"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
          <button type="submit" className="ct-btn-search">
            Search
          </button>
        </form>
      </div>

      {/* Incidents List Rows */}
      <div className="ct-incidents-container">
        {incidentsToDisplay.map((incident) => (
          <div 
            key={incident.id} 
            className="ct-incident-item"
            onClick={() => setSelectedIncident(incident)}
          >
            <div className="ct-incident-id">{incident.id}</div>
            
            <div className="ct-incident-info">
              <div className="ct-incident-title">{incident.title}</div>
              <div className="ct-incident-sub">
                {incident.category} · {incident.zone}
              </div>
            </div>

            <div className="ct-incident-badge">
              <PriorityBadge priority={incident.priority} />
            </div>

            <div className="ct-incident-status">
              <StatusBadge status={incident.status} />
            </div>
          </div>
        ))}

        {incidentsToDisplay.length === 0 && (
          <div className="ct-empty-search">
            <p>No incidents match "{activeQuery}".</p>
            <button 
              className="btn btn-outline" 
              onClick={() => {
                setSearchTerm('');
                setActiveQuery('');
              }}
            >
              Reset Search
            </button>
          </div>
        )}
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
                <span className="ct-field-value">{selectedIncident.assignedTeam || 'None (Unassigned)'}</span>
              </div>
              <div className="ct-modal-field">
                <span className="ct-field-label">Reported Timestamp</span>
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
              {selectedIncident.status === 'Awaiting Verification' && (
                <button 
                  type="button" 
                  className="btn btn-primary"
                  onClick={() => {
                    setSelectedIncident(null);
                    navigate('/authority/verification');
                  }}
                >
                  Verify Resolution Evidence
                </button>
              )}
              {!selectedIncident.assignedTeam && (
                <button 
                  type="button" 
                  className="btn btn-primary"
                  onClick={() => {
                    setSelectedIncident(null);
                    navigate('/authority/assignment');
                  }}
                >
                  Assign Field Team
                </button>
              )}
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
};

export default IncidentsPage;
