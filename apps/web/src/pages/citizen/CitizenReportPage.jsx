import React, { useState, useEffect } from 'react';
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
  CheckCircle2,
  Loader2,
  AlertTriangle
} from 'lucide-react';
import { createIncident } from '../../services/api';
import './CitizenReportPage.css';

export default function CitizenReportPage() {
  const navigate = useNavigate();
  const citizenId = localStorage.getItem('ct_user_id');

  useEffect(() => {
    if (!citizenId) {
      navigate('/login');
    }
  }, [citizenId, navigate]);

  const [currentStep, setCurrentStep] = useState(1);
  const [selectedCategory, setSelectedCategory] = useState('Road');
  const [description, setDescription] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [submittedId, setSubmittedId] = useState(null);
  const [realId, setRealId] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState(null);
  const [coords, setCoords] = useState({
    latitude: null,
    longitude: null,
    address_raw: "",
    isLiveGps: false,
  });
  const [locError, setLocError] = useState(null);

  useEffect(() => {
    if (typeof navigator !== 'undefined' && navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          setCoords({
            latitude: pos.coords.latitude,
            longitude: pos.coords.longitude,
            address_raw: `GPS Location (${pos.coords.latitude.toFixed(4)}, ${pos.coords.longitude.toFixed(4)})`,
            isLiveGps: true,
          });
          setLocError(null);
        },
        (err) => {
          console.warn('Geolocation unavailable or denied:', err);
          setLocError('Location access is required to submit a report. Please enable GPS.');
        },
        { timeout: 10000, enableHighAccuracy: true }
      );
    } else {
      setLocError('Geolocation is not supported by your browser.');
    }
  }, []);

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
        setDescription(prev => prev ? prev + ' (Voice input)' : 'Voice input');
        setIsRecording(false);
      }, 1500);
    }
  };

  const handleNextStep = async (e) => {
    e.preventDefault();
    if (currentStep < 4) {
      setCurrentStep(currentStep + 1);
    } else {
      // Step 4: Complete submission
      setIsSubmitting(true);
      setSubmitError(null);
      
      const issueTypeMap = {
        'Road': 'road_damage',
        'Garbage': 'illegal_dumping',
        'Water': 'water_leak',
        'Drainage': 'sewage_overflow',
        'Streetlight': 'broken_streetlight',
        'Electrical': 'other'
      };
      
      const payload = {
        title: selectedCategory + ' Issue',
        description: description || 'No description provided.',
        issue_type: issueTypeMap[selectedCategory] || 'other',
        location: {
          latitude: coords.latitude,
          longitude: coords.longitude,
          accuracy_meters: 10,
          address_raw: coords.address_raw,
        },
        fusion_metadata: {
          citizen_id: citizenId || "unknown_citizen"
        }
      };

      try {
        const response = await createIncident(payload);
        setSubmittedId(response.reference_number || response.id);
        setRealId(response.id);
      } catch (err) {
        console.error('Failed to submit incident:', err);
        setSubmitError(err.message || 'Failed to submit incident. Please check your connection and try again.');
      } finally {
        setIsSubmitting(false);
      }
    }
  };

  return (
    <div className="citizen-report-container">

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
              onClick={() => navigate(`/citizen/track?id=${realId || submittedId}`)}
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
            {submitError && (
              <div style={{ backgroundColor: '#fee2e2', color: '#b91c1c', padding: '1rem', borderRadius: '8px', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <AlertTriangle size={16} />
                <span style={{ fontSize: '0.9rem' }}>{submitError}</span>
              </div>
            )}
            
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
                      <MapPin size={20} className="loc-marker-icon" style={{ color: locError ? '#EF4444' : undefined }} />
                      <div>
                        {locError ? (
                          <>
                            <h4 className="loc-addr-title" style={{ color: '#EF4444' }}>Location Required</h4>
                            <p className="loc-addr-meta">{locError}</p>
                          </>
                        ) : (
                          <>
                            <h4 className="loc-addr-title">{coords.address_raw}</h4>
                            <p className="loc-addr-meta">
                              {coords.isLiveGps ? 'Live GPS Location' : 'Manual Location'}
                              {' '}(Lat: {coords.latitude?.toFixed(4)}, Long: {coords.longitude?.toFixed(4)})
                            </p>
                          </>
                        )}
                      </div>
                    </div>

                    <div className="simulated-map-box">
                      {!locError && <div className="map-circle-ping"></div>}
                      <span className="map-ping-label">
                        {locError ? 'No GPS Lock' : (coords.isLiveGps ? 'Live GPS Lock Acquired' : 'Location Set')}
                      </span>
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
                    disabled={!!locError}
                    style={locError ? { opacity: 0.5, cursor: 'not-allowed' } : {}}
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
                    <span className="review-val">{description || 'No description provided.'}</span>
                  </div>
                  <div className="review-row">
                    <span className="review-key">Location</span>
                    <span className="review-val">{coords.address_raw}</span>
                  </div>
                  <div className="review-row">
                    <span className="review-key">Responsible Department</span>
                    <span className="review-val" style={{ fontStyle: 'italic', color: '#6b7280' }}>Pending Triage Assignment</span>
                  </div>
                  <div className="review-row">
                    <span className="review-key">Estimated SLA Target</span>
                    <span className="review-val" style={{ fontStyle: 'italic', color: '#6b7280' }}>Pending SLA Evaluation</span>
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
                    disabled={isSubmitting}
                    style={{ opacity: isSubmitting ? 0.7 : 1, cursor: isSubmitting ? 'not-allowed' : 'pointer' }}
                  >
                    {isSubmitting ? <Loader2 size={16} className="animate-spin" /> : <Check size={16} />}
                    <span>{isSubmitting ? 'Submitting...' : 'Submit Incident Report'}</span>
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
                  <h4 className="explainer-step-heading">Authority & SLA are assigned</h4>
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
