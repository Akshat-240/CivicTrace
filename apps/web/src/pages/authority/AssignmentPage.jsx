import React, { useState } from 'react';
import PageHeader from '../../components/layout/PageHeader';
import PriorityBadge from '../../components/common/PriorityBadge';
import Modal from '../../components/common/Modal';
import { 
  mockIncidents, 
  mockTeamLoads, 
  mockAvailableOfficers 
} from '../../data/mockData';
import './AssignmentPage.css';

const AssignmentPage = () => {
  const [incidents, setIncidents] = useState([
    {
      id: "CT-INC-021",
      shortTitle: "Water leakage",
      priority: "CRITICAL",
      department: "Water Supply"
    },
    {
      id: "CT-INC-024",
      shortTitle: "Pothole",
      priority: "HIGH",
      department: "Road Infrastructure"
    },
    {
      id: "CT-INC-017",
      shortTitle: "Garbage accumulation",
      priority: "HIGH",
      department: "Sanitation"
    },
    {
      id: "CT-INC-016",
      shortTitle: "Broken drain cover",
      priority: "MEDIUM",
      department: "Road Infrastructure"
    }
  ]);

  const [assigningIncident, setAssigningIncident] = useState(null);
  const [selectedOfficer, setSelectedOfficer] = useState(mockAvailableOfficers[0].id);
  const [assignedSuccess, setAssignedSuccess] = useState(null);

  const handleConfirmAssignment = () => {
    if (!assigningIncident) return;
    const officer = mockAvailableOfficers.find(o => o.id === selectedOfficer);
    
    // Remove from unassigned queue
    setIncidents(prev => prev.filter(item => item.id !== assigningIncident.id));
    setAssignedSuccess(`Successfully assigned ${assigningIncident.id} (${assigningIncident.shortTitle}) to ${officer.name} (${officer.department})`);
    setAssigningIncident(null);

    setTimeout(() => {
      setAssignedSuccess(null);
    }, 4500);
  };

  return (
    <div className="ct-assignment-page">
      <PageHeader 
        title="Assignment"
        subtitle="Route work to officers and field teams with clear ownership."
      />

      {assignedSuccess && (
        <div className="ct-success-banner">
          {assignedSuccess}
        </div>
      )}

      <div className="ct-assignment-grid">
        {/* Left Card: Unassigned Queue */}
        <div className="ct-card ct-unassigned-card">
          <div className="ct-card-head">
            <h2 className="ct-card-title">Unassigned Queue</h2>
            <p className="ct-card-desc">{incidents.length} incidents waiting for assignment</p>
          </div>

          <div className="ct-unassigned-list">
            {incidents.map((inc) => (
              <div key={inc.id} className="ct-unassigned-row">
                <div className="ct-unassigned-id">{inc.id}</div>
                
                <div className="ct-unassigned-info">
                  <div className="ct-unassigned-title">{inc.shortTitle}</div>
                  <div className="ct-unassigned-priority">
                    <PriorityBadge priority={inc.priority} variant="text" />
                  </div>
                </div>

                <div className="ct-unassigned-action">
                  <button 
                    type="button" 
                    className="ct-btn-assign"
                    onClick={() => setAssigningIncident(inc)}
                  >
                    Assign Officer
                  </button>
                </div>
              </div>
            ))}

            {incidents.length === 0 && (
              <div className="ct-all-assigned">
                <p>All incidents have been successfully assigned to field teams!</p>
              </div>
            )}
          </div>
        </div>

        {/* Right Card: Team Load */}
        <div className="ct-card ct-teamload-card">
          <div className="ct-card-head">
            <h2 className="ct-card-title">Team Load</h2>
          </div>

          <div className="ct-team-list">
            {mockTeamLoads.map((team) => (
              <div key={team.name} className="ct-team-row">
                <div className="ct-team-name">{team.name}</div>
                <div className="ct-team-count" style={{ color: team.color }}>
                  {team.active} active
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Assignment Modal */}
      <Modal
        isOpen={!!assigningIncident}
        onClose={() => setAssigningIncident(null)}
        title={`Assign Officer: ${assigningIncident?.id}`}
      >
        {assigningIncident && (
          <div className="ct-assign-modal">
            <p className="ct-assign-modal-sub">
              Route <strong>{assigningIncident.shortTitle}</strong> ({assigningIncident.priority}) to an accountable municipal field officer.
            </p>

            <div className="ct-officer-options">
              {mockAvailableOfficers.map((officer) => (
                <label 
                  key={officer.id} 
                  className={`ct-officer-card ${selectedOfficer === officer.id ? 'selected' : ''}`}
                >
                  <input 
                    type="radio" 
                    name="officerChoice"
                    value={officer.id}
                    checked={selectedOfficer === officer.id}
                    onChange={(e) => setSelectedOfficer(e.target.value)}
                  />
                  <div className="ct-officer-info">
                    <div className="ct-officer-name">{officer.name}</div>
                    <div className="ct-officer-meta">
                      {officer.department} · {officer.currentAssignments} active tasks
                    </div>
                  </div>
                </label>
              ))}
            </div>

            <div className="ct-modal-actions">
              <button 
                type="button" 
                className="btn btn-outline"
                onClick={() => setAssigningIncident(null)}
              >
                Cancel
              </button>
              <button 
                type="button" 
                className="btn btn-primary"
                onClick={handleConfirmAssignment}
              >
                Confirm Assignment
              </button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
};

export default AssignmentPage;
