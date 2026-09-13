import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { mockAdminMapPins, mockIncidentDetailCT1842 } from '../../data/mockData';
import { 
  Search, 
  ChevronDown, 
  Plus, 
  Minus, 
  Crosshair, 
  MapPin, 
  AlertTriangle, 
  Clock, 
  ExternalLink,
  ShieldAlert,
  ArrowRight
} from 'lucide-react';
import './AdminMapPage.css';

const AdminMapPage = () => {
  const navigate = useNavigate();
  const [selectedPin, setSelectedPin] = useState(mockAdminMapPins[0]);
  const [searchQuery, setSearchQuery] = useState('');
  const [zoomLevel, setZoomLevel] = useState(1);

  return (
    <div className="ct-admin-map-page">
      {/* Top Filter Bar */}
      <div className="ct-map-top-bar">
        <div className="ct-map-search">
          <Search size={16} className="ct-map-search-icon" />
          <input
            type="text"
            placeholder="Search incident, ID, location, department..."
            className="ct-map-search-input"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>

        <div className="ct-map-filter-pills">
          <select className="ct-map-filter-select">
            <option>All Categories</option>
            <option>Road Damage</option>
            <option>Sanitation</option>
            <option>Electrical</option>
            <option>Water Supply</option>
          </select>
          <select className="ct-map-filter-select">
            <option>All Priorities</option>
            <option>Critical</option>
            <option>High</option>
            <option>Medium</option>
            <option>Low</option>
          </select>
          <select className="ct-map-filter-select">
            <option>All Status</option>
            <option>Active</option>
            <option>In Progress</option>
            <option>Resolved</option>
          </select>
          <select className="ct-map-filter-select">
            <option>All SLA States</option>
            <option>On Track</option>
            <option>At Risk</option>
            <option>Breached</option>
          </select>
        </div>
      </div>

      {/* Main Map + Side Drawer */}
      <div className="ct-map-main-grid">
        {/* Map Canvas Card */}
        <div className="ct-map-display-card">
          <div className="ct-map-display-header">
            <div>
              <h2 className="ct-map-title">Live GIS Map · Citywide</h2>
              <p className="ct-map-sub">All incidents across Lucknow · 284 total</p>
            </div>

            {/* Map Controls */}
            <div className="ct-map-zoom-controls">
              <button 
                type="button" 
                className="ct-zoom-btn" 
                onClick={() => setZoomLevel(prev => Math.min(prev + 0.2, 1.6))}
                title="Zoom In"
              >
                <Plus size={15} />
              </button>
              <button 
                type="button" 
                className="ct-zoom-btn" 
                onClick={() => setZoomLevel(prev => Math.max(prev - 0.2, 0.8))}
                title="Zoom Out"
              >
                <Minus size={15} />
              </button>
              <button 
                type="button" 
                className="ct-zoom-btn" 
                onClick={() => setZoomLevel(1)}
                title="Reset View"
              >
                <Crosshair size={15} />
              </button>
            </div>
          </div>

          <div className="ct-gis-viewport">
            <div 
              className="ct-gis-scalable-canvas" 
              style={{ transform: `scale(${zoomLevel})` }}
            >
              <svg className="ct-gis-svg-overlay" width="100%" height="100%">
                <defs>
                  <pattern id="gisPattern" width="70" height="70" patternUnits="userSpaceOnUse">
                    <path d="M 70 0 L 0 0 0 70" fill="none" stroke="rgba(255, 255, 255, 0.05)" strokeWidth="1" />
                  </pattern>
                </defs>
                <rect width="100%" height="100%" fill="#080F24" />
                <rect width="100%" height="100%" fill="url(#gisPattern)" />

                {/* Concentric Ward Boundaries */}
                <circle cx="50%" cy="50%" r="300" fill="none" stroke="rgba(59, 130, 246, 0.12)" strokeWidth="1.5" strokeDasharray="6 4" />
                <circle cx="50%" cy="50%" r="200" fill="none" stroke="rgba(59, 130, 246, 0.18)" strokeWidth="1.5" />
                <circle cx="50%" cy="50%" r="100" fill="none" stroke="rgba(59, 130, 246, 0.25)" strokeWidth="1" />

                {/* Arterial Corridors */}
                <line x1="10%" y1="20%" x2="90%" y2="80%" stroke="rgba(255, 255, 255, 0.07)" strokeWidth="2" />
                <line x1="15%" y1="85%" x2="85%" y2="15%" stroke="rgba(255, 255, 255, 0.07)" strokeWidth="2" />

                <text x="50%" y="54%" textAnchor="middle" fill="rgba(255, 255, 255, 0.2)" fontSize="18" fontWeight="800" letterSpacing="0.1em">
                  LUCKNOW • ALL WARDS
                </text>
              </svg>

              {/* Mapped Pins */}
              {mockAdminMapPins.map((pin) => {
                const isSelected = selectedPin?.id === pin.id;
                let colorClass = 'blue';
                if (pin.priority === 'Critical') colorClass = 'red';
                else if (pin.priority === 'High') colorClass = 'amber';
                else if (pin.priority === 'Medium') colorClass = 'yellow';
                else if (pin.priority === 'Resolved') colorClass = 'green';

                return (
                  <div
                    key={pin.id}
                    className={`ct-map-node ${colorClass} ${isSelected ? 'active-selection' : ''}`}
                    style={{ top: `${pin.y}%`, left: `${pin.x}%` }}
                    onClick={() => setSelectedPin(pin)}
                  >
                    <span className="ct-node-dot"></span>
                    {isSelected && <span className="ct-node-pulse"></span>}
                  </div>
                );
              })}

              {/* Pin Callout Box */}
              {selectedPin && (
                <div 
                  className="ct-node-callout-box"
                  style={{ 
                    top: `${Math.max(10, Math.min(60, selectedPin.y - 12))}%`, 
                    left: `${Math.max(15, Math.min(65, selectedPin.x - 10))}%` 
                  }}
                  onClick={() => navigate('/admin/incidents/CT-1842')}
                >
                  <div className="ct-callout-id">{selectedPin.id} • {selectedPin.status}</div>
                  <div className="ct-callout-issue">{selectedPin.issue}</div>
                  <div className="ct-callout-location">{selectedPin.location}</div>
                  <div className="ct-callout-tag">{selectedPin.tag}</div>
                </div>
              )}
            </div>
          </div>

          {/* Map Legend */}
          <div className="ct-map-display-footer">
            <div className="ct-legend-group">
              <span className="ct-dot red"></span>
              <span>Critical</span>
            </div>
            <div className="ct-legend-group">
              <span className="ct-dot amber"></span>
              <span>High</span>
            </div>
            <div className="ct-legend-group">
              <span className="ct-dot yellow"></span>
              <span>Medium</span>
            </div>
            <div className="ct-legend-group">
              <span className="ct-dot blue"></span>
              <span>Low</span>
            </div>
            <div className="ct-legend-group">
              <span className="ct-dot green"></span>
              <span>Resolved</span>
            </div>
          </div>
        </div>

        {/* Right Drawer: Admin Incident Oversight */}
        <div className="ct-oversight-drawer">
          <div className="ct-oversight-header">
            <h3 className="ct-oversight-title">Admin Incident Oversight</h3>
            <p className="ct-oversight-subtitle">
              Fast triage, incident re-routing & governance view
            </p>
          </div>

          <div className="ct-oversight-body">
            <div className="ct-oversight-incident-box">
              <div className="ct-oversight-id-row">
                <span className="ct-oversight-id">{selectedPin?.id || '#CT-1842'}</span>
                <span className="ct-badge-pill badge-red font-bold">OPEN</span>
              </div>
              <h4 className="ct-oversight-issue">{selectedPin?.issue || 'Pothole'}</h4>
              <p className="ct-oversight-addr">{selectedPin?.location || 'Faizabad Road, Ward 12'}</p>
              <span className="ct-oversight-time">2 hours ago • Citizen report</span>
            </div>

            <div className="ct-oversight-priority-box">
              <span className="ct-box-label">PRIORITY</span>
              <span className="ct-priority-val">High • Safety Risk</span>
            </div>

            <div className="ct-oversight-jurisdiction-box">
              <span className="ct-box-label">Jurisdiction & Routing</span>
              <div className="ct-jurisdiction-val">Ward 12 • East Zone</div>
              <div className="ct-jurisdiction-sub">Roads Department • Responsible Authority</div>
            </div>

            <div className="ct-oversight-actions">
              <button 
                type="button" 
                className="ct-oversight-btn-primary"
                onClick={() => navigate('/admin/incidents/CT-1842')}
              >
                <span>Open Full Incident</span>
                <ArrowRight size={15} />
              </button>

              <div className="ct-oversight-secondary-actions">
                <button 
                  type="button" 
                  className="ct-oversight-btn-sec"
                  onClick={() => alert("Reviewing routing tables for Ward 12...")}
                >
                  View Routing
                </button>
                <button 
                  type="button" 
                  className="ct-oversight-btn-sec"
                  onClick={() => alert("Audit log: 4 events recorded for " + (selectedPin?.id || '#CT-1842'))}
                >
                  View Audit Log
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Bottom KPI Status Bar */}
      <div className="ct-map-kpi-bar">
        <div className="ct-kpi-bar-item status-live">
          <span className="ct-live-status-dot"></span>
          <span className="ct-kpi-bar-val">284 incidents mapped</span>
        </div>

        <div className="ct-kpi-bar-divider"></div>

        <div className="ct-kpi-bar-item">
          <span className="ct-kpi-bar-label">SLA Breached</span>
          <span className="ct-kpi-bar-val text-red">14</span>
        </div>

        <div className="ct-kpi-bar-divider"></div>

        <div className="ct-kpi-bar-item">
          <span className="ct-kpi-bar-label">Escalations</span>
          <span className="ct-kpi-bar-val">9</span>
        </div>

        <div className="ct-kpi-bar-divider"></div>

        <div className="ct-kpi-bar-item">
          <span className="ct-kpi-bar-label">Verification Pending</span>
          <span className="ct-kpi-bar-val">21</span>
        </div>

        <div className="ct-kpi-bar-divider"></div>

        <div className="ct-kpi-bar-item">
          <span className="ct-kpi-bar-label">Resolved</span>
          <span className="ct-kpi-bar-val text-green">321</span>
        </div>
      </div>
    </div>
  );
};

export default AdminMapPage;
