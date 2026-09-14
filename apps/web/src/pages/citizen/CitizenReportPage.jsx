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
import { createIncident, getJurisdiction, uploadEvidence, analyzeEvidence, getIntelligenceReport } from '../../services/api';
import { MapContainer, TileLayer, Marker, useMapEvents } from 'react-leaflet';
import L from 'leaflet';
import './CitizenReportPage.css';

// Fix Leaflet's default icon path issues with Vite
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

function LocationMarker({ position, setPosition }) {
  useMapEvents({
    click(e) {
      setPosition(e.latlng);
    },
  });

  return position === null ? null : (
    <Marker position={position}></Marker>
  );
}

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
  const [evidenceFile, setEvidenceFile] = useState(null);
  const [evidencePreview, setEvidencePreview] = useState(null);
  const [evidenceId, setEvidenceId] = useState(null);
  const [aiResult, setAiResult] = useState(null);
  const [intelligence, setIntelligence] = useState(null);
  const [coords, setCoords] = useState({
    latitude: null,
    longitude: null,
    address_raw: "",
    isLiveGps: false,
  });
  const [locError, setLocError] = useState(null);
  const [mapPosition, setMapPosition] = useState(null);
  const [resolvingGis, setResolvingGis] = useState(false);

  const resolveAndSetLocation = async (lat, lng, isLive) => {
    setResolvingGis(true);
    setLocError(null);
    try {
      const res = await getJurisdiction(lat, lng);
      setCoords({
        latitude: lat,
        longitude: lng,
        address_raw: res.status === 'JURISDICTION_FOUND' ? res.explanation : 'Jurisdiction unresolved',
        isLiveGps: isLive,
      });
    } catch (error) {
      console.warn("GIS resolve failed", error);
      setCoords({
        latitude: lat,
        longitude: lng,
        address_raw: `Location coordinates captured (Lat: ${lat.toFixed(4)}, Long: ${lng.toFixed(4)})`,
        isLiveGps: isLive,
      });
    } finally {
      setResolvingGis(false);
    }
  };

  const requestGps = () => {
    setLocError(null);
    if (typeof navigator !== 'undefined' && navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          resolveAndSetLocation(pos.coords.latitude, pos.coords.longitude, true);
        },
        (err) => {
          console.warn('Geolocation unavailable or denied:', err);
          setLocError('Location access denied or unavailable. Please choose a location on the map.');
        },
        { timeout: 10000, enableHighAccuracy: true }
      );
    } else {
      setLocError('Geolocation is not supported by your browser.');
    }
  };

  useEffect(() => {
    requestGps();
  }, []);

  const handleManualLocationSubmit = () => {
    if (!mapPosition) {
      setLocError('Please place a marker on the map.');
      return;
    }
    resolveAndSetLocation(mapPosition.lat, mapPosition.lng, false);
  };

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

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setEvidenceFile(file);
      const reader = new FileReader();
      reader.onload = (ev) => {
        setEvidencePreview(ev.target.result);
      };
      reader.readAsDataURL(file);
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
        let currentIncidentId = realId;
        if (!currentIncidentId) {
          const response = await createIncident(payload);
          setSubmittedId(response.reference_number || response.id);
          currentIncidentId = response.id;
          setRealId(response.id);
        }

        if (evidenceFile && !aiResult) {
          let currentEvId = evidenceId;
          if (!currentEvId) {
            const evResponse = await uploadEvidence(currentIncidentId, evidenceFile);
            currentEvId = evResponse.id;
            setEvidenceId(currentEvId);
          }
          try {
            const aiData = await analyzeEvidence(currentIncidentId, currentEvId);
            setAiResult(aiData);
          } catch (aiErr) {
            console.error('AI Analysis Failed:', aiErr);
            throw new Error("AI analysis failed. Please retry.");
          }
        }

        // Generate structured intelligence report
        try {
          const report = await getIntelligenceReport(currentIncidentId);
          setIntelligence(report);
        } catch (intelErr) {
          console.error('Intelligence Report Failed:', intelErr);
        }
      } catch (err) {
        console.error('Failed to submit incident:', err);
        setSubmitError(err.message || 'Failed to submit incident. Please check your connection and try again.');
        setIsSubmitting(false);
        return; // Stop and allow retry
      } finally {
        if (!submitError) {
          setIsSubmitting(false);
        }
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

          {isSubmitting && !aiResult && evidenceFile && (
            <div style={{margin: '20px 0', padding: '15px', background: '#f8f9fa', borderRadius: '8px', textAlign: 'center'}}>
              <Loader2 className="spinning" size={24} style={{marginBottom: '10px', color: '#0d6efd'}} />
              <p>Analyzing evidence using AI...</p>
            </div>
          )}

          {submitError && (
             <div style={{margin: '20px 0', padding: '15px', background: '#fff3cd', color: '#856404', borderRadius: '8px', textAlign: 'center'}}>
                <AlertTriangle size={24} style={{marginBottom: '10px'}} />
                <p>{submitError}</p>
                <button onClick={handleNextStep} style={{marginTop: '10px', padding: '5px 15px'}}>Retry Analysis</button>
             </div>
          )}

          {intelligence && (
            <div style={{margin: '20px 0', border: '1px solid #e5e7eb', borderRadius: '8px', overflow: 'hidden', boxShadow: '0 1px 3px rgba(0,0,0,0.05)'}}>
              <div style={{background: '#f8fafc', padding: '12px 20px', borderBottom: '1px solid #e5e7eb', display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
                <h3 style={{margin: 0, fontSize: '1.1rem', color: '#0f172a', fontWeight: '600'}}>CivicTrace Intelligence</h3>
                <span style={{fontSize: '0.75rem', background: '#dbeafe', color: '#1e40af', padding: '2px 8px', borderRadius: '12px', fontWeight: '500'}}>AI + GIS Enhanced</span>
              </div>

              <div style={{padding: '20px'}}>
                {/* AI EVIDENCE ASSESSMENT */}
                <div style={{marginBottom: '24px'}}>
                  <h4 style={{fontSize: '0.85rem', textTransform: 'uppercase', color: '#64748b', letterSpacing: '0.05em', margin: '0 0 12px 0', borderBottom: '1px solid #f1f5f9', paddingBottom: '4px'}}>AI Evidence Assessment</h4>
                  {evidencePreview && (
                     <div style={{marginBottom: '15px'}}>
                       <img src={evidencePreview} alt="Evidence" style={{width: '100%', maxHeight: '160px', objectFit: 'cover', borderRadius: '6px', border: '1px solid #e2e8f0'}} />
                     </div>
                  )}

                  <div style={{display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '12px'}}>
                    <div>
                      <span style={{color: '#64748b', fontSize: '0.8rem', display: 'block'}}>Issue</span>
                      <div style={{fontWeight: '500', color: '#334155', fontSize: '0.95rem'}}>{intelligence.normalized_issue_category || intelligence.issue_category || 'Unknown'}</div>
                    </div>
                    {intelligence.severity && (
                      <div>
                        <span style={{color: '#64748b', fontSize: '0.8rem', display: 'block'}}>Severity</span>
                        <div style={{fontWeight: '500', color: '#334155', fontSize: '0.95rem'}}>{intelligence.severity}</div>
                      </div>
                    )}
                    {intelligence.confidence !== null && (
                      <div>
                        <span style={{color: '#64748b', fontSize: '0.8rem', display: 'block'}}>Confidence</span>
                        <div style={{fontWeight: '500', color: '#334155', fontSize: '0.95rem'}}>{(intelligence.confidence * 100).toFixed(0)}%</div>
                      </div>
                    )}
                    <div>
                      <span style={{color: '#64748b', fontSize: '0.8rem', display: 'block'}}>Evidence Quality</span>
                      <div style={{fontWeight: '500', color: '#334155', fontSize: '0.95rem'}}>{intelligence.evidence_quality || 'N/A'}</div>
                    </div>
                  </div>

                  {intelligence.visual_finding && (
                    <div style={{marginBottom: '12px'}}>
                      <span style={{color: '#64748b', fontSize: '0.8rem', display: 'block'}}>Visual Finding</span>
                      <p style={{margin: '2px 0 0 0', fontSize: '0.95rem', color: '#334155'}}>{intelligence.visual_finding}</p>
                    </div>
                  )}

                  {intelligence.safety_risk && (
                    <div style={{background: '#fee2e2', color: '#991b1b', padding: '8px 12px', borderRadius: '6px', fontSize: '0.85rem', display: 'flex', alignItems: 'center', gap: '8px', marginTop: '8px'}}>
                      <AlertTriangle size={14} />
                      <span><strong>Safety Risk:</strong> Potential road-user or public hazard detected.</span>
                    </div>
                  )}

                  {intelligence.ambiguity_flag && (
                    <div style={{background: '#fef3c7', color: '#92400e', padding: '8px 12px', borderRadius: '6px', fontSize: '0.85rem', display: 'flex', alignItems: 'center', gap: '8px', marginTop: '8px'}}>
                      <AlertTriangle size={14} />
                      <span><strong>Needs review:</strong> {intelligence.ambiguity_reason || "Image does not provide sufficient clear visual evidence."}</span>
                    </div>
                  )}
                </div>

                {/* LOCATION INTELLIGENCE */}
                <div style={{marginBottom: '24px'}}>
                  <h4 style={{fontSize: '0.85rem', textTransform: 'uppercase', color: '#64748b', letterSpacing: '0.05em', margin: '0 0 12px 0', borderBottom: '1px solid #f1f5f9', paddingBottom: '4px'}}>Location Intelligence</h4>
                  <div style={{display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px'}}>
                    <div>
                      <span style={{color: '#64748b', fontSize: '0.8rem', display: 'block'}}>Coordinates</span>
                      <div style={{fontWeight: '500', color: '#334155', fontSize: '0.95rem'}}>{intelligence.latitude?.toFixed(4)}, {intelligence.longitude?.toFixed(4)}</div>
                    </div>
                    <div>
                      <span style={{color: '#64748b', fontSize: '0.8rem', display: 'block'}}>Ward</span>
                      <div style={{fontWeight: '500', color: '#334155', fontSize: '0.95rem'}}>{intelligence.ward || 'Pending GIS'}</div>
                    </div>
                    <div style={{gridColumn: '1 / -1'}}>
                      <span style={{color: '#64748b', fontSize: '0.8rem', display: 'block'}}>Jurisdiction</span>
                      <div style={{fontWeight: '500', color: '#334155', fontSize: '0.95rem'}}>{intelligence.jurisdiction || 'Pending GIS'}</div>
                    </div>
                  </div>
                </div>

                {/* RESPONSIBILITY */}
                <div style={{marginBottom: '24px'}}>
                  <h4 style={{fontSize: '0.85rem', textTransform: 'uppercase', color: '#64748b', letterSpacing: '0.05em', margin: '0 0 12px 0', borderBottom: '1px solid #f1f5f9', paddingBottom: '4px'}}>Responsibility</h4>
                  <div style={{display: 'grid', gridTemplateColumns: '1fr', gap: '12px'}}>
                    <div>
                      <span style={{color: '#64748b', fontSize: '0.8rem', display: 'block'}}>Responsible Authority</span>
                      <div style={{fontWeight: '500', color: '#334155', fontSize: '0.95rem'}}>{intelligence.responsible_authority || 'Authority mapping unavailable'}</div>
                    </div>
                    <div>
                      <span style={{color: '#64748b', fontSize: '0.8rem', display: 'block'}}>Department</span>
                      <div style={{fontWeight: '500', color: '#334155', fontSize: '0.95rem'}}>{intelligence.responsible_department || 'Department mapping unavailable'}</div>
                    </div>
                    <div>
                      <span style={{color: '#64748b', fontSize: '0.8rem', display: 'block'}}>Basis</span>
                      <div style={{fontWeight: '500', color: '#334155', fontSize: '0.95rem'}}>{intelligence.responsibility_basis}</div>
                    </div>
                  </div>
                </div>

                {/* SLA */}
                <div style={{marginBottom: '24px'}}>
                  <h4 style={{fontSize: '0.85rem', textTransform: 'uppercase', color: '#64748b', letterSpacing: '0.05em', margin: '0 0 12px 0', borderBottom: '1px solid #f1f5f9', paddingBottom: '4px'}}>Service Level Agreement</h4>
                  <div style={{display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px'}}>
                    <div>
                      <span style={{color: '#64748b', fontSize: '0.8rem', display: 'block'}}>Target</span>
                      <div style={{fontWeight: '500', color: '#334155', fontSize: '0.95rem'}}>{intelligence.resolution_target || 'N/A'}</div>
                    </div>
                    <div>
                      <span style={{color: '#64748b', fontSize: '0.8rem', display: 'block'}}>Due</span>
                      <div style={{fontWeight: '500', color: '#334155', fontSize: '0.95rem'}}>{intelligence.due_at ? new Date(intelligence.due_at).toLocaleString() : 'N/A'}</div>
                    </div>
                  </div>
                </div>

                {/* SUMMARY */}
                <div style={{background: '#f8fafc', padding: '12px 16px', borderRadius: '6px', borderLeft: '3px solid #3b82f6'}}>
                  <h4 style={{fontSize: '0.85rem', textTransform: 'uppercase', color: '#1e40af', letterSpacing: '0.05em', margin: '0 0 8px 0'}}>CivicTrace Assessment</h4>
                  <p style={{margin: '0', fontSize: '0.95rem', color: '#334155', lineHeight: '1.5'}}>{intelligence.civictrace_summary}</p>
                </div>

                <div style={{marginTop: '16px', fontSize: '0.75rem', color: '#94a3b8', fontStyle: 'italic', textAlign: 'center'}}>
                  AI perception is advisory. Final responsibility and administrative decisions are determined by CivicTrace rules and authorized workflows.
                </div>
              </div>
            </div>
          )}

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

                <div className="evidence-upload-zone" style={{position: 'relative'}}>
                  <input
                    type="file"
                    accept="image/jpeg, image/png, image/webp"
                    onChange={handleFileChange}
                    style={{position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', opacity: 0, cursor: 'pointer'}}
                  />
                  <UploadCloud size={36} className="upload-cloud-icon" />
                  <p className="upload-zone-prompt">Drag & drop photo here or <span>Browse Files</span></p>
                  <span className="upload-zone-hint">Supports JPEG, PNG, WEBP up to 20MB.</span>
                </div>

                {evidencePreview && (
                  <div className="sample-photo-preview" style={{marginTop: '1rem'}}>
                    <span className="preview-badge">Image Attached</span>
                    <div style={{marginTop: '10px'}}>
                      <img src={evidencePreview} alt="Evidence Preview" style={{maxHeight: '150px', borderRadius: '8px'}} />
                    </div>
                  </div>
                )}

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
                        {resolvingGis ? 'Resolving Jurisdiction...' : (locError ? 'No GPS Lock' : (coords.isLiveGps ? 'Live GPS Lock Acquired' : 'Location Set'))}
                      </span>
                    </div>

                    {locError && (
                      <div style={{ marginTop: '1rem', padding: '1rem', background: '#F8FAFC', borderRadius: '8px', border: '1px solid #E2E8F0' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
                          <h5 style={{ fontSize: '0.9rem', fontWeight: 600, color: '#334155', margin: 0 }}>Select Location on Map</h5>
                          <button
                            type="button"
                            onClick={requestGps}
                            style={{ padding: '0.35rem 0.75rem', backgroundColor: '#F1F5F9', color: '#475569', border: '1px solid #CBD5E1', borderRadius: '4px', fontSize: '0.75rem', cursor: 'pointer' }}
                          >
                            Retry GPS
                          </button>
                        </div>
                        <div style={{ height: '300px', width: '100%', marginBottom: '1rem', borderRadius: '6px', overflow: 'hidden', border: '1px solid #CBD5E1' }}>
                          <MapContainer center={[26.8467, 80.9462]} zoom={12} style={{ height: '100%', width: '100%' }}>
                            <TileLayer
                              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                              attribution='&copy; OpenStreetMap contributors'
                            />
                            <LocationMarker position={mapPosition} setPosition={setMapPosition} />
                          </MapContainer>
                        </div>
                        <button
                          type="button"
                          onClick={handleManualLocationSubmit}
                          disabled={resolvingGis || !mapPosition}
                          style={{ width: '100%', padding: '0.65rem', backgroundColor: '#3B82F6', color: 'white', border: 'none', borderRadius: '6px', fontSize: '0.9rem', fontWeight: 500, cursor: (resolvingGis || !mapPosition) ? 'not-allowed' : 'pointer', opacity: (resolvingGis || !mapPosition) ? 0.6 : 1 }}
                        >
                          {resolvingGis ? 'Resolving Jurisdiction...' : 'Confirm Location'}
                        </button>
                      </div>
                    )}
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
                  {evidenceFile && (
                    <div className="review-row">
                      <span className="review-key">Evidence</span>
                      <span className="review-val">
                        <div style={{fontWeight: '500', color: '#1f2937'}}>1 image attached</div>
                        <div style={{fontSize: '0.85rem', color: '#0d6efd', marginTop: '4px'}}>AI assessment available upon submission</div>
                      </span>
                    </div>
                  )}
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
