import React, { useState } from 'react';
import PageHeader from '../../components/layout/PageHeader';
import Modal from '../../components/common/Modal';
import './VerificationPage.css';

const VerificationPage = () => {
  const pendingCases = [
    {
      id: "CT-INC-024",
      title: "Pothole on MG Road",
      submittedBy: "Road Team 04",
      beforeLabel: "Pothole detected",
      afterLabel: "Repair visible",
      aiScore: "96%",
      aiResolution: "Partial resolution",
      department: "Road Infrastructure",
      location: "Hazratganj, MG Road"
    },
    {
      id: "CT-INC-019",
      title: "Streetlight not working",
      submittedBy: "Electrical Team 01",
      beforeLabel: "Dark pole fixture",
      afterLabel: "Fixture lit & operational",
      aiScore: "99%",
      aiResolution: "Full resolution",
      department: "Electrical Works",
      location: "Gomti Nagar, Viram Khand"
    }
  ];

  const [currentIndex, setCurrentIndex] = useState(0);
  const [selectedState, setSelectedState] = useState('PARTIALLY_RESOLVED');
  const [saveSuccess, setSaveSuccess] = useState(null);
  const [isEvidenceModalOpen, setIsEvidenceModalOpen] = useState(false);

  const currentCase = pendingCases[currentIndex] || pendingCases[0];

  const groundTruthOptions = [
    { key: "FULLY_RESOLVED", label: "FULLY_RESOLVED", colorClass: "ct-gt-green" },
    { key: "PARTIALLY_RESOLVED", label: "PARTIALLY_RESOLVED", colorClass: "ct-gt-orange" },
    { key: "NOT_RESOLVED", label: "NOT_RESOLVED", colorClass: "ct-gt-red" },
    { key: "INSUFFICIENT_EVIDENCE", label: "INSUFFICIENT_EVIDENCE", colorClass: "ct-gt-grey" },
    { key: "HUMAN_REVIEW", label: "HUMAN_REVIEW", colorClass: "ct-gt-blue" }
  ];

  const handleSaveDecision = () => {
    setSaveSuccess(`Decision saved for ${currentCase.id}: marked as ${selectedState}.`);
    
    setTimeout(() => {
      setSaveSuccess(null);
      if (currentIndex < pendingCases.length - 1) {
        setCurrentIndex(currentIndex + 1);
      }
    }, 2000);
  };

  return (
    <div className="ct-verification-page">
      <PageHeader 
        title="Incident Verification"
        subtitle="Review resolution evidence before an incident can be closed."
      />

      {saveSuccess && (
        <div className="ct-save-banner">
          {saveSuccess}
        </div>
      )}

      {/* Top Banner Card */}
      <div className="ct-card ct-pending-card">
        <div className="ct-pending-left">
          <h2 className="ct-pending-title">Pending verification</h2>
          <p className="ct-pending-desc">7 cases require review</p>
        </div>
        <div className="ct-pending-right">
          <span className="ct-evidence-badge">Evidence required</span>
        </div>
      </div>

      {/* Two Column Section */}
      <div className="ct-verification-grid">
        {/* Left: Evidence Review Card */}
        <div className="ct-card ct-evidence-card">
          <div className="ct-card-head">
            <h2 className="ct-card-title">{currentCase.id} · {currentCase.title}</h2>
            <p className="ct-card-desc">Resolution evidence submitted by {currentCase.submittedBy}</p>
          </div>

          <div className="ct-photo-panels">
            {/* Before Photo */}
            <div className="ct-photo-box">
              <div className="ct-photo-tag">BEFORE</div>
              <div className="ct-photo-visual">
                <div className="ct-photo-placeholder-text">{currentCase.beforeLabel}</div>
              </div>
            </div>

            {/* After Photo */}
            <div className="ct-photo-box">
              <div className="ct-photo-tag">AFTER</div>
              <div className="ct-photo-visual">
                <div className="ct-photo-placeholder-text">{currentCase.afterLabel}</div>
              </div>
            </div>
          </div>

          {/* AI Score & Action Footer */}
          <div className="ct-evidence-footer">
            <div className="ct-evidence-pills">
              <span className="ct-ai-verified-pill">AI VERIFIED · {currentCase.aiScore}</span>
              <span className="ct-partial-pill">{currentCase.aiResolution}</span>
            </div>
            <button 
              type="button" 
              className="ct-btn-openevidence"
              onClick={() => setIsEvidenceModalOpen(true)}
            >
              Open evidence
            </button>
          </div>
        </div>

        {/* Right: Ground Truth State Selector */}
        <div className="ct-card ct-groundtruth-card">
          <div className="ct-card-head">
            <h2 className="ct-card-title">Ground Truth State</h2>
            <p className="ct-card-desc">Select the final accountable state</p>
          </div>

          <div className="ct-groundtruth-list">
            {groundTruthOptions.map((opt) => (
              <div 
                key={opt.key}
                className={`ct-groundtruth-item ${opt.colorClass} ${selectedState === opt.key ? 'selected' : ''}`}
                onClick={() => setSelectedState(opt.key)}
              >
                {opt.label}
              </div>
            ))}
          </div>

          <div className="ct-decision-action">
            <button 
              type="button" 
              className="ct-btn-savedecision"
              onClick={handleSaveDecision}
            >
              Save decision
            </button>
          </div>
        </div>
      </div>

      {/* Full Evidence Inspection Modal */}
      <Modal
        isOpen={isEvidenceModalOpen}
        onClose={() => setIsEvidenceModalOpen(false)}
        title={`Evidence Inspection: ${currentCase.id}`}
      >
        <div className="ct-modal-evidence-detail">
          <div className="ct-evidence-meta-row">
            <div>
              <strong>Location:</strong> {currentCase.location}
            </div>
            <div>
              <strong>Field Team:</strong> {currentCase.submittedBy}
            </div>
            <div>
              <strong>Model Confidence:</strong> {currentCase.aiScore}
            </div>
          </div>

          <div className="ct-modal-photo-preview">
            <div className="ct-modal-photo-col">
              <h4>Citizen Report Evidence (Before)</h4>
              <div className="ct-modal-photo-frame">
                <span className="ct-frame-tag">{currentCase.beforeLabel}</span>
                <p className="ct-frame-meta">Captured: 12 Sep 2026 09:32 AM</p>
              </div>
            </div>
            <div className="ct-modal-photo-col">
              <h4>Authority Resolution Evidence (After)</h4>
              <div className="ct-modal-photo-frame">
                <span className="ct-frame-tag">{currentCase.afterLabel}</span>
                <p className="ct-frame-meta">Uploaded: 12 Sep 2026 02:45 PM</p>
              </div>
            </div>
          </div>

          <div className="ct-modal-actions">
            <button 
              type="button" 
              className="btn btn-outline"
              onClick={() => setIsEvidenceModalOpen(false)}
            >
              Close
            </button>
          </div>
        </div>
      </Modal>
    </div>
  );
};

export default VerificationPage;
