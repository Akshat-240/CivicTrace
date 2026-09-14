import React, { useState, useEffect } from 'react';
import PageHeader from '../../components/layout/PageHeader';
import { getCurrentUser } from '../../services/api';

const FieldWorkerSettingsPage = () => {
  const [profile, setProfile] = useState({
    name: "Loading...",
    email: "Loading...",
    role: "Field Worker"
  });

  useEffect(() => {
    async function loadData() {
      try {
        const user = await getCurrentUser();
        setProfile({
          name: user.full_name || "Unknown Worker",
          email: user.email || "Unknown Email",
          role: "Field Worker"
        });
      } catch (err) {
        console.error("Failed to load user data", err);
      }
    }
    loadData();
  }, []);

  return (
    <div style={{ padding: '2rem' }}>
      <PageHeader
        title="Settings"
        subtitle="Manage your field worker profile and preferences."
      />

      <div style={{ background: 'white', padding: '2rem', borderRadius: '8px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)' }}>
        <h2 style={{ fontSize: '18px', fontWeight: 'bold', marginBottom: '1rem', color: '#111827' }}>Profile Settings</h2>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div>
            <label style={{ display: 'block', fontSize: '14px', fontWeight: '500', color: '#374151', marginBottom: '4px' }}>Full Name</label>
            <input type="text" readOnly value={profile.name} style={{ width: '100%', maxWidth: '400px', padding: '8px', border: '1px solid #d1d5db', borderRadius: '4px', background: '#f9fafb' }} />
          </div>
          <div>
            <label style={{ display: 'block', fontSize: '14px', fontWeight: '500', color: '#374151', marginBottom: '4px' }}>Email Address</label>
            <input type="text" readOnly value={profile.email} style={{ width: '100%', maxWidth: '400px', padding: '8px', border: '1px solid #d1d5db', borderRadius: '4px', background: '#f9fafb' }} />
          </div>
          <div>
            <label style={{ display: 'block', fontSize: '14px', fontWeight: '500', color: '#374151', marginBottom: '4px' }}>Role</label>
            <input type="text" readOnly value={profile.role} style={{ width: '100%', maxWidth: '400px', padding: '8px', border: '1px solid #d1d5db', borderRadius: '4px', background: '#f9fafb' }} />
          </div>
        </div>
      </div>
    </div>
  );
};

export default FieldWorkerSettingsPage;
