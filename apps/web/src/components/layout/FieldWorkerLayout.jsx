import React from 'react';
import { Outlet, NavLink, useNavigate, useLocation } from 'react-router-dom';
import FieldWorkerSidebar from './FieldWorkerSidebar';
import { 
  ClipboardList, 
  FileText, 
  MapPin, 
  Camera, 
  CheckCircle2,
  Layers
} from 'lucide-react';
import './FieldWorkerLayout.css';

const FieldWorkerLayout = () => {
  const navigate = useNavigate();
  const location = useLocation();

  const mobileNavItems = [
    { name: 'Jobs', path: '/field-worker/dashboard', icon: <ClipboardList size={20} /> },
    { name: 'Details', path: '/field-worker/tasks/CT-INC-024', icon: <FileText size={20} /> },
    { name: 'Map', path: '/field-worker/location', icon: <MapPin size={20} /> },
    { name: 'Evidence', path: '/field-worker/evidence', icon: <Camera size={20} /> },
    { name: 'Submit', path: '/field-worker/review', icon: <CheckCircle2 size={20} /> },
  ];

  return (
    <div className="ct-fw-layout">
      {/* Desktop & Tablet Sidebar */}
      <FieldWorkerSidebar />

      {/* Mobile Top Header */}
      <header className="ct-fw-mobile-header">
        <div className="ct-fw-mobile-brand" onClick={() => navigate('/field-worker/dashboard')}>
          <span className="ct-fw-mobile-dot"></span>
          <span className="ct-fw-mobile-title">CivicTrace</span>
          <span className="ct-fw-mobile-badge">FIELD</span>
        </div>

        {/* Mobile quick portal switcher */}
        <div className="ct-fw-mobile-portal-switch">
          <select 
            value="worker" 
            onChange={(e) => {
              const val = e.target.value;
              if (val === 'admin') navigate('/admin/dashboard');
              if (val === 'authority') navigate('/authority/dashboard');
              if (val === 'citizen') navigate('/citizen/dashboard');
            }}
            className="ct-fw-mobile-portal-select"
          >
            <option value="worker">Worker Portal</option>
            <option value="citizen">Citizen Portal</option>
            <option value="authority">Authority Portal</option>
            <option value="admin">Admin Portal</option>
          </select>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="ct-fw-main-content">
        <Outlet />
      </main>

      {/* Mobile Bottom Navigation */}
      <nav className="ct-fw-mobile-bottom-nav">
        {mobileNavItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) => 
              `ct-fw-mobile-nav-item ${isActive ? 'active' : ''}`
            }
          >
            <span className="ct-fw-mobile-nav-icon">{item.icon}</span>
            <span className="ct-fw-mobile-nav-label">{item.name}</span>
          </NavLink>
        ))}
      </nav>
    </div>
  );
};

export default FieldWorkerLayout;
