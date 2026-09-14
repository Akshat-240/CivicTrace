import React from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { mockFieldWorkerData } from '../../data/mockData';
import { Image as ImageIcon, ArrowRight } from 'lucide-react';
import './FieldWorkerIncidentPage.css';

const FieldWorkerIncidentPage = () => {
  const navigate = useNavigate();
  const { id } = useParams();
  
  // Find task or default to CT-INC-024
  const task = mockFieldWorkerData.tasks.find(t => t.id === id) || mockFieldWorkerData.tasks[0];

  const handleContinueToMap = () => {
    navigate(`/field-worker/location?id=${task.id}`);
  };

  return (
    <div className="ct-fw-page-container">
      {/* Header */}
      <div className="ct-fw-page-header">
        <h1 className="ct-fw-page-title">Incident Details</h1>
        <p className="ct-fw-page-subtitle">{task.title}</p>
      </div>

      {/* Top Two Column Cards */}
      <div className="ct-fw-incident-grid-top">
        {/* Incident Summary Card */}
        <div className="ct-fw-card ct-fw-incident-summary-card">
          <span className="ct-fw-card-header-label">Incident summary</span>
          <h2 className="ct-fw-incident-main-heading">{task.incidentName}</h2>
          <div className="ct-fw-incident-category-sub">{task.detailedCategory}</div>

          <div className="ct-fw-incident-meta-list">
            <div className="ct-fw-meta-row">
              <span className="ct-fw-meta-key">Reported by</span>
              <span className="ct-fw-meta-val">{task.reportedBy}</span>
            </div>
            <div className="ct-fw-meta-row">
              <span className="ct-fw-meta-key">Assigned authority</span>
              <span className="ct-fw-meta-val">{task.assignedAuthority}</span>
            </div>
            <div className="ct-fw-meta-row">
              <span className="ct-fw-meta-key">SLA</span>
              <span className="ct-fw-meta-val ct-fw-meta-sla-urgent">{task.slaTotal}</span>
            </div>
          </div>
        </div>

        {/* Citizen Evidence Card */}
        <div className="ct-fw-card ct-fw-citizen-evidence-card">
          <span className="ct-fw-card-header-label">Citizen evidence</span>
          <div className="ct-fw-evidence-photo-box">
            <div className="ct-fw-photo-placeholder">
              <ImageIcon size={36} className="ct-fw-photo-icon" />
              <span className="ct-fw-photo-text">PHOTO</span>
            </div>
          </div>
          <div className="ct-fw-evidence-footer-note">
            1 image attached • location metadata present
          </div>
        </div>
      </div>

      {/* Work Objective Card */}
      <div className="ct-fw-card ct-fw-work-objective-card">
        <div className="ct-fw-objective-header">
          <span className="ct-fw-card-header-label">Work objective</span>
          <span className="ct-fw-objective-badge">
            {task.objective?.badge || 'REPAIR REQUIRED'}
          </span>
        </div>

        <div className="ct-fw-objective-sections">
          <div className="ct-fw-objective-block">
            <span className="ct-fw-obj-label">Field action</span>
            <p className="ct-fw-obj-text">
              {task.objective?.fieldAction || 'Inspect, repair the pothole, and capture clear resolution evidence.'}
            </p>
          </div>

          <div className="ct-fw-objective-block">
            <span className="ct-fw-obj-label">Before work</span>
            <p className="ct-fw-obj-text">
              {task.objective?.beforeWork || 'Confirm the exact damage location and severity before starting.'}
            </p>
          </div>

          <div className="ct-fw-objective-block">
            <span className="ct-fw-obj-label">Completion requirement</span>
            <p className="ct-fw-obj-text">
              {task.objective?.completionRequirement || 'After-work evidence must show the repaired surface and match the incident location.'}
            </p>
          </div>
        </div>

        {/* Bottom CTA to Map */}
        <div className="ct-fw-objective-footer">
          <button 
            type="button" 
            className="ct-fw-continue-btn"
            onClick={handleContinueToMap}
          >
            <span>Continue to Map</span>
            <ArrowRight size={16} />
          </button>
        </div>
      </div>
    </div>
  );
};

export default FieldWorkerIncidentPage;
