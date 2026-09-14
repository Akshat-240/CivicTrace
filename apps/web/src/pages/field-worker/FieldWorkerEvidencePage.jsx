import React, { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { mockFieldWorkerData } from '../../data/mockData';
import { Camera, Upload, ArrowRight, CheckCircle2 } from 'lucide-react';
import './FieldWorkerEvidencePage.css';

const FieldWorkerEvidencePage = () => {
  const navigate = useNavigate();
  const task = mockFieldWorkerData.tasks[0];
  const { evidence } = task;

  const [workNotes, setWorkNotes] = useState(evidence.workNotes);
  const [evidenceNotes, setEvidenceNotes] = useState(evidence.evidenceNotes);
  const [afterImage, setAfterImage] = useState(null);
  const [isUploaded, setIsUploaded] = useState(true); // Default ready as in Figma

  const fileInputRef = useRef(null);

  const handleFileChange = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      const imageUrl = URL.createObjectURL(file);
      setAfterImage(imageUrl);
      setIsUploaded(true);
    }
  };

  const handleTriggerUpload = () => {
    if (fileInputRef.current) {
      fileInputRef.current.click();
    }
  };

  const handleContinue = () => {
    navigate('/field-worker/review');
  };

  return (
    <div className="ct-fw-page-container">
      {/* Header */}
      <div className="ct-fw-page-header">
        <h1 className="ct-fw-page-title">Evidence & Work Status</h1>
        <p className="ct-fw-page-subtitle">Record what was done and attach resolution evidence</p>
      </div>

      {/* Main Two-Column Grid */}
      <div className="ct-fw-evidence-grid">
        {/* Left Card: Work status */}
        <div className="ct-fw-card ct-fw-work-status-card">
          <div className="ct-fw-card-top-row">
            <span className="ct-fw-card-header-label">Work status</span>
            <span className="ct-fw-status-badge in-progress">
              {evidence.status}
            </span>
          </div>

          <div className="ct-fw-field-group">
            <span className="ct-fw-field-label">Action completed</span>
            <div className="ct-fw-action-completed-val">
              {evidence.actionCompleted}
            </div>
          </div>

          <div className="ct-fw-field-group">
            <label htmlFor="fwWorkNotes" className="ct-fw-field-label">Work notes</label>
            <textarea
              id="fwWorkNotes"
              className="ct-fw-textarea"
              rows={4}
              value={workNotes}
              onChange={(e) => setWorkNotes(e.target.value)}
              placeholder="Describe work performed in detail..."
            />
          </div>

          <div className="ct-fw-field-group">
            <span className="ct-fw-field-label">Evidence readiness</span>
            <div>
              <span className="ct-fw-readiness-badge">
                {evidence.readiness}
              </span>
            </div>
          </div>
        </div>

        {/* Right Card: Resolution evidence */}
        <div className="ct-fw-card ct-fw-resolution-evidence-card">
          <span className="ct-fw-card-header-label">Resolution evidence</span>

          {/* Side by Side Before / After Boxes */}
          <div className="ct-fw-evidence-boxes-container">
            {/* Before Box */}
            <div className="ct-fw-evidence-col">
              <span className="ct-fw-box-sublabel">Before</span>
              <div className="ct-fw-evidence-box before-box">
                <div className="ct-fw-box-center-tag">BEFORE</div>
                <div className="ct-fw-evidence-pothole-hint">Pothole detected</div>
              </div>
            </div>

            {/* After Box */}
            <div className="ct-fw-evidence-col">
              <span className="ct-fw-box-sublabel">After</span>
              <div 
                className="ct-fw-evidence-box after-box"
                onClick={handleTriggerUpload}
                title="Click to change after-photo"
              >
                {afterImage ? (
                  <img src={afterImage} alt="After work repair" className="ct-fw-uploaded-img-preview" />
                ) : (
                  <>
                    <div className="ct-fw-box-center-tag after-tag">AFTER</div>
                    <div className="ct-fw-evidence-repaired-hint">Surface leveled</div>
                  </>
                )}
              </div>
            </div>
          </div>

          {/* Hidden File Input */}
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileChange}
            accept="image/*"
            style={{ display: 'none' }}
          />

          {/* Upload / Capture CTA */}
          <div className="ct-fw-upload-action-row">
            <button
              type="button"
              className="ct-fw-capture-btn"
              onClick={handleTriggerUpload}
            >
              <Camera size={16} />
              <span>Capture / Upload</span>
            </button>
          </div>

          {/* Evidence Notes Input */}
          <div className="ct-fw-field-group">
            <label htmlFor="fwEvidenceNotes" className="ct-fw-field-label">Evidence notes</label>
            <textarea
              id="fwEvidenceNotes"
              className="ct-fw-textarea"
              rows={3}
              value={evidenceNotes}
              onChange={(e) => setEvidenceNotes(e.target.value)}
              placeholder="Notes on captured evidence..."
            />
          </div>

          {/* Continue CTA */}
          <div className="ct-fw-evidence-footer">
            <button
              type="button"
              className="ct-fw-continue-btn"
              onClick={handleContinue}
            >
              <span>Continue</span>
              <ArrowRight size={16} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default FieldWorkerEvidencePage;
