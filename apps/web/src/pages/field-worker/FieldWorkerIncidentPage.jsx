import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { getWorkerTaskDetail, updateWorkerTaskStatus } from '../../services/api';
import { Image as ImageIcon, ArrowRight } from 'lucide-react';
import './FieldWorkerIncidentPage.css';

const FieldWorkerIncidentPage = () => {
  const navigate = useNavigate();
  const { id } = useParams();
  const [task, setTask] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadIncident() {
      try {
        setLoading(true);
        const res = await getWorkerTaskDetail(id);
        setTask(res);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    if (id) loadIncident();
  }, [id]);

  const handleContinueToMap = async () => {
    try {
      let currentStatus = task.worker_status;
      if (currentStatus === 'ASSIGNED') {
        await updateWorkerTaskStatus(task.id, 'ACCEPTED');
        currentStatus = 'ACCEPTED';
      }
      if (currentStatus === 'ACCEPTED') {
        await updateWorkerTaskStatus(task.id, 'ON_THE_WAY');
      }
    } catch (e) {
      console.error(e);
      alert('Failed to update status. Please try again.');
      return;
    }
    navigate(`/field-worker/location?id=${task.id}`);
  };

  if (!id || id === 'none') return <div style={{padding: '2rem'}}>No task selected. Please select a task from the dashboard.</div>;
  if (loading) return <div style={{padding: '2rem'}}>Loading incident details...</div>;
  if (!task) return <div style={{padding: '2rem'}}>Incident not found.</div>;

  const displayId = task.reference_number || task.id.substring(0,8).toUpperCase();
  const title = task.title || 'Untitled Incident';
  const category = task.issue_type?.replace(/_/g, ' ')?.toUpperCase() || 'GENERAL ISSUE';

  return (
    <div className="ct-fw-page-container">
      {/* Header */}
      <div className="ct-fw-page-header">
        <h1 className="ct-fw-page-title">Incident Details</h1>
        <p className="ct-fw-page-subtitle">{displayId} - {title}</p>
      </div>

      {/* Top Two Column Cards */}
      <div className="ct-fw-incident-grid-top">
        {/* Incident Summary Card */}
        <div className="ct-fw-card ct-fw-incident-summary-card">
          <span className="ct-fw-card-header-label">Incident summary</span>
          <h2 className="ct-fw-incident-main-heading">{title}</h2>
          <div className="ct-fw-incident-category-sub">{category}</div>

          <div className="ct-fw-incident-meta-list">
            <div className="ct-fw-meta-row">
              <span className="ct-fw-meta-key">Reported by</span>
              <span className="ct-fw-meta-val">Citizen via App</span>
            </div>
            <div className="ct-fw-meta-row">
              <span className="ct-fw-meta-key">Assigned authority</span>
              <span className="ct-fw-meta-val">Your Authority</span>
            </div>
            <div className="ct-fw-meta-row">
              <span className="ct-fw-meta-key">SLA</span>
              <span className="ct-fw-meta-val ct-fw-meta-sla-urgent">{task.priority || 'PENDING'}</span>
            </div>
          </div>
        </div>

        {/* Citizen Evidence Card */}
        <div className="ct-fw-card ct-fw-citizen-evidence-card">
          <span className="ct-fw-card-header-label">Citizen evidence</span>
          <div className="ct-fw-evidence-photo-box">
            <div className="ct-fw-photo-placeholder">
              {task.before_evidence_url ? <img src={task.before_evidence_url} alt="Before Evidence" style={{width: "100%", height: "100%", objectFit: "cover"}} /> : <><ImageIcon size={36} className="ct-fw-photo-icon" /><span className="ct-fw-photo-text">PHOTO</span></>}
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
          <span className="ct-fw-objective-badge">REPAIR REQUIRED</span>
        </div>

        <div className="ct-fw-objective-sections">
          <div className="ct-fw-objective-block">
            <span className="ct-fw-obj-label">Field action</span>
            <p className="ct-fw-obj-text">
              Inspect, repair the reported issue, and capture clear resolution evidence.
            </p>
          </div>

          <div className="ct-fw-objective-block">
            <span className="ct-fw-obj-label">Description</span>
            <p className="ct-fw-obj-text">
              {task.description || 'No description provided.'}
            </p>
          </div>

          <div className="ct-fw-objective-block">
            <span className="ct-fw-obj-label">Completion requirement</span>
            <p className="ct-fw-obj-text">
              After-work evidence must show the repaired surface and match the incident location.
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






