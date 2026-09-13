import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowRight, FileText, CheckCircle2, AlertTriangle } from 'lucide-react';
import { mockCitizenPastIncidents } from '../../data/mockData';
import './CitizenHistoryPage.css';

export default function CitizenHistoryPage() {
  const navigate = useNavigate();
  const [activeFilter, setActiveFilter] = useState('All');

  const filteredIncidents = mockCitizenPastIncidents.filter((item) => {
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

      {/* Incidents Cards List */}
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
              <span className={`history-status-badge ${incident.status === 'Resolved' ? 'resolved' : 'escalated'}`}>
                {incident.status}
              </span>

              <div 
                className="history-action-col"
                onClick={() => navigate('/citizen/track')}
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
    </div>
  );
}
