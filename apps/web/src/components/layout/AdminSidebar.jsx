import React from 'react';
import { NavLink, useNavigate, useLocation } from 'react-router-dom';
import { 
  LayoutDashboard, 
  AlertCircle, 
  Map, 
  BarChart3, 
  Clock, 
  Building2, 
  ShieldCheck, 
  Settings,
  LogOut
} from 'lucide-react';
import './AdminSidebar.css';

const AdminSidebar = () => {
  const navigate = useNavigate();
  const location = useLocation();

  const navItems = [
    { name: 'Dashboard', path: '/admin/dashboard', icon: <LayoutDashboard size={18} /> },
    { name: 'Incidents', path: '/admin/incidents', icon: <AlertCircle size={18} /> },
    { name: 'Map', path: '/admin/map', icon: <Map size={18} /> },
    { name: 'Analysis', path: '/admin/analysis', icon: <BarChart3 size={18} /> },
    { name: 'SLA Monitoring', path: '/admin/sla', icon: <Clock size={18} /> },
    { name: 'Department', path: '/admin/departments', icon: <Building2 size={18} /> },
    { name: 'Review & Governance', path: '/admin/governance', icon: <ShieldCheck size={18} /> },
  ];

  const handleSignOut = () => {
    localStorage.removeItem('ct_auth_token');
    localStorage.removeItem('ct_user_role');
    localStorage.removeItem('ct_user_id');
    navigate('/login');
  };

  return (
    <aside className="ct-admin-sidebar">
      <div className="ct-admin-brand" onClick={() => navigate('/admin/dashboard')}>
        <div className="ct-admin-brand-icon">
          <span className="ct-brand-blue-dot"></span>
        </div>
        <div className="ct-admin-brand-name">CivicTrace</div>
        <div className="ct-admin-role-badge">ADMIN</div>
      </div>

      <nav className="ct-admin-nav">
        {navItems.map((item) => (
          <NavLink 
            key={item.path}
            to={item.path}
            className={({ isActive }) => `ct-admin-nav-item ${isActive ? 'active' : ''}`}
          >
            <span className="ct-admin-nav-icon">{item.icon}</span>
            <span className="ct-admin-nav-label">{item.name}</span>
          </NavLink>
        ))}
      </nav>

      <div className="ct-admin-sidebar-footer">
        <div className="ct-admin-user-card">
          <div className="ct-admin-avatar">
            <span>AU</span>
          </div>
          <div className="ct-admin-user-info">
            <span className="ct-admin-user-name">Admin User</span>
            <span className="ct-admin-user-sub">CivicTrace Governance</span>
          </div>
        </div>
        <div className="ct-admin-footer-actions">
          <button 
            type="button" 
            className="ct-admin-footer-btn" 
            onClick={() => navigate('/admin/settings')}
          >
            <Settings size={16} />
            <span>Settings</span>
          </button>
          <button 
            type="button" 
            className="ct-admin-footer-btn" 
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

export default AdminSidebar;
