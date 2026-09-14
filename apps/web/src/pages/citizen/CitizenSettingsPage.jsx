import React, { useState } from 'react';
import { useNavigate, useOutletContext } from 'react-router-dom';
import {
  ChevronRight,
  CheckCircle
} from 'lucide-react';
import './CitizenSettingsPage.css';

export default function CitizenSettingsPage() {
  const navigate = useNavigate();
  const { profile } = useOutletContext();

  const [settings, setSettings] = useState({
    notifications: {
      reportUpdates: true,
      authorityResponses: true,
      resolutionAlerts: false
    }
  });

  const [savedFeedback, setSavedFeedback] = useState(false);

  const toggleNotification = (key) => {
    setSettings(prev => ({
      ...prev,
      notifications: {
        ...prev.notifications,
        [key]: !prev.notifications[key]
      }
    }));
    triggerFeedback();
  };

  const triggerFeedback = () => {
    setSavedFeedback(true);
    setTimeout(() => setSavedFeedback(false), 2500);
  };

  return (
    <div className="citizen-settings-container">
      {savedFeedback && (
        <div className="settings-saved-toast">
          <CheckCircle size={16} />
          <span>Settings updated</span>
        </div>
      )}

      {/* Profile Section */}
      <section className="settings-section-card profile-card">
        <div className="profile-info-left">
          <span className="profile-section-label">Profile</span>
          <h2 className="profile-user-name">{profile?.full_name || 'Citizen'}</h2>
          <span className="profile-user-area">{profile?.email}</span>
          <span className="profile-user-area">{profile?.city || 'Registered Citizen'}</span>
          <span className="profile-user-area" style={{textTransform: 'capitalize'}}>{profile?.role || 'Citizen'}</span>
        </div>
      </section>

      {/* 2-Column Settings Grid */}
      <div className="settings-two-col-grid">
        {/* Left Column: Notifications & Privacy */}
        <div className="settings-col">
          {/* Notifications Card */}
          <section className="settings-section-card">
            <h3 className="section-card-title">Notifications</h3>

            <div className="settings-toggle-list">
              <div className="setting-toggle-row">
                <div className="toggle-text-col">
                  <span className="toggle-label">Report updates</span>
                  <span className="toggle-desc">Receive status changes</span>
                </div>
                <button
                  type="button"
                  className={`switch-btn ${settings.notifications.reportUpdates ? 'active' : ''}`}
                  onClick={() => toggleNotification('reportUpdates')}
                  aria-label="Toggle report updates"
                >
                  <div className="switch-knob" />
                </button>
              </div>

              <div className="setting-toggle-row">
                <div className="toggle-text-col">
                  <span className="toggle-label">Authority responses</span>
                  <span className="toggle-desc">Get notified when action is taken</span>
                </div>
                <button
                  type="button"
                  className={`switch-btn ${settings.notifications.authorityResponses ? 'active' : ''}`}
                  onClick={() => toggleNotification('authorityResponses')}
                  aria-label="Toggle authority responses"
                >
                  <div className="switch-knob" />
                </button>
              </div>

              <div className="setting-toggle-row">
                <div className="toggle-text-col">
                  <span className="toggle-label">Resolution alerts</span>
                  <span className="toggle-desc">Know when verification is complete</span>
                </div>
                <button
                  type="button"
                  className={`switch-btn ${settings.notifications.resolutionAlerts ? 'active' : ''}`}
                  onClick={() => toggleNotification('resolutionAlerts')}
                  aria-label="Toggle resolution alerts"
                >
                  <div className="switch-knob" />
                </button>
              </div>
            </div>
          </section>

          {/* Privacy & Data Card */}
          <section className="settings-section-card">
            <h3 className="section-card-title">Privacy & Data</h3>

            <div className="settings-links-list">
              <div
                className="settings-link-row"
                onClick={() => alert("Your data is used only for civic issue verification and resolution tracking.")}
              >
                <div className="link-text-col">
                  <span className="link-label">Privacy information</span>
                  <span className="link-desc">How your data is used</span>
                </div>
                <ChevronRight size={18} className="link-arrow-icon" />
              </div>

              <div
                className="settings-link-row"
                onClick={() => alert("Evidence photo metadata is encrypted and anonymized per municipal guidelines.")}
              >
                <div className="link-text-col">
                  <span className="link-label">Evidence preferences</span>
                  <span className="link-desc">Control report evidence handling</span>
                </div>
                <ChevronRight size={18} className="link-arrow-icon" />
              </div>
            </div>
          </section>
        </div>

        {/* Right Column: Location & Security */}
        <div className="settings-col">
          {/* Location Card */}
          <section className="settings-section-card">
            <h3 className="section-card-title">Location</h3>

            <div className="settings-info-list">
              <div className="setting-info-row">
                <span className="info-row-label">Location permissions</span>
                <span className="permission-badge active">Active</span>
              </div>
            </div>
          </section>

          {/* Security Card */}
          <section className="settings-section-card">
            <h3 className="section-card-title">Security</h3>

            <div className="settings-security-list">
              <div className="security-action-row">
                <div className="security-text-col">
                  <span className="security-label">Change password</span>
                  <span className="security-desc">Update your account password</span>
                </div>
                <button
                  type="button"
                  className="btn-security-action blue"
                  onClick={() => alert("Password reset link sent to your registered mobile number.")}
                >
                  Change
                </button>
              </div>

              <div className="security-action-row">
                <div className="security-text-col">
                  <span className="security-label">Sign out</span>
                  <span className="security-desc">End your current CivicTrace session</span>
                </div>
                <button
                  type="button"
                  className="btn-security-action red"
                  onClick={() => {
                    localStorage.removeItem('ct_user_id');
                    localStorage.removeItem('ct_auth_token');
                    localStorage.removeItem('ct_user_role');
                    navigate('/login');
                  }}
                >
                  Sign out
                </button>
              </div>
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}
