import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Road, 
  Trash2, 
  Droplet, 
  Waves, 
  Lightbulb, 
  Zap, 
  Mic, 
  ArrowRight, 
  Check, 
  UploadCloud, 
  MapPin, 
  CheckCircle2 
} from 'lucide-react';
import './CitizenReportPage.css';

export default function CitizenReportPage() {
  const navigate = useNavigate();
  const [currentStep, setCurrentStep] = useState(1);
  const [selectedCategory, setSelectedCategory] = useState('Road');
  const [description, setDescription] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [submittedId, setSubmittedId] = useState(null);

  const categories = [
    { name: 'Road', icon: <Road size={20} />, label: 'Pothole, broken asphalt, road caving' },
    { name: 'Garbage', icon: <Trash2 size={20} />, label: 'Overflowing bins, open dumping' },
    { name: 'Water', icon: <Droplet size={20} />, label: 'Pipe burst, water contamination' },
    { name: 'Drainage', icon: <Waves size={20} />, label: 'Blocked storm drain, sewer backflow' },
    { name: 'Streetlight', icon: <Lightbulb size={20} />, label: 'Light not working, flickering, dark spot' },
    { name: 'Electrical', icon: <Zap size={20} />, label: 'Exposed wiring, spark hazard, transformer' },
  ];

  const handleSpeechToggle = () => {
    setIsRecording(!isRecording);
    if (!isRecording) {
      setTimeout(() => {
        setDescription(prev => prev ? prev + ' (Deep pothole causing vehicle jam)' : 'Large pothole on road causing dangerous vehicle congestion.');
        setIsRecording(false);
      }, 1500);
    }
  };

  const handleNextStep = (e) => {
    e.preventDefault();
    if (currentStep < 4) {
      setCurrentStep(currentStep + 1);
    } else {
      // Complete submission
      setSubmittedId('CT-INC-025');
    }
  };

  return (
    <div className="citizen-report-container">
      {/* 4-Step Stepper */}
      <div className="citizen-stepper-bar">
        {[
          { num: 1, label: '1 Issue' },
          { num: 2, label: '2 Evidence' },
          { num: 3, label: '3 Location' },
          { num: 4, label: '4 Review' }
        ].map((s) => (
          <div 
            key={s.num}
            className={`stepper-pill ${currentStep === s.num ? 'active' : currentStep > s.num ? 'completed' : ''}`}
            onClick={() => setCurrentStep(s.num)}
          >
            {s.label}
          </div>
        ))}
      </div>

      {submittedId ? (
        /* Submission Success View */
        <div className="report-success-card">
          <div className="success-icon-wrapper">
            <CheckCircle2 size={48} className="success-check-icon" />
          </div>
          <h2 className="success-title">Report Filed Successfully!</h2>
          <p className="success-subtitle">
            Your complaint has been assigned incident ID <strong className="id-highlight">{submittedId}</strong> and routed to the municipal triage engine.
          </p>
          <div className="success-actions">
            <button 
              className="btn-track-submitted"
              onClick={() => navigate('/citizen/track')}
            >
              Track Report ({submittedId})
            </button>
            <button 
              className="btn-back-dashboard"
              onClick={() => navigate('/citizen/dashboard')}
            >
              Back to Dashboard
            </button>
          </div>
        </div>
      ) : (
        /* Form & Explainer Grid */
        <div className="citizen-report-grid">
          {/* Main Form Panel */}
          <div className="citizen-report-form-panel">
            {currentStep === 1 && (
              <>
                <div className="report-step-header">
                  <h2 className="report-step-title">What happened?</h2>
                  <p className="report-step-subtitle">Choose the closest category so we can understand your report.</p>
                </div>

                {/* Categories 3x2 Grid */}
                <div className="categories-grid">
                  {categories.map((cat) => (
                    <div 
                      key={cat.name}
                      className={`category-select-card ${selectedCategory === cat.name ? 'selected' : ''}`}
                      onClick={() => setSelectedCategory(cat.name)}
                    >
                      <div className="category-icon-title">
                        <span className="cat-icon">{cat.icon}</span>
                        <span className="cat-name">{cat.name}</span>
                      </div>
                      <span className="cat-select-indicator">
                        {selectedCategory === cat.name ? 'Selected' : 'Select'}
                      </span>
                    </div>
                  ))}
                </div>

                {/* Description Textarea */}
                <div className="report-desc-box">
                  <label className="desc-label">Describe the issue</label>
                  <div className="desc-textarea-wrapper">
                    <textarea 
                      className="desc-textarea"
                      placeholder="Tell us what happened..."
                      value={description}
                      onChange={(e) => setDescription(e.target.value)}
                      rows={3}
                    />
                    <button 
                      type="button" 
                      className={`mic-btn ${isRecording ? 'recording' : ''}`}
                      onClick={handleSpeechToggle}
                      title="Voice input"
                    >
                      <Mic size={16} />
                    </button>
                  </div>
                  <span className="desc-hint">You can also speak your description</span>
                </div>

                <div className="report-actions-row">
                  <button 
                    type="button" 
                    className="btn-continue-step"
                    onClick={handleNextStep}
                  >
                    <span>Continue</span>
                    <ArrowRight size={16} />
                  </button>
                </div>
              </>
            )}

            {currentStep === 2 && (
              <>
                <div className="report-step-header">
                  <h2 className="report-step-title">Upload Evidence</h2>
                  <p className="report-step-subtitle">Photographs allow automated AI verification and rapid authority dispatch.</p>
                </div>

                <div className="evidence-upload-zone">
                  <UploadCloud size={36} className="upload-cloud-icon" />
                  <p className="upload-zone-prompt">Drag & drop photo here or <span>Browse Files</span></p>
                  <span className="upload-zone-hint">Supports JPEG, PNG, HEIC up to 15MB. Geotagged photos automatically fill coordinates.</span>
                </div>

                <div className="sample-photo-preview">
                  <span className="preview-badge">Sample Attached</span>
                  <div className="photo-placeholder-box">
                    <span>Pothole photo attached with GPS metadata</span>
                  </div>
                </div>

                <div className="report-actions-row">
                  <button 
                    type="button" 
                    className="btn-step-back"
                    onClick={() => setCurrentStep(1)}
                  >
                    Back
                  </button>
                  <button 
                    type="button" 
                    className="btn-continue-step"
                    onClick={handleNextStep}
                  >
                    <span>Continue to Location</span>
                    <ArrowRight size={16} />
                  </button>
                </div>
              </>
            )}

            {currentStep === 3 && (
              <>
                <div className="report-step-header">
                  <h2 className="report-step-title">Confirm Location</h2>
                  <p className="report-step-subtitle">Exact location ensures your complaint reaches the correct ward nodal officer.</p>
                </div>

                <div className="location-confirm-box">
                  <div className="location-pin-header">
                    <MapPin size={20} className="loc-marker-icon" />
                    <div>
                      <h4 className="loc-addr-title">MG Road, Near Hazratganj Crossing</h4>
                      <p className="loc-addr-meta">Ward 12 · Zone 1 · Lucknow (Lat: 26.8467, Long: 80.9462)</p>
                    </div>
                  </div>

                  <div className="simulated-map-box">
                    <div className="map-circle-ping"></div>
                    <span className="map-ping-label">Incident GPS Lock Acquired</span>
                  </div>
                </div>

                <div className="report-actions-row">
                  <button 
                    type="button" 
                    className="btn-step-back"
                    onClick={() => setCurrentStep(2)}
                  >
                    Back
                  </button>
                  <button 
                    type="button" 
                    className="btn-continue-step"
                    onClick={handleNextStep}
                  >
                    <span>Review & Submit</span>
                    <ArrowRight size={16} />
                  </button>
                </div>
              </>
            )}

            {currentStep === 4 && (
              <>
                <div className="report-step-header">
                  <h2 className="report-step-title">Review & Submit</h2>
                  <p className="report-step-subtitle">Inspect the normalized report details before official dispatch.</p>
                </div>

                <div className="review-summary-list">
                  <div className="review-row">
                    <span className="review-key">Category</span>
                    <span className="review-val category-tag">{selectedCategory}</span>
                  </div>
                  <div className="review-row">
                    <span className="review-key">Description</span>
                    <span className="review-val">{description || 'Large pothole on road causing dangerous vehicle congestion.'}</span>
                  </div>
                  <div className="review-row">
                    <span className="review-key">Location</span>
                    <span className="review-val">MG Road, Near Hazratganj Crossing · Ward 12</span>
                  </div>
                  <div className="review-row">
                    <span className="review-key">Responsible Department</span>
                    <span className="review-val">Lucknow Municipal Corporation · Roads Division</span>
                  </div>
                  <div className="review-row">
                    <span className="review-key">Estimated SLA Target</span>
                    <span className="review-val highlight">Within 24 Hours</span>
                  </div>
                </div>

                <div className="report-actions-row">
                  <button 
                    type="button" 
                    className="btn-step-back"
                    onClick={() => setCurrentStep(3)}
                  >
                    Back
                  </button>
                  <button 
                    type="button" 
                    className="btn-submit-final"
                    onClick={handleNextStep}
                  >
                    <Check size={16} />
                    <span>Submit Incident Report</span>
                  </button>
                </div>
              </>
            )}
          </div>

          {/* Side Card: What happens next? */}
          <div className="citizen-explainer-card">
            <h3 className="explainer-title">What happens next?</h3>

            <div className="explainer-steps-list">
              <div className="explainer-step-item">
                <div className="explainer-num-badge">1</div>
                <div className="explainer-text-col">
                  <h4 className="explainer-step-heading">AI structures your report</h4>
                  <p className="explainer-step-body">Issue details are normalized</p>
                </div>
              </div>

              <div className="explainer-step-item">
                <div className="explainer-num-badge">2</div>
                <div className="explainer-text-col">
                  <h4 className="explainer-step-heading">Location is verified</h4>
                  <p className="explainer-step-body">We identify the correct jurisdiction</p>
                </div>
              </div>

              <div className="explainer-step-item">
                <div className="explainer-num-badge">3</div>
                <div className="explainer-text-col">
                  <h4 className="explainer-step-heading">Duplicates are checked</h4>
                  <p className="explainer-step-body">Related reports are linked</p>
                </div>
              </div>

              <div className="explainer-step-item">
                <div className="explainer-num-badge">4</div>
                <div className="explainer-text-col">
                  <h4 className="explainer-step-heading">Priority & SLA are assigned</h4>
                  <p className="explainer-step-body">Deterministic rules apply</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
