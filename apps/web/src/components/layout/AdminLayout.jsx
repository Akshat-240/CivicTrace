import React from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import AdminSidebar from './AdminSidebar';
import { Bell, MapPin } from 'lucide-react';
import './AdminLayout.css';

const AdminLayout = () => {
  const location = useLocation();

  const getPageHeaderInfo = () => {
    const path = location.pathname;
    if (path.includes('/admin/dashboard')) {
      return {
        title: 'Admin Command Center',
        subtitle: 'System-wide oversight of civic incidents, SLA performance and authority action.'
      };
    }
    if (path.includes('/admin/incidents/') && path !== '/admin/incidents') {
      return {
        title: 'Incident Detail',
        subtitle: 'In-depth triage, forensic AI analysis, evidence matching and authority dispatch.'
      };
    }
    if (path.includes('/admin/incidents')) {
      return {
        title: 'All Incidents',
        subtitle: 'Review, inspect, flag and audit every civic issue across the city.'
      };
    }
    if (path.includes('/admin/map')) {
      return {
        title: 'Citywide Incident Map',
        subtitle: 'Admin oversight of incidents, jurisdictions, SLA risk and authority workload.'
      };
    }
    if (path.includes('/admin/analysis')) {
      return {
        title: 'Analytics',
        subtitle: 'Citywide performance, trends, SLA health and resolution intelligence.'
      };
    }
    if (path.includes('/admin/sla')) {
      return {
        title: 'SLA Monitoring',
        subtitle: 'Track response targets, breaches and escalation risk across departments.'
      };
    }
    if (path.includes('/admin/departments')) {
      return {
        title: 'Departments',
        subtitle: 'Manage authority ownership, workload, SLA performance and nodal responsibility.'
      };
    }
    if (path.includes('/admin/governance')) {
      return {
        title: 'Review & Governance',
        subtitle: 'This is where responsible-system architecture becomes visible.'
      };
    }
    if (path.includes('/admin/settings')) {
      return {
        title: 'Settings',
        subtitle: 'Configure administrator access, notifications, system preferences and governance controls.'
      };
    }
    return {
      title: 'Admin Portal',
      subtitle: 'CivicTrace Administrative Command & Control'
    };
  };

  const headerInfo = getPageHeaderInfo();

  return (
    <div className="ct-admin-layout">
      <AdminSidebar />
      <div className="ct-admin-main-wrapper">
        <header className="ct-admin-header">
          <div className="ct-admin-header-left">
            <h1 className="ct-admin-title">{headerInfo.title}</h1>
            <p className="ct-admin-subtitle">{headerInfo.subtitle}</p>
          </div>

          <div className="ct-admin-header-right">
            <div className="ct-admin-loc-badge">
              <div className="ct-loc-indicator">
                <span className="ct-loc-dot"></span>
                <span className="ct-loc-text">Lucknow · All Wards</span>
              </div>
              <span className="ct-loc-time">12 Sept 2024, 10:24 AM</span>
            </div>

            <button className="ct-admin-notif-btn" title="Alerts & System Notifications">
              <Bell size={18} />
              <span className="ct-notif-badge"></span>
            </button>
          </div>
        </header>

        <main className="ct-admin-content">
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export default AdminLayout;
