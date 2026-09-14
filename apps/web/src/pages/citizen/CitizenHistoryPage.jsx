import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowRight, FileText, AlertTriangle, Loader2 } from 'lucide-react';
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
        const citizenId = localStorage.getItem('ct_user_id');
        if (!citizenId) {
          navigate('/login');
          return;
        }
        // Load real backend incidents for authenticated citizen
        const response = await getIncidents(0, 100, citizenId);
        const items = response?.data || [];
        
        // Map backend data to frontend expectations
        const mapped = items.map(item => {
          const rawStatus = (item.status || '').toLowerCase();
          const rawAccountability = (item.accountability_state || '').toLowerCase();
          
          let uiStatus = 'Submitted';
          if (rawStatus === 'resolved' || rawStatus === 'closed') {
            uiStatus = 'Resolved';
          } else if (rawAccountability === 'escalation_eligible') {
            uiStatus = 'Escalated';
          } else if (rawStatus === 'active' || rawStatus === 'under_review') {
            uiStatus = 'In Progress';
          } else if (rawStatus === 'draft') {
            uiStatus = 'Submitted';
          } else {
            uiStatus = item.status || 'Submitted';
          }

          const locationString = 
            item.location?.address_raw || 
            [item.location?.street, item.location?.suburb, item.location?.city].filter(Boolean).join(', ') ||
            'Location unrecorded';

          return {
            id: item.reference_number || (item.id ? item.id.substring(0, 8).toUpperCase() : 'INC-UNKNOWN'),
            realId: item.id,
            title: item.title || (item.issue_type ? item.issue_type.replace(/_/g, ' ').toUpperCase() : 'Citizen Report'),
            location: locationString,
            status: uiStatus,
            date: item.created_at ? new Date(item.created_at).toLocaleDateString() : 'Recent',
          };
        });
        setIncidents(mapped);
      } catch (err) {
        console.error('Failed to load citizen incidents:', err);
        setError('Failed to load incidents. Please check your connection and try again.');
      } finally {
        setLoading(false);
      }
    }
    loadIncidents();
  }, [navigate]);

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
        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', padding: '3rem', color: '#64748B' }}>
          <Loader2 className="animate-spin" size={24} />
          <span style={{ marginLeft: '10px', fontSize: '0.95rem' }}>Loading your reports from server...</span>
        </div>
      )}

      {error && (
        <div style={{ padding: '2rem', color: '#ef4444', textAlign: 'center' }}>
          <AlertTriangle size={24} style={{ margin: '0 auto 8px' }} />
          <p>{error}</p>
        </div>
      )}

      {!loading && !error && filteredIncidents.length === 0 && (
        <div style={{ textAlign: 'center', padding: '3rem', color: '#64748B' }}>
          <FileText size={36} style={{ margin: '0 auto 12px', opacity: 0.4 }} />
          <p style={{ fontWeight: 500 }}>No reports found for "{activeFilter}".</p>
        </div>
      )}

      {/* Incidents Cards List */}
      {!loading && !error && filteredIncidents.length > 0 && (
        <div className="history-incidents-list">
          {filteredIncidents.map((incident) => {
            const badgeClass = 
              incident.status === 'Resolved' ? 'resolved' :
              incident.status === 'Escalated' ? 'escalated' :
              incident.status === 'In Progress' ? 'in-progress' :
              'submitted';

            return (
              <div key={incident.id} className="history-incident-card">
                <div className="history-incident-left">
                  <h3 className="history-incident-title">{incident.title}</h3>
                  <span className="history-incident-meta">
                    {incident.location} • {incident.status} • {incident.date}
                  </span>
                </div>

                <div className="history-incident-right">
                  <span className={`history-status-badge ${badgeClass}`}>
                    {incident.status}
                  </span>

                  <div 
                    className="history-action-col"
                    onClick={() => navigate(`/citizen/track?id=${encodeURIComponent(incident.realId)}`)}
                  >
                    <span className="history-report-id">{incident.id}</span>
                    <button type="button" className="history-view-link">
                      <span>View Report</span>
                      <ArrowRight size={14} />
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
