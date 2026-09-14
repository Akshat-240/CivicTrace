import React from 'react';
import { NavLink, useNavigate, useLocation } from 'react-router-dom';
import { 
  Home, 
  PlusCircle, 
  Target, 
  Clock, 
  MessageSquareQuote, 
  Settings,
  Layers
} from 'lucide-react';
import './CitizenSidebar.css';

const CitizenSidebar = () => {
  const navigate = useNavigate();
  const location = useLocation();

  const navItems = [
    { name: 'Dashboard', path: '/citizen/dashboard', icon: <Home size={18} /> },
    { name: 'Report', path: '/citizen/report', icon: <PlusCircle size={18} /> },
    { name: 'Track', path: '/citizen/track', icon: <Target size={18} /> },
    { name: 'Past Incidents', path: '/citizen/history', icon: <Clock size={18} /> },
    { name: 'Feedback', path: '/citizen/feedback', icon: <MessageSquareQuote size={18} /> },
  ];

  const isSettingsActive = location.pathname.includes('/citizen/settings');

  return (
    <aside className="ct-citizen-sidebar">
      <div className="ct-citizen-brand" onClick={() => navigate('/citizen/dashboard')}>
        <div className="ct-citizen-brand-icon">
          <span className="ct-brand-blue-dot"></span>
        </div>
        <div className="ct-citizen-brand-name">CivicTrace</div>
        <div className="ct-citizen-role-badge">CITIZEN</div>
      </div>

      {/* Portal Switcher */}
      <div className="ct-portal-switcher">
        <div className="ct-portal-select-label">
          <Layers size={13} />
          <span>PORTAL</span>
        </div>
        <div className="ct-portal-pills">
          <button 
            type="button" 
            className="ct-portal-pill" 
            onClick={() => navigate('/admin/dashboard')}
          >
            Admin
          </button>
          <button 
            type="button" 
            className="ct-portal-pill" 
            onClick={() => navigate('/authority/dashboard')}
          >
            Authority
          </button>
          <button 
            type="button" 
            className="ct-portal-pill active" 
            onClick={() => navigate('/citizen/dashboard')}
          >
            Citizen
          </button>
          <button 
            type="button" 
            className="ct-portal-pill" 
            onClick={() => navigate('/field-worker/dashboard')}
          >
            Worker
          </button>
        </div>
      </div>

      {/* Main Navigation */}
      <nav className="ct-citizen-nav">
        <ul className="ct-citizen-nav-list">
          {navItems.map((item) => (
            <li key={item.path} className="ct-citizen-nav-item">
              <NavLink
                to={item.path}
                className={({ isActive }) => 
                  `ct-citizen-nav-link ${isActive ? 'active' : ''}`
                }
              >
                <span className="ct-citizen-nav-icon">{item.icon}</span>
                <span className="ct-citizen-nav-text">{item.name}</span>
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>

      {/* Footer Profile & Settings */}
      <div className="ct-citizen-footer">
        <div 
          className={`ct-citizen-profile ${isSettingsActive ? 'active' : ''}`}
          onClick={() => navigate('/citizen/settings')}
          title="Account Settings"
        >
          <div className="ct-citizen-avatar">C</div>
          <div className="ct-citizen-user-info">
            <span className="ct-citizen-user-name">Citizen</span>
            <span className="ct-citizen-user-role">Lucknow resident</span>
          </div>
          <button 
            type="button" 
            className="ct-citizen-settings-btn"
            onClick={(e) => {
              e.stopPropagation();
              navigate('/citizen/settings');
            }}
            aria-label="Settings"
          >
            <Settings size={17} />
          </button>
        </div>
      </div>
    </aside>
  );
};

export default CitizenSidebar;
