import React from 'react';
import { NavLink, useNavigate, useLocation } from 'react-router-dom';
import { 
  Home, 
  Grid, 
  ArrowLeftRight, 
  Target, 
  CheckCircle2, 
  Settings 
} from 'lucide-react';
import './Sidebar.css';

const Sidebar = () => {
  const navigate = useNavigate();
  const location = useLocation();

  const navItems = [
    { name: 'Dashboard', path: '/authority/dashboard', icon: <Home size={18} strokeWidth={2} /> },
    { name: 'Incidents', path: '/authority/incidents', icon: <Grid size={18} strokeWidth={2} /> },
    { name: 'Assignment', path: '/authority/assignment', icon: <ArrowLeftRight size={18} strokeWidth={2} /> },
    { name: 'Live Map + SLA Monitor', path: '/authority/map', icon: <Target size={18} strokeWidth={2} /> },
    { name: 'Incident Verification', path: '/authority/verification', icon: <CheckCircle2 size={18} strokeWidth={2} /> },
  ];

  const isSettingsActive = location.pathname.includes('/authority/settings');

  return (
    <aside className="ct-sidebar">
      <div className="ct-sidebar-brand">
        <div className="ct-brand-title">CivicTrace</div>
        <div className="ct-brand-badge">AUTHORITY</div>
      </div>

      <nav className="ct-sidebar-nav">
        {navItems.map((item) => (
          <NavLink 
            key={item.path}
            to={item.path}
            className={({ isActive }) => `ct-nav-item ${isActive ? 'active' : ''}`}
          >
            <span className="ct-nav-icon">{item.icon}</span>
            <span className="ct-nav-label">{item.name}</span>
          </NavLink>
        ))}
      </nav>

      <div className="ct-sidebar-footer">
        <div 
          className={`ct-profile-card ${isSettingsActive ? 'settings-active' : ''}`}
          onClick={() => navigate('/authority/settings')}
          title="Open Authority Settings"
        >
          <div className="ct-avatar">A</div>
          <div className="ct-user-meta">
            <span className="ct-user-name">LMC Authority</span>
            <span className="ct-user-dept">Civic Operations</span>
          </div>
          <button 
            type="button" 
            className="ct-settings-btn"
            aria-label="Settings"
            onClick={(e) => {
              e.stopPropagation();
              navigate('/authority/settings');
            }}
          >
            <Settings size={17} />
          </button>
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;
