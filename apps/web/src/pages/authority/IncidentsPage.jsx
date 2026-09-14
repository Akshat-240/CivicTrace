import React, { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { Loader2 } from 'lucide-react';
import PageHeader from '../../components/layout/PageHeader';
import PriorityBadge from '../../components/common/PriorityBadge';
import StatusBadge from '../../components/common/StatusBadge';
import Modal from '../../components/common/Modal';
import { getIncidents } from '../../services/api';
import './IncidentsPage.css';

const IncidentsPage = () => {
  const navigate = useNavigate();
  const [searchTerm, setSearchTerm] = useState('');
  const [activeQuery, setActiveQuery] = useState('');
  const [selectedIncident, setSelectedIncident] = useState(null);
  
  const [incidents, setIncidents] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        const res = await getIncidents(0, 100);
        const MOCK_AUTHORITY_ID = "61c6d93e-889d-42fc-b6b9-b167ce631d47";
        const allIncidents = res?.data || [];
        const myIncidents = allIncidents.filter(inc => inc.authority?.id === MOCK_AUTHORITY_ID);
        
        const mapped = myIncidents.map(item => {
          return {
            realId: item.id,
            id: item.reference_number || (item.id ? item.id.substring(0, 8).toUpperCase() : 'UNKNOWN'),
            title: item.title || item.issue_type?.replace(/_/g, ' ')?.toUpperCase() || 'Incident',
            category: item.issue_type?.replace(/_/g, ' ')?.toUpperCase() || 'General',
            zone: item.jurisdiction?.name || 'Unknown Jurisdiction',
            location: item.location?.address_raw || item.location?.street || 'Unknown Location',
            subLocation: '',
            priority: item.priority_level?.toUpperCase() || 'Pending',
            status: item.status?.replace(/_/g, ' ')?.toUpperCase() || 'OPEN',
            slaRemaining: item.accountability_state ? item.accountability_state.toUpperCase() : 'Pending',
            description: 'Description not available in list view. Click for details.',
            assignedTeam: item.authority?.name || null,
            reportedAt: item.created_at ? new Date(item.created_at).toLocaleString() : 'Unknown',
          };
        });
        setIncidents(mapped);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  const incidentsToDisplay = useMemo(() => {
    return incidents.filter((inc) => {
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
  }, [activeQuery, incidents]);

  const handleSearch = (e) => {
    e.preventDefault();
    setActiveQuery(searchTerm);
  };

  const handleIncidentClick = async (incident) => {
    setSelectedIncident({ ...incident, description: 'Loading...', zone: 'Loading...' });
    try {
      const detail = await import('../../services/api').then(m => m.getIncident(incident.realId));
      setSelectedIncident({
        ...incident,
        zone: detail.jurisdiction?.name || 'Unknown Jurisdiction',
        description: detail.description || 'No description provided.',
        assignedTeam: detail.authority?.name || 'Unassigned',
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

  return (
    <div className="ct-incidents-page">
      <div style={{ padding: '0.5rem 1rem', background: '#e0f2fe', color: '#0284c7', fontSize: '0.875rem', fontWeight: 500, marginBottom: '1rem', borderRadius: '4px', border: '1px solid #bae6fd' }}>
        DEMO AUTHORITY CONTEXT — NOT AUTHENTICATION (Filtering by hardcoded Lucknow Municipal Corporation ID for Gate 4)
      </div>
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
        {loading ? (
          <div style={{ display: 'flex', justifyContent: 'center', padding: '3rem' }}>
            <Loader2 className="animate-spin" size={32} />
          </div>
        ) : incidentsToDisplay.map((incident) => (
          <div 
            key={incident.id} 
            className="ct-incident-item"
            onClick={() => handleIncidentClick(incident)}
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
