import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getIncidents } from '../../services/api';
import {
  ChevronRight,
  AlertTriangle,
  Clock,
  MapPin,
  Filter,
  ExternalLink,
  ChevronDown
} from 'lucide-react';
import './AdminDashboardPage.css';

const AdminDashboardPage = () => {
  const navigate = useNavigate();
  const [selectedCategory, setSelectedCategory] = useState('All Categories');
  const [selectedTimeframe, setSelectedTimeframe] = useState('Last 30 Days');

  const [incidents, setIncidents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activePin, setActivePin] = useState(null);

  useEffect(() => {
    const fetchIncidents = async () => {
      try {
        const data = await getIncidents();
        const mapped = data.map(inc => ({
          ...inc,
          x: Math.floor(Math.random() * 60) + 20,
          y: Math.floor(Math.random() * 60) + 20
        }));
        setIncidents(mapped);
        if (mapped.length > 0) {
          setActivePin(mapped[0]);
        }
      } catch (err) {
        console.error('Failed to load incidents', err);
      } finally {
        setLoading(false);
      }
    };
    fetchIncidents();
  }, []);

  // Pseudo-priorities since backend removed legacy priority field
  const getPseudoPriority = (type) => {
    const criticalTypes = ['sewage_overflow', 'water_leak', 'flooding'];
    const highTypes = ['pothole', 'broken_streetlight'];
    if (criticalTypes.includes(type)) return 'critical';
    if (highTypes.includes(type)) return 'high';
    return 'low';
  };

  const critical = incidents.filter(i => getPseudoPriority(i.issue_type) === 'critical').length;
  const high = incidents.filter(i => getPseudoPriority(i.issue_type) === 'high').length;
  const openCount = incidents.filter(i => (i.status || '').toLowerCase() !== 'resolved' && (i.status || '').toLowerCase() !== 'closed').length;

  // Calculate SLA Compliance
  const totalSLA = incidents.length;
  const breachedSLA = incidents.filter(i => i.accountability_state === 'overdue' || i.accountability_state === 'escalation_eligible').length;
  const slaCompliance = totalSLA > 0 ? Math.round(((totalSLA - breachedSLA) / totalSLA) * 100) + '%' : '100%';

  // Calculate Citizen Rating (mock dynamic)
  const resolved = incidents.filter(i => (i.status || '').toLowerCase() === 'resolved').length;
  const ratingBase = 4.0;
  const ratingBoost = totalSLA > 0 ? (resolved / totalSLA) * 1.0 : 0.8;
  const citizenRating = (ratingBase + ratingBoost).toFixed(1) + '/5';

  return (
    <div className="ct-admin-dashboard">
      {/* 5 KPI Stat Cards */}
      <div className="ct-admin-kpi-grid">
        <div className="ct-admin-kpi-card">
          <div className="ct-kpi-header">
            <span className="ct-kpi-indicator red"></span>
            <span className="ct-kpi-val">{loading ? '-' : critical}</span>
          </div>
          <span className="ct-kpi-label">Critical</span>
        </div>

        <div className="ct-admin-kpi-card">
          <div className="ct-kpi-header">
            <span className="ct-kpi-indicator amber"></span>
            <span className="ct-kpi-val">{loading ? '-' : high}</span>
          </div>
          <span className="ct-kpi-label">High</span>
        </div>

        <div className="ct-admin-kpi-card">
          <div className="ct-kpi-header">
            <span className="ct-kpi-indicator blue"></span>
            <span className="ct-kpi-val">{loading ? '-' : openCount}</span>
          </div>
          <span className="ct-kpi-label">Open</span>
        </div>

        <div className="ct-admin-kpi-card">
          <div className="ct-kpi-header">
            <span className="ct-kpi-indicator green"></span>
            <span className="ct-kpi-val">{loading ? '-' : slaCompliance}</span>
          </div>
          <span className="ct-kpi-label">SLA Compliance</span>
        </div>

        <div className="ct-admin-kpi-card">
          <div className="ct-kpi-header">
            <span className="ct-kpi-indicator gold"></span>
            <span className="ct-kpi-val">{loading ? '-' : citizenRating}</span>
          </div>
          <span className="ct-kpi-label">Citizen Rating</span>
        </div>
      </div>

      {/* Main Grid: Live Map + Priority & SLA Risk Queue */}
      <div className="ct-admin-command-grid">
        {/* Left: Citywide Live Map */}
        <div className="ct-admin-card ct-live-map-card">
          <div className="ct-card-header">
            <h2 className="ct-card-title">Live Incident Map · Citywide</h2>
            <div className="ct-map-filters">
              <div className="ct-select-wrapper">
                <select
                  value={selectedCategory}
                  onChange={(e) => setSelectedCategory(e.target.value)}
                  className="ct-filter-select"
                >
                  <option>All Categories</option>
                  <option>Road Damage</option>
                  <option>Sanitation</option>
                  <option>Streetlight</option>
                  <option>Water Supply</option>
                </select>
                <ChevronDown size={14} className="ct-select-chevron" />
              </div>

              <div className="ct-select-wrapper">
                <select
                  value={selectedTimeframe}
                  onChange={(e) => setSelectedTimeframe(e.target.value)}
                  className="ct-filter-select"
                >
                  <option>Last 30 Days</option>
                  <option>Last 7 Days</option>
                  <option>Today</option>
                </select>
                <ChevronDown size={14} className="ct-select-chevron" />
              </div>
            </div>
          </div>

          {/* Map canvas */}
          <div className="ct-map-canvas-container">
            <svg className="ct-gis-grid-lines" width="100%" height="100%">
              <defs>
                <pattern id="gisGrid" width="60" height="60" patternUnits="userSpaceOnUse">
                  <path d="M 60 0 L 0 0 0 60" fill="none" stroke="rgba(255, 255, 255, 0.04)" strokeWidth="1" />
                </pattern>
              </defs>
              <rect width="100%" height="100%" fill="#0A1128" />
              <rect width="100%" height="100%" fill="url(#gisGrid)" />

              {/* Connecting constellation lines */}
              <path d="M 320 220 L 480 340 L 720 290 L 590 180 Z" fill="none" stroke="rgba(59, 130, 246, 0.18)" strokeWidth="1.5" />
              <path d="M 180 380 L 320 220 L 220 160" fill="none" stroke="rgba(239, 68, 68, 0.15)" strokeWidth="1.5" />
              <circle cx="50%" cy="50%" r="220" fill="none" stroke="rgba(255, 255, 255, 0.05)" strokeDasharray="4 4" />
            </svg>

            {/* Pins on the map */}
            {!loading && incidents.map((pin) => {
              const isSelected = activePin?.id === pin.id;
              const prio = (pin.priority || '').toLowerCase();
              let pinClass = 'blue';
              if (prio === 'critical') pinClass = 'red';
              else if (prio === 'high') pinClass = 'amber';
              else if (prio === 'medium') pinClass = 'yellow';
              else if ((pin.status || '').toLowerCase() === 'resolved') pinClass = 'green';

              return (
                <div
                  key={pin.id}
                  className={`ct-map-pin-node ${pinClass} ${isSelected ? 'active-pulse' : ''}`}
                  style={{ top: `${pin.y}%`, left: `${pin.x}%` }}
                  onClick={() => setActivePin(pin)}
                  title={`${pin.id} - ${pin.description || ''}`}
                >
                  <span className="ct-pin-core"></span>
                  {isSelected && <span className="ct-pin-ring"></span>}
                </div>
              );
            })}

            {/* Selected Pin Tooltip Card */}
            {activePin && (
              <div
                className="ct-map-active-tooltip"
                style={{
                  top: `${Math.max(15, Math.min(65, activePin.y - 12))}%`,
                  left: `${Math.max(20, Math.min(68, activePin.x - 10))}%`
                }}
                onClick={() => navigate(`/admin/incidents/${activePin.id}`)}
              >
                <div className="ct-tooltip-title-row">
                  <span className="ct-tooltip-id">{activePin.id} · {activePin.status || 'Open'}</span>
                </div>
                <div className="ct-tooltip-issue">{activePin.description || 'No description'}</div>
                <div className="ct-tooltip-loc">
                  <MapPin size={12} />
                  <span>{activePin.location_name || 'Unknown Location'}</span>
                </div>
                <div className="ct-tooltip-risk-tag">
                  {activePin.category || 'General'}
                </div>
              </div>
            )}
          </div>

          {/* Map Legend */}
          <div className="ct-map-legend">
            <div className="ct-legend-item">
              <span className="ct-legend-dot red"></span>
              <span>Critical</span>
            </div>
            <div className="ct-legend-item">
              <span className="ct-legend-dot amber"></span>
              <span>High</span>
            </div>
            <div className="ct-legend-item">
              <span className="ct-legend-dot yellow"></span>
              <span>Medium</span>
            </div>
            <div className="ct-legend-item">
              <span className="ct-legend-dot blue"></span>
              <span>Low</span>
            </div>
            <div className="ct-legend-item">
              <span className="ct-legend-dot green"></span>
              <span>Resolved</span>
            </div>
          </div>
        </div>

        {/* Right: Priority & SLA Risk Queue */}
        <div className="ct-admin-card ct-queue-card">
          <div className="ct-card-header">
            <h2 className="ct-card-title">Priority & SLA Risk Queue</h2>
            <button
              type="button"
              className="ct-view-all-link"
              onClick={() => navigate('/admin/sla')}
            >
              View All
            </button>
          </div>

          <div className="ct-queue-list">
            {loading && <div style={{ padding: '1rem', color: '#888' }}>Loading queue...</div>}
            {!loading && incidents.slice(0, 4).map((inc) => {
              const prio = (inc.priority || '').toLowerCase();
              let dotClass = 'blue';
              if (prio === 'critical') dotClass = 'red';
              else if (prio === 'high') dotClass = 'amber';
              else if (prio === 'medium') dotClass = 'yellow';

              return (
                <div
                  key={inc.id}
                  className="ct-queue-item"
                  onClick={() => navigate(`/admin/incidents/${inc.id}`)}
                >
                  <div className={`ct-queue-dot-wrapper ${dotClass}`}>
                    <span className="ct-queue-dot"></span>
                  </div>

                  <div className="ct-queue-info">
                    <div className="ct-queue-id">{inc.id}</div>
                    <div className="ct-queue-title">
                      {inc.description} · <span className="ct-queue-priority">{inc.priority || 'Unassigned'}</span>
                    </div>
                    <div className="ct-queue-dept">
                      {inc.category || 'General'}
                    </div>
                    <div className="ct-queue-sla-tag">
                      <Clock size={12} />
                      <span>SLA Risk · 2 hrs</span>
                    </div>
                  </div>

                  <ChevronRight size={16} className="ct-queue-arrow" />
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdminDashboardPage;

