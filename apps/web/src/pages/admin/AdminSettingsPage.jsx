import React, { useState } from 'react';
import { 
  ShieldCheck, 
  Bell, 
  Sliders, 
  FileCheck2, 
  User, 
  Save, 
  CheckCircle 
} from 'lucide-react';
import { mockAdminSettings } from '../../data/mockData';
import './AdminSettingsPage.css';

export default function AdminSettingsPage() {
  const [settings, setSettings] = useState(mockAdminSettings);
  const [activeModal, setActiveModal] = useState(null);
  const [savedMessage, setSavedMessage] = useState(false);

  // Form states for modals
  const [profileName, setProfileName] = useState(settings.account.name);
  const [timeoutVal, setTimeoutVal] = useState(settings.account.sessionTimeout);
  const [locationVal, setLocationVal] = useState(settings.preferences.defaultLocation);
  const [refreshVal, setRefreshVal] = useState(settings.preferences.dataRefresh);
  const [retentionVal, setRetentionVal] = useState(settings.governance.auditRetention);

  const handleToggle = (category, field) => {
    setSettings(prev => ({
      ...prev,
      [category]: {
        ...prev[category],
        [field]: !prev[category][field]
      }
    }));
    triggerSaveFeedback();
  };

  const triggerSaveFeedback = () => {
    setSavedMessage(true);
    setTimeout(() => setSavedMessage(false), 3000);
  };

  const handleSaveModal = (e) => {
    e.preventDefault();
    if (activeModal === 'profile') {
      setSettings(prev => ({ ...prev, account: { ...prev.account, name: profileName } }));
    } else if (activeModal === 'timeout') {
      setSettings(prev => ({ ...prev, account: { ...prev.account, sessionTimeout: timeoutVal } }));
    } else if (activeModal === 'location') {
      setSettings(prev => ({ ...prev, preferences: { ...prev.preferences, defaultLocation: locationVal } }));
    } else if (activeModal === 'refresh') {
      setSettings(prev => ({ ...prev, preferences: { ...prev.preferences, dataRefresh: refreshVal } }));
    } else if (activeModal === 'retention') {
      setSettings(prev => ({ ...prev, governance: { ...prev.governance, auditRetention: retentionVal } }));
    }
    setActiveModal(null);
    triggerSaveFeedback();
  };

  return (
    <div className="admin-settings-container">
      {savedMessage && (
        <div className="settings-toast">
          <CheckCircle size={18} />
          <span>Settings saved successfully</span>
        </div>
      )}

      {/* SECTION 1: Account & Access */}
      <section className="settings-card">
        <div className="settings-card-header">
          <h2 className="settings-card-title">Account & Access</h2>
          <p className="settings-card-subtitle">Manage administrator profile, authentication and session security.</p>
        </div>

        <div className="settings-rows-list">
          <div className="settings-row">
            <div className="setting-info">
              <span className="setting-label">Profile information</span>
            </div>
            <div className="setting-value-col">
              <span className="setting-value">{settings.account.name}</span>
              <button 
                className="setting-action-btn"
                onClick={() => setActiveModal('profile')}
              >
                Edit
              </button>
            </div>
          </div>

          <div className="settings-row">
            <div className="setting-info">
              <span className="setting-label">Authentication</span>
            </div>
            <div className="setting-value-col">
              <span className="setting-value">{settings.account.authMethod}</span>
              <button 
                className="setting-action-btn secondary"
                onClick={() => alert("SSO is active and verified by state authority.")}
              >
                Configured
              </button>
            </div>
          </div>

          <div className="settings-row">
            <div className="setting-info">
              <span className="setting-label">Session timeout</span>
            </div>
            <div className="setting-value-col">
              <span className="setting-value">{settings.account.sessionTimeout}</span>
              <button 
                className="setting-action-btn"
                onClick={() => setActiveModal('timeout')}
              >
                Change
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* SECTION 2: Notifications */}
      <section className="settings-card">
        <div className="settings-card-header">
          <h2 className="settings-card-title">Notifications</h2>
          <p className="settings-card-subtitle">Control alerts for incidents, SLA breaches and governance events.</p>
        </div>

        <div className="settings-rows-list">
          <div className="settings-row">
            <div className="setting-info">
              <span className="setting-label">Critical incidents</span>
            </div>
            <div className="setting-value-col">
              <span className="setting-value">Immediate</span>
              <button 
                className={`toggle-switch-btn ${settings.notifications.criticalIncidents ? 'active' : ''}`}
                onClick={() => handleToggle('notifications', 'criticalIncidents')}
                aria-label="Toggle critical incident alerts"
              >
                <div className="toggle-switch-handle" />
              </button>
            </div>
          </div>

          <div className="settings-row">
            <div className="setting-info">
              <span className="setting-label">SLA breach alerts</span>
            </div>
            <div className="setting-value-col">
              <span className="setting-value">Immediate</span>
              <button 
                className={`toggle-switch-btn ${settings.notifications.slaBreachAlerts ? 'active' : ''}`}
                onClick={() => handleToggle('notifications', 'slaBreachAlerts')}
                aria-label="Toggle SLA breach alerts"
              >
                <div className="toggle-switch-handle" />
              </button>
            </div>
          </div>

          <div className="settings-row">
            <div className="setting-info">
              <span className="setting-label">Daily digest</span>
            </div>
            <div className="setting-value-col">
              <span className="setting-value">{settings.notifications.digestTime}</span>
              <button 
                className={`toggle-switch-btn ${settings.notifications.dailyDigest ? 'active' : ''}`}
                onClick={() => handleToggle('notifications', 'dailyDigest')}
                aria-label="Toggle daily digest"
              >
                <div className="toggle-switch-handle" />
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* SECTION 3: System Preferences */}
      <section className="settings-card">
        <div className="settings-card-header">
          <h2 className="settings-card-title">System Preferences</h2>
          <p className="settings-card-subtitle">Set default location, data refresh and dashboard behavior.</p>
        </div>

        <div className="settings-rows-list">
          <div className="settings-row">
            <div className="setting-info">
              <span className="setting-label">Default location</span>
            </div>
            <div className="setting-value-col">
              <span className="setting-value">{settings.preferences.defaultLocation}</span>
              <button 
                className="setting-action-btn"
                onClick={() => setActiveModal('location')}
              >
                Change
              </button>
            </div>
          </div>

          <div className="settings-row">
            <div className="setting-info">
              <span className="setting-label">Data refresh</span>
            </div>
            <div className="setting-value-col">
              <span className="setting-value">{settings.preferences.dataRefresh}</span>
              <button 
                className="setting-action-btn"
                onClick={() => setActiveModal('refresh')}
              >
                Change
              </button>
            </div>
          </div>

          <div className="settings-row">
            <div className="setting-info">
              <span className="setting-label">Timezone</span>
            </div>
            <div className="setting-value-col">
              <span className="setting-value">{settings.preferences.timezone}</span>
              <button 
                className="setting-action-btn secondary"
                onClick={() => alert("Timezone is locked to Asia/Kolkata (IST).")}
              >
                Change
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* SECTION 4: Governance & Audit */}
      <section className="settings-card">
        <div className="settings-card-header">
          <h2 className="settings-card-title">Governance & Audit</h2>
          <p className="settings-card-subtitle">Configure retention and administrative review policies.</p>
        </div>

        <div className="settings-rows-list">
          <div className="settings-row">
            <div className="setting-info">
              <span className="setting-label">Audit retention</span>
            </div>
            <div className="setting-value-col">
              <span className="setting-value">{settings.governance.auditRetention}</span>
              <button 
                className="setting-action-btn"
                onClick={() => setActiveModal('retention')}
              >
                Change
              </button>
            </div>
          </div>

          <div className="settings-row">
            <div className="setting-info">
              <span className="setting-label">Evidence verification</span>
            </div>
            <div className="setting-value-col">
              <span className="setting-value">Required</span>
              <button 
                className={`toggle-switch-btn ${settings.governance.evidenceVerificationRequired ? 'active' : ''}`}
                onClick={() => handleToggle('governance', 'evidenceVerificationRequired')}
                aria-label="Toggle evidence verification requirement"
              >
                <div className="toggle-switch-handle" />
              </button>
            </div>
          </div>

          <div className="settings-row">
            <div className="setting-info">
              <span className="setting-label">Admin action logging</span>
            </div>
            <div className="setting-value-col">
              <span className="setting-value">All actions</span>
              <button 
                className="setting-action-btn secondary"
                onClick={() => alert("Admin action logging is strictly enforced.")}
              >
                Change
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* Save action footer */}
      <div className="settings-footer-action">
        <button 
          className="settings-save-all-btn"
          onClick={triggerSaveFeedback}
        >
          <Save size={16} />
          <span>Save Preferences</span>
        </button>
      </div>

      {/* Modals */}
      {activeModal && (
        <div className="settings-modal-backdrop" onClick={() => setActiveModal(null)}>
          <div className="settings-modal" onClick={e => e.stopPropagation()}>
            {activeModal === 'profile' && (
              <form onSubmit={handleSaveModal}>
                <h3>Edit Profile Information</h3>
                <p>Update administrator display name.</p>
                <div className="modal-input-group">
                  <label>Administrator Name</label>
                  <input 
                    type="text" 
                    value={profileName} 
                    onChange={e => setProfileName(e.target.value)} 
                    required 
                  />
                </div>
                <div className="modal-actions">
                  <button type="button" className="btn-cancel" onClick={() => setActiveModal(null)}>Cancel</button>
                  <button type="submit" className="btn-confirm">Save</button>
                </div>
              </form>
            )}

            {activeModal === 'timeout' && (
              <form onSubmit={handleSaveModal}>
                <h3>Change Session Timeout</h3>
                <p>Select security auto-logout inactivity window.</p>
                <div className="modal-input-group">
                  <label>Timeout Duration</label>
                  <select value={timeoutVal} onChange={e => setTimeoutVal(e.target.value)}>
                    <option value="15 minutes">15 minutes</option>
                    <option value="30 minutes">30 minutes (Standard)</option>
                    <option value="60 minutes">60 minutes</option>
                    <option value="120 minutes">120 minutes</option>
                  </select>
                </div>
                <div className="modal-actions">
                  <button type="button" className="btn-cancel" onClick={() => setActiveModal(null)}>Cancel</button>
                  <button type="submit" className="btn-confirm">Save</button>
                </div>
              </form>
            )}

            {activeModal === 'location' && (
              <form onSubmit={handleSaveModal}>
                <h3>Change Default Location</h3>
                <p>Select the default view for the GIS Command Center.</p>
                <div className="modal-input-group">
                  <label>Default Ward / Zone</label>
                  <select value={locationVal} onChange={e => setLocationVal(e.target.value)}>
                    <option value="Lucknow · All Wards">Lucknow · All Wards</option>
                    <option value="Zone 1 · Hazratganj">Zone 1 · Hazratganj</option>
                    <option value="Zone 2 · Gomti Nagar">Zone 2 · Gomti Nagar</option>
                    <option value="Zone 3 · Alambagh">Zone 3 · Alambagh</option>
                    <option value="Zone 4 · Indira Nagar">Zone 4 · Indira Nagar</option>
                  </select>
                </div>
                <div className="modal-actions">
                  <button type="button" className="btn-cancel" onClick={() => setActiveModal(null)}>Cancel</button>
                  <button type="submit" className="btn-confirm">Save</button>
                </div>
              </form>
            )}

            {activeModal === 'refresh' && (
              <form onSubmit={handleSaveModal}>
                <h3>Data Refresh Frequency</h3>
                <p>Configure polling interval for live incident feeds.</p>
                <div className="modal-input-group">
                  <label>Refresh Rate</label>
                  <select value={refreshVal} onChange={e => setRefreshVal(e.target.value)}>
                    <option value="Every 1 minute">Every 1 minute</option>
                    <option value="Every 5 minutes">Every 5 minutes (Recommended)</option>
                    <option value="Every 15 minutes">Every 15 minutes</option>
                    <option value="Manual refresh only">Manual refresh only</option>
                  </select>
                </div>
                <div className="modal-actions">
                  <button type="button" className="btn-cancel" onClick={() => setActiveModal(null)}>Cancel</button>
                  <button type="submit" className="btn-confirm">Save</button>
                </div>
              </form>
            )}

            {activeModal === 'retention' && (
              <form onSubmit={handleSaveModal}>
                <h3>Audit Log Retention</h3>
                <p>Compliant retention schedule for government accountability.</p>
                <div className="modal-input-group">
                  <label>Retention Period</label>
                  <select value={retentionVal} onChange={e => setRetentionVal(e.target.value)}>
                    <option value="3 years">3 years</option>
                    <option value="5 years">5 years</option>
                    <option value="7 years">7 years (Statutory Default)</option>
                    <option value="10 years">10 years</option>
                  </select>
                </div>
                <div className="modal-actions">
                  <button type="button" className="btn-cancel" onClick={() => setActiveModal(null)}>Cancel</button>
                  <button type="submit" className="btn-confirm">Save</button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
