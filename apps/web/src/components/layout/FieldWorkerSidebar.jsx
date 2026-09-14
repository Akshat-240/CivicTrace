import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { 
  ClipboardList, 
  FileText, 
  MapPin, 
  Camera, 
  CheckCircle2,
  Layers
} from 'lucide-react';
import './FieldWorkerSidebar.css';

const FieldWorkerSidebar = () => {
  const navigate = useNavigate();

  const navItems = [
    { name: 'Assigned Work', path: '/field-worker/dashboard', icon: <ClipboardList size={18} /> },
    { name: 'Incident Details', path: '/field-worker/tasks/CT-INC-024', icon: <FileText size={18} /> },
    { name: 'Location & Map', path: '/field-worker/location', icon: <MapPin size={18} /> },
    { name: 'Evidence & Work Status', path: '/field-worker/evidence', icon: <Camera size={18} /> },
    { name: 'Review & Submit', path: '/field-worker/review', icon: <CheckCircle2 size={18} /> },
  ];

  return (
    <aside className="ct-fw-sidebar">
      {/* Brand Header */}
      <div className="ct-fw-brand" onClick={() => navigate('/field-worker/dashboard')}>
        <div className="ct-fw-brand-header">
          <span className="ct-fw-brand-dot"></span>
          <span className="ct-fw-brand-name">CivicTrace</span>
        </div>
        <div className="ct-fw-brand-subtitle">FIELD OPERATIONS</div>
      </div>

      {/* 4-Way Portal Switcher */}
      <div className="ct-fw-portal-switcher">
        <div className="ct-fw-portal-label">
          <Layers size={13} />
          <span>PORTAL</span>
        </div>
        <div className="ct-fw-portal-pills">
          <button 
            type="button" 
            className="ct-fw-portal-pill" 
            onClick={() => navigate('/admin/dashboard')}
            title="Admin Portal"
          >
            Admin
          </button>
          <button 
            type="button" 
            className="ct-fw-portal-pill" 
            onClick={() => navigate('/authority/dashboard')}
            title="Authority Portal"
          >
            Authority
          </button>
          <button 
            type="button" 
            className="ct-fw-portal-pill" 
            onClick={() => navigate('/citizen/dashboard')}
            title="Citizen Portal"
          >
            Citizen
          </button>
          <button 
            type="button" 
            className="ct-fw-portal-pill active" 
            onClick={() => navigate('/field-worker/dashboard')}
            title="Field Worker Portal"
          >
            Worker
          </button>
        </div>
      </div>

      {/* Navigation Links */}
      <nav className="ct-fw-nav">
        <ul className="ct-fw-nav-list">
          {navItems.map((item) => (
            <li key={item.path} className="ct-fw-nav-item">
              <NavLink
                to={item.path}
                className={({ isActive }) => 
                  `ct-fw-nav-link ${isActive ? 'active' : ''}`
                }
              >
                <span className="ct-fw-nav-icon">{item.icon}</span>
                <span className="ct-fw-nav-text">{item.name}</span>
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>

      {/* Worker Profile Footer */}
      <div className="ct-fw-footer">
        <div className="ct-fw-profile-label">FIELD WORKER</div>
        <div className="ct-fw-profile-card">
          <div className="ct-fw-avatar">R</div>
          <div className="ct-fw-user-info">
            <span className="ct-fw-user-name">Ravi Kumar</span>
            <span className="ct-fw-user-role">Zone 3 • Team B</span>
          </div>
        </div>
      </div>
    </aside>
  );
};

export default FieldWorkerSidebar;
