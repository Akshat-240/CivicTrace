import React, { useState } from 'react';
import {
  Settings,
  User,
  Bell,
  Shield,
  Database,
  Save
} from 'lucide-react';
import './AdminSettingsPage.css';

const AdminSettingsPage = () => {
  const [activeTab, setActiveTab] = useState('profile');

  const [settings, setSettings] = useState({
    profile: { name: 'Admin User', email: 'admin@civictrace.com', role: 'System Administrator' },
    notifications: { emailAlerts: true, smsAlerts: false, criticalOnly: true }
  });

  return (
    <div className="ct-admin-settings">
      <div className="ct-admin-header">
        <h1>System Settings</h1>
      </div>
      <div className="ct-settings-content">
        <p>System settings are currently being migrated to live database connections.</p>
        <div style={{marginTop: '20px'}}>
            <div className="ct-admin-card">
              <h3>Profile</h3>
              <p>Name: {settings.profile.name}</p>
              <p>Email: {settings.profile.email}</p>
              <p>Role: {settings.profile.role}</p>
            </div>
            <div className="ct-admin-card" style={{marginTop: '10px'}}>
              <h3>Notifications</h3>
              <p>Email Alerts: {settings.notifications.emailAlerts ? 'On' : 'Off'}</p>
              <p>SMS Alerts: {settings.notifications.smsAlerts ? 'On' : 'Off'}</p>
            </div>
        </div>
      </div>
    </div>
  );
};

export default AdminSettingsPage;
