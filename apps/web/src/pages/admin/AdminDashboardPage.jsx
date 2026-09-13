import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  mockAdminStats, 
  mockAdminIncidents, 
  mockAdminMapPins 
} from '../../data/mockData';
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
  const [activePin, setActivePin] = useState(mockAdminMapPins[0]);

  return (
    <div className="ct-admin-dashboard">
      {/* 5 KPI Stat Cards */}
      <div className="ct-admin-kpi-grid">
        <div className="ct-admin-kpi-card">
          <div className="ct-kpi-header">
            <span className="ct-kpi-indicator red"></span>
            <span className="ct-kpi-val">{mockAdminStats.critical}</span>
          </div>
          <span className="ct-kpi-label">Critical</span>
        </div>

        <div className="ct-admin-kpi-card">
          <div className="ct-kpi-header">
            <span className="ct-kpi-indicator amber"></span>
            <span className="ct-kpi-val">{mockAdminStats.high}</span>
          </div>
          <span className="ct-kpi-label">High</span>
        </div>

        <div className="ct-admin-kpi-card">
          <div className="ct-kpi-header">
            <span className="ct-kpi-indicator blue"></span>
            <span className="ct-kpi-val">{mockAdminStats.open}</span>
          </div>
          <span className="ct-kpi-label">Open</span>
        </div>

        <div className="ct-admin-kpi-card">
          <div className="ct-kpi-header">
            <span className="ct-kpi-indicator green"></span>
            <span className="ct-kpi-val">{mockAdminStats.slaCompliance}</span>
          </div>
          <span className="ct-kpi-label">SLA Compliance</span>
        </div>

        <div className="ct-admin-kpi-card">
          <div className="ct-kpi-header">
            <span className="ct-kpi-indicator gold"></span>
            <span className="ct-kpi-val">{mockAdminStats.citizenRating}</span>
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
            {mockAdminMapPins.map((pin) => {
              const isSelected = activePin?.id === pin.id;
              let pinClass = 'blue';
              if (pin.priority === 'Critical') pinClass = 'red';
              else if (pin.priority === 'High') pinClass = 'amber';
              else if (pin.priority === 'Medium') pinClass = 'yellow';
              else if (pin.priority === 'Resolved') pinClass = 'green';

              return (
                <div
                  key={pin.id}
                  className={`ct-map-pin-node ${pinClass} ${isSelected ? 'active-pulse' : ''}`}
                  style={{ top: `${pin.y}%`, left: `${pin.x}%` }}
                  onClick={() => setActivePin(pin)}
                  title={`${pin.id} - ${pin.issue}`}
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
                onClick={() => navigate(`/admin/incidents/CT-1842`)}
              >
                <div className="ct-tooltip-title-row">
                  <span className="ct-tooltip-id">{activePin.id} · {activePin.status}</span>
                </div>
                <div className="ct-tooltip-issue">{activePin.issue}</div>
                <div className="ct-tooltip-loc">
                  <MapPin size={12} />
                  <span>{activePin.location}</span>
                </div>
                <div className="ct-tooltip-risk-tag">
                  {activePin.tag}
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
            {mockAdminIncidents.slice(0, 4).map((inc) => {
              let dotClass = 'amber';
              if (inc.priority === 'Critical') dotClass = 'red';
              else if (inc.priority === 'Medium') dotClass = 'yellow';

              return (
                <div 
                  key={inc.id} 
                  className="ct-queue-item"
                  onClick={() => navigate(`/admin/incidents/${inc.rawId}`)}
                >
                  <div className={`ct-queue-dot-wrapper ${dotClass}`}>
                    <span className="ct-queue-dot"></span>
                  </div>

                  <div className="ct-queue-info">
                    <div className="ct-queue-id">{inc.id}</div>
                    <div className="ct-queue-title">
                      {inc.issue} · <span className="ct-queue-priority">{inc.priority}</span>
                    </div>
                    <div className="ct-queue-dept">
                      {inc.ward} · {inc.department}
                    </div>
                    <div className={`ct-queue-sla-tag ${inc.slaBreached ? 'breached' : ''}`}>
                      <Clock size={12} />
                      <span>{inc.slaBreached ? 'Critical · SLA breached' : `SLA Risk · ${inc.sla}`}</span>
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
