import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowRight, FileText, CheckCircle2, AlertTriangle, Loader2 } from 'lucide-react';
import { getIncidents } from '../../services/api';
import './CitizenHistoryPage.css';

export default function CitizenHistoryPage() {
  const navigate = useNavigate();
  const [activeFilter, setActiveFilter] = useState('All');
  const [incidents, setIncidents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function loadIncidents() {
      try {
        setLoading(true);
        const data = await getIncidents(0, 100);
        // map backend data to frontend expectations
        const mapped = data.data.map(item => {
          let uiStatus = 'Pending';
          if (item.status === 'resolved' || item.status === 'closed') {
            uiStatus = 'Resolved';
          } else if (item.status === 'active' || item.status === 'under_review') {
            uiStatus = 'In Progress';
          } else {
            uiStatus = item.status;
          }
          
          if (item.accountability_state === 'escalation_eligible') {
            uiStatus = 'Escalated';
          }

          return {
            id: item.reference_number || item.id.substring(0, 8).toUpperCase(),
            realId: item.id,
            title: item.title || item.issue_type?.replace('_', ' ')?.toUpperCase() || 'Unknown Issue',
            location: item.location?.address || 'Location Unknown',
            status: uiStatus,
            date: new Date(item.created_at).toLocaleDateString(),
          };
        });
        setIncidents(mapped);
      } catch (err) {
        console.error(err);
        setError('Failed to load incidents. Please try again later.');
      } finally {
        setLoading(false);
      }
    }
    loadIncidents();
  }, []);

  const filteredIncidents = incidents.filter((item) => {
    if (activeFilter === 'All') return true;
    if (activeFilter === 'Resolved') return item.status === 'Resolved';
    if (activeFilter === 'Unresolved') return item.status !== 'Resolved';
    if (activeFilter === 'Escalated') return item.status === 'Escalated';
    return true;
  });

  return (
    <div className="citizen-history-container">
      {/* Filter Tabs */}
      <div className="history-filter-tabs">
        {['All', 'Resolved', 'Unresolved', 'Escalated'].map((tab) => (
          <button 
            key={tab}
            type="button"
            className={`history-filter-tab ${activeFilter === tab ? 'active' : ''}`}
            onClick={() => setActiveFilter(tab)}
          >
            {tab}
          </button>
        ))}
      </div>

      {loading && (
        <div style={{ display: 'flex', justifyContent: 'center', padding: '2rem' }}>
          <Loader2 className="animate-spin" size={24} />
          <span style={{ marginLeft: '8px' }}>Loading your reports...</span>
        </div>
      )}

      {error && (
        <div style={{ padding: '2rem', color: '#ef4444', textAlign: 'center' }}>
          <AlertTriangle size={24} style={{ margin: '0 auto 8px' }} />
          <p>{error}</p>
        </div>
      )}

      {!loading && !error && filteredIncidents.length === 0 && (
        <div style={{ textAlign: 'center', padding: '3rem', color: '#6b7280' }}>
          <FileText size={32} style={{ margin: '0 auto 12px', opacity: 0.5 }} />
          <p>No reports found matching this filter.</p>
        </div>
      )}

      {/* Incidents Cards List */}
      {!loading && !error && (
        <div className="history-incidents-list">
          {filteredIncidents.map((incident) => (
            <div key={incident.id} className="history-incident-card">
              <div className="history-incident-left">
                <h3 className="history-incident-title">{incident.title}</h3>
                <span className="history-incident-meta">
                  {incident.location} · {incident.status} · {incident.date}
                </span>
              </div>

              <div className="history-incident-right">
                <span className={`history-status-badge ${incident.status === 'Resolved' ? 'resolved' : incident.status === 'Escalated' ? 'escalated' : 'in-progress'}`}>
                  {incident.status}
                </span>

                <div 
                  className="history-action-col"
                  onClick={() => navigate(`/citizen/track?id=${incident.realId}`)}
                >
                  <span className="history-report-id">{incident.id}</span>
                  <button type="button" className="history-view-link">
                    <span>View Report</span>
                    <ArrowRight size={14} />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
