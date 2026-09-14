import React from 'react';
import { NavLink, useNavigate, useLocation } from 'react-router-dom';
import { 
  Home, 
  Grid, 
  ArrowLeftRight, 
  Target, 
  CheckCircle2, 
  Settings,
  LogOut
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

  const handleSignOut = (e) => {
    e.stopPropagation();
    localStorage.removeItem('ct_auth_token');
    localStorage.removeItem('ct_user_role');
    localStorage.removeItem('ct_user_id');
    navigate('/login');
  };

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
        <div className="ct-profile-card">
          <div className="ct-avatar">A</div>
          <div className="ct-user-meta">
            <span className="ct-user-name">LMC Authority</span>
            <span className="ct-user-dept">Civic Operations</span>
          </div>
        </div>
        <div className="ct-admin-footer-actions" style={{ display: 'flex', flexDirection: 'column', gap: '4px', marginTop: '8px', paddingTop: '8px', borderTop: '1px solid rgba(255, 255, 255, 0.06)' }}>
          <button 
            type="button" 
            className="ct-admin-footer-btn" 
            style={{ display: 'flex', alignItems: 'center', gap: '10px', background: 'transparent', border: 'none', color: '#94A3B8', padding: '8px 12px', borderRadius: '6px', fontSize: '13px', fontWeight: 500, cursor: 'pointer', textAlign: 'left', width: '100%' }}
            onClick={(e) => { e.stopPropagation(); navigate('/authority/settings'); }}
          >
            <Settings size={16} />
            <span>Settings</span>
          </button>
          <button 
            type="button" 
            className="ct-admin-footer-btn" 
            style={{ display: 'flex', alignItems: 'center', gap: '10px', background: 'transparent', border: 'none', color: '#94A3B8', padding: '8px 12px', borderRadius: '6px', fontSize: '13px', fontWeight: 500, cursor: 'pointer', textAlign: 'left', width: '100%' }}
            onClick={handleSignOut}
          >
            <LogOut size={16} />
            <span>Sign Out</span>
          </button>
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;
