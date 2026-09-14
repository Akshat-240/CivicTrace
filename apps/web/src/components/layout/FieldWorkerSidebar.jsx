import React from 'react';
import { NavLink, useNavigate, useLocation } from 'react-router-dom';
import { 
  ClipboardList, 
  FileText, 
  MapPin, 
  Camera, 
  CheckCircle2,
  Layers,
  LogOut
} from 'lucide-react';
import './FieldWorkerSidebar.css';

const FieldWorkerSidebar = () => {
  const navigate = useNavigate();
  const location = useLocation();
  
  const searchParams = new URLSearchParams(location.search);
  let currentId = searchParams.get('id');
  if (!currentId) {
    const match = location.pathname.match(/\/tasks\/([^/]+)/);
    if (match) currentId = match[1];
  }

  const navItems = [
    { name: 'Assigned Work', path: '/field-worker/dashboard', icon: <ClipboardList size={18} />, requiresId: false },
    { name: 'Incident Details', path: currentId ? `/field-worker/tasks/${currentId}` : '#', icon: <FileText size={18} />, requiresId: true },
    { name: 'Location & Map', path: currentId ? `/field-worker/location?id=${currentId}` : '#', icon: <MapPin size={18} />, requiresId: true },
    { name: 'Evidence & Work Status', path: currentId ? `/field-worker/evidence?id=${currentId}` : '#', icon: <Camera size={18} />, requiresId: true },
    { name: 'Review & Submit', path: currentId ? `/field-worker/review?id=${currentId}` : '#', icon: <CheckCircle2 size={18} />, requiresId: true },
  ];

  const handleSignOut = () => {
    localStorage.clear();
    navigate('/login');
  };

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
          {navItems.map((item) => {
            if (item.requiresId && !currentId) {
              return (
                <li key={item.name} className="ct-fw-nav-item">
                  <div className="ct-fw-nav-link" style={{ opacity: 0.5, cursor: 'not-allowed' }}>
                    <span className="ct-fw-nav-icon">{item.icon}</span>
                    <span className="ct-fw-nav-text">{item.name}</span>
                  </div>
                </li>
              );
            }
            return (
              <li key={item.name} className="ct-fw-nav-item">
                <NavLink
                  to={item.path}
                  className={({ isActive }) => 
                    `ct-fw-nav-link ${isActive && item.path !== '#' ? 'active' : ''}`
                  }
                  end={item.name === 'Assigned Work'}
                >
                  <span className="ct-fw-nav-icon">{item.icon}</span>
                  <span className="ct-fw-nav-text">{item.name}</span>
                </NavLink>
              </li>
            );
          })}
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
        <button className="ct-fw-profile-action-btn" onClick={handleSignOut} style={{marginTop: '10px', width: '100%', display: 'flex', alignItems: 'center', gap: '8px', background: 'transparent', border: 'none', color: '#94a3b8', cursor: 'pointer', padding: '8px 12px', fontSize: '13px'}}>
          <LogOut size={14} /> Sign Out
        </button>
      </div>
    </aside>
  );
};

export default FieldWorkerSidebar;
