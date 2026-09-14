import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { mockFieldWorkerData } from '../../data/mockData';
import { CheckCircle2, ShieldCheck, ArrowLeft, ArrowRight } from 'lucide-react';
import './FieldWorkerReviewPage.css';

const FieldWorkerReviewPage = () => {
  const navigate = useNavigate();
  const task = mockFieldWorkerData.tasks[0];
  const { submission } = task;

  const [isSubmitted, setIsSubmitted] = useState(false);

  const handleSubmit = () => {
    setIsSubmitted(true);
  };

  const handleReturnToDashboard = () => {
    navigate('/field-worker/dashboard');
  };

  return (
    <div className="ct-fw-page-container">
      {/* Header */}
      <div className="ct-fw-page-header">
        <h1 className="ct-fw-page-title">Review & Submit</h1>
        <p className="ct-fw-page-subtitle">Final field-worker submission before authority verification</p>
      </div>

      {/* Two Column Layout */}
      <div className="ct-fw-review-grid">
        {/* Left Card: Submission summary */}
        <div className="ct-fw-card ct-fw-summary-card">
          <span className="ct-fw-card-header-label">Submission summary</span>

          <div className="ct-fw-summary-list">
            <div className="ct-fw-summary-item">
              <span className="ct-fw-summary-label">Incident</span>
              <span className="ct-fw-summary-val">{task.title}</span>
            </div>

            <div className="ct-fw-summary-item">
              <span className="ct-fw-summary-label">Location</span>
              <span className="ct-fw-summary-val">MG Road • Ward 12 • GPS confirmed</span>
            </div>

            <div className="ct-fw-summary-item">
              <span className="ct-fw-summary-label">Work status</span>
              <span className="ct-fw-summary-val ct-fw-val-highlight">{submission.workStatus}</span>
            </div>

            <div className="ct-fw-summary-item">
              <span className="ct-fw-summary-label">Resolution evidence</span>
              <span className="ct-fw-summary-val">Before + After captured</span>
            </div>

            <div className="ct-fw-summary-item">
              <span className="ct-fw-summary-label">Work note</span>
              <span className="ct-fw-summary-val">Repair completed; surface level checked</span>
            </div>
          </div>
        </div>

        {/* Right Card: Submission checks */}
        <div className="ct-fw-card ct-fw-checks-card">
          <span className="ct-fw-card-header-label">Submission checks</span>

          <div className="ct-fw-pass-checks-list">
            {submission.checks.map((chk, idx) => (
              <div key={idx} className="ct-fw-pass-row">
                <span className="ct-fw-pass-badge">PASS</span>
                <span className="ct-fw-pass-name">{chk.name}</span>
              </div>
            ))}
          </div>

          <div className="ct-fw-next-step-section">
            <span className="ct-fw-next-step-label">Next step</span>
            <p className="ct-fw-next-step-text">{submission.nextStep}</p>
          </div>

          <div className="ct-fw-submission-actions">
            <button
              type="button"
              className="ct-fw-submit-btn"
              onClick={handleSubmit}
            >
              Submit Work Record
            </button>
            <button
              type="button"
              className="ct-fw-back-btn"
              onClick={() => navigate('/field-worker/evidence')}
            >
              Back to Evidence
            </button>
          </div>
        </div>
      </div>

      {/* Success Modal */}
      {isSubmitted && (
        <div className="ct-fw-modal-backdrop" onClick={handleReturnToDashboard}>
          <div className="ct-fw-success-modal" onClick={(e) => e.stopPropagation()}>
            <div className="ct-fw-modal-icon-circle">
              <CheckCircle2 size={44} className="ct-fw-modal-icon" />
            </div>
            <h2 className="ct-fw-modal-title">Work Record Submitted</h2>
            <p className="ct-fw-modal-desc">
              Incident <strong>CT-INC-024</strong> has been marked completed with GPS and Before/After photographic evidence attached.
            </p>
            <div className="ct-fw-modal-meta-box">
              <div className="ct-fw-modal-meta-line">
                <span>Verification State:</span>
                <span className="ct-fw-tag-pending">SENT TO AUTHORITY</span>
              </div>
              <div className="ct-fw-modal-meta-line">
                <span>Logged Coordinates:</span>
                <span>26.8467° N, 80.9462° E</span>
              </div>
            </div>
            <button
              type="button"
              className="ct-fw-modal-confirm-btn"
              onClick={handleReturnToDashboard}
            >
              <span>Return to Assigned Work</span>
              <ArrowRight size={16} />
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default FieldWorkerReviewPage;
