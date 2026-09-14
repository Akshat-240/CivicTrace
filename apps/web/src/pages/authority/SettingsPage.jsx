import React, { useState } from 'react';
import PageHeader from '../../components/layout/PageHeader';
import Modal from '../../components/common/Modal';
import './SettingsPage.css';

import { getCurrentUser, getAuthorities } from '../../services/api';

const SettingsPage = () => {
  const [profile, setProfile] = useState({
    name: "Loading...",
    department: "Loading...",
    role: "Loading...",
    auth: "Government SSO"
  });

  React.useEffect(() => {
    async function loadData() {
      try {
        const user = await getCurrentUser();
        let authName = "Not Assigned";
        let rolePart = "Authority User";
        let namePart = user.full_name || "Unknown Authority";

        if (user.full_name && user.full_name.includes(' - ')) {
          const parts = user.full_name.split(' - ');
          namePart = parts[0];
          rolePart = parts[1];
        }

        if (user.authority_id) {
          const auths = await getAuthorities();
          const match = auths.find(a => a.id === user.authority_id);
          if (match) authName = match.name;
        }

        setProfile({
          name: namePart,
          department: authName,
          role: rolePart,
          auth: "Government SSO"
        });

        if (user.city) {
          setPreferences(prev => ({ ...prev, location: user.city }));
        }
      } catch (err) {
        console.error("Failed to load user info", err);
      }
    }
    loadData();
  }, []);

  const [notifications, setNotifications] = useState({
    critical: true,
    assignments: true,
    dueSoon: true,
    verification: true
  });

  const [preferences, setPreferences] = useState({
    location: "Lucknow",
    view: "Priority",
    mapDisplay: "Incidents + SLA",
    timezone: "Asia/Kolkata"
  });

  const [slaSettings, setSlaSettings] = useState({
    slaRules: "Operational rules",
    threshold: "2 hours"
  });

  const [activeEditModal, setActiveEditModal] = useState(null);
  const [tempValue, setTempValue] = useState('');
  const [toastMessage, setToastMessage] = useState(null);

  const showToast = (msg) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 3000);
  };

  const handleOpenEdit = (field, currentVal) => {
    setActiveEditModal(field);
    setTempValue(currentVal);
  };

  const handleSaveModal = () => {
    if (activeEditModal === 'profileName') {
      setProfile(prev => ({ ...prev, name: tempValue }));
      showToast("Profile information updated successfully.");
    } else if (activeEditModal === 'department') {
      setProfile(prev => ({ ...prev, department: tempValue }));
      showToast("Department updated successfully.");
    } else if (activeEditModal === 'threshold') {
      setSlaSettings(prev => ({ ...prev, threshold: tempValue }));
      showToast("Due soon threshold updated.");
    } else if (activeEditModal === 'location') {
      setPreferences(prev => ({ ...prev, location: tempValue }));
      showToast("Default location updated.");
    }
    setActiveEditModal(null);
  };

  const toggleNotification = (key) => {
    setNotifications(prev => {
      const updated = { ...prev, [key]: !prev[key] };
      showToast(`${key} notifications ${updated[key] ? 'enabled' : 'disabled'}.`);
      return updated;
    });
  };

  return (
    <div className="ct-settings-page">
      <PageHeader
        title="Settings"
        subtitle="Configure your authority profile, notifications, operational preferences and security."
        rightSub="Last updated 12 Sep 2026"
      />

      {toastMessage && (
        <div className="ct-settings-toast">
          {toastMessage}
        </div>
      )}

      <div className="ct-settings-container">
        {/* Section 1: Authority Profile & Access */}
        <div className="ct-card ct-settings-card">
          <div className="ct-settings-section-head">
            <h2 className="ct-section-title">Authority Profile & Access</h2>
            <p className="ct-section-desc">Manage your authority identity, department access and account security.</p>
          </div>

          <div className="ct-settings-table">
            <div className="ct-settings-row">
              <div className="ct-row-col-label">Profile Information</div>
              <div className="ct-row-col-value">{profile.name}</div>
              <div className="ct-row-col-action">
                <button
                  type="button"
                  className="ct-link-btn"
                  onClick={() => handleOpenEdit('profileName', profile.name)}
                >
                  Edit
                </button>
              </div>
            </div>

            <div className="ct-settings-row">
              <div className="ct-row-col-label">Department</div>
              <div className="ct-row-col-value">{profile.department}</div>
              <div className="ct-row-col-action">
                <button
                  type="button"
                  className="ct-link-btn"
                  onClick={() => handleOpenEdit('department', profile.department)}
                >
                  View / Change
                </button>
              </div>
            </div>

            <div className="ct-settings-row">
              <div className="ct-row-col-label">Role</div>
              <div className="ct-row-col-value">{profile.role}</div>
              <div className="ct-row-col-action">
                <button type="button" className="ct-link-btn" onClick={() => showToast("Role: Civic Operations Officer (Full Administrative Access)")}>
                  View
                </button>
              </div>
            </div>

            <div className="ct-settings-row">
              <div className="ct-row-col-label">Authentication</div>
              <div className="ct-row-col-value">{profile.auth}</div>
              <div className="ct-row-col-action">
                <span className="ct-text-connected">Connected</span>
              </div>
            </div>
          </div>
        </div>

        {/* Section 2: Notifications */}
        <div className="ct-card ct-settings-card">
          <div className="ct-settings-section-head">
            <h2 className="ct-section-title">Notifications</h2>
            <p className="ct-section-desc">Control alerts for incidents, assignments, SLA events and verification tasks.</p>
          </div>

          <div className="ct-settings-table">
            <div className="ct-settings-row">
              <div className="ct-row-col-label">Critical Incidents</div>
              <div className="ct-row-col-value">Immediate</div>
              <div className="ct-row-col-action">
                <button
                  type="button"
                  className={`ct-badge-toggle ${notifications.critical ? 'enabled' : 'disabled'}`}
                  onClick={() => toggleNotification('critical')}
                >
                  {notifications.critical ? 'Enabled' : 'Disabled'}
                </button>
              </div>
            </div>

            <div className="ct-settings-row">
              <div className="ct-row-col-label">New Incident Assignments</div>
              <div className="ct-row-col-value">Immediate</div>
              <div className="ct-row-col-action">
                <button
                  type="button"
                  className={`ct-badge-toggle ${notifications.assignments ? 'enabled' : 'disabled'}`}
                  onClick={() => toggleNotification('assignments')}
                >
                  {notifications.assignments ? 'Enabled' : 'Disabled'}
                </button>
              </div>
            </div>

            <div className="ct-settings-row">
              <div className="ct-row-col-label">SLA Due Soon</div>
              <div className="ct-row-col-value">Immediate</div>
              <div className="ct-row-col-action">
                <button
                  type="button"
                  className={`ct-badge-toggle ${notifications.dueSoon ? 'enabled' : 'disabled'}`}
                  onClick={() => toggleNotification('dueSoon')}
                >
                  {notifications.dueSoon ? 'Enabled' : 'Disabled'}
                </button>
              </div>
            </div>

            <div className="ct-settings-row">
              <div className="ct-row-col-label">Verification Required</div>
              <div className="ct-row-col-value">Immediate</div>
              <div className="ct-row-col-action">
                <button
                  type="button"
                  className={`ct-badge-toggle ${notifications.verification ? 'enabled' : 'disabled'}`}
                  onClick={() => toggleNotification('verification')}
                >
                  {notifications.verification ? 'Enabled' : 'Disabled'}
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Section 3: Operational Preferences */}
        <div className="ct-card ct-settings-card">
          <div className="ct-settings-section-head">
            <h2 className="ct-section-title">Operational Preferences</h2>
            <p className="ct-section-desc">Configure the information and geographic scope shown in your workspace.</p>
          </div>

          <div className="ct-settings-table">
            <div className="ct-settings-row">
              <div className="ct-row-col-label">Default Location</div>
              <div className="ct-row-col-value">{preferences.location}</div>
              <div className="ct-row-col-action">
                <button
                  type="button"
                  className="ct-link-btn"
                  onClick={() => handleOpenEdit('location', preferences.location)}
                >
                  Change
                </button>
              </div>
            </div>

            <div className="ct-settings-row">
              <div className="ct-row-col-label">Default Incident View</div>
              <div className="ct-row-col-value">{preferences.view}</div>
              <div className="ct-row-col-action">
                <button
                  type="button"
                  className="ct-link-btn"
                  onClick={() => {
                    const next = preferences.view === 'Priority' ? 'Chronological' : 'Priority';
                    setPreferences(prev => ({ ...prev, view: next }));
                    showToast(`Default view set to ${next}`);
                  }}
                >
                  Change
                </button>
              </div>
            </div>

            <div className="ct-settings-row">
              <div className="ct-row-col-label">Map Display</div>
              <div className="ct-row-col-value">{preferences.mapDisplay}</div>
              <div className="ct-row-col-action">
                <button
                  type="button"
                  className="ct-link-btn"
                  onClick={() => {
                    const next = preferences.mapDisplay === 'Incidents + SLA' ? 'Heatmap Density' : 'Incidents + SLA';
                    setPreferences(prev => ({ ...prev, mapDisplay: next }));
                    showToast(`Map display set to ${next}`);
                  }}
                >
                  Change
                </button>
              </div>
            </div>

            <div className="ct-settings-row ct-timezone-row">
              <div className="ct-row-col-label">Timezone</div>
              <div className="ct-row-col-value">
                <input
                  type="text"
                  className="ct-inline-input"
                  value={preferences.timezone}
                  onChange={(e) => setPreferences(prev => ({ ...prev, timezone: e.target.value }))}
                />
              </div>
              <div className="ct-row-col-action ct-btn-pair">
                <button
                  type="button"
                  className="ct-btn-cancel"
                  onClick={() => setPreferences(prev => ({ ...prev, timezone: 'Asia/Kolkata' }))}
                >
                  Cancel
                </button>
                <button
                  type="button"
                  className="ct-btn-save-pill"
                  onClick={() => showToast(`Timezone saved as ${preferences.timezone}`)}
                >
                  Save
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Section 4: SLA & Workflow */}
        <div className="ct-card ct-settings-card">
          <div className="ct-settings-section-head">
            <h2 className="ct-section-title">SLA & Workflow</h2>
            <p className="ct-section-desc">Configure how operational alerts and workflow states are presented.</p>
          </div>

          <div className="ct-settings-table">
            <div className="ct-settings-row">
              <div className="ct-row-col-label">CivicTrace Pilot SLA</div>
              <div className="ct-row-col-value">{slaSettings.slaRules}</div>
              <div className="ct-row-col-action">
                <span className="ct-badge-enabled-text">Enabled</span>
              </div>
            </div>

            <div className="ct-settings-row">
              <div className="ct-row-col-label">Due Soon Threshold</div>
              <div className="ct-row-col-value">{slaSettings.threshold}</div>
              <div className="ct-row-col-action">
                <button
                  type="button"
                  className="ct-link-btn"
                  onClick={() => handleOpenEdit('threshold', slaSettings.threshold)}
                >
                  Change
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Edit Field Modal */}
      <Modal
        isOpen={!!activeEditModal}
        onClose={() => setActiveEditModal(null)}
        title="Update Setting"
      >
        <div className="ct-edit-modal-content">
          <label className="ct-modal-input-label">New Value:</label>
          <input
            type="text"
            className="ct-search-input"
            value={tempValue}
            onChange={(e) => setTempValue(e.target.value)}
          />

          <div className="ct-modal-actions">
            <button
              type="button"
              className="btn btn-outline"
              onClick={() => setActiveEditModal(null)}
            >
              Cancel
            </button>
            <button
              type="button"
              className="btn btn-primary"
              onClick={handleSaveModal}
            >
              Save Change
            </button>
          </div>
        </div>
      </Modal>
    </div>
  );
};

export default SettingsPage;
