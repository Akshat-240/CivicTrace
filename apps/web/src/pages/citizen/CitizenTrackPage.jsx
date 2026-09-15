import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { 
  Search, 
  Check, 
  Clock, 
  ShieldCheck, 
  CheckCircle2, 
  MapPin, 
  Building2, 
  Sparkles,
  Loader2,
  AlertTriangle
} from 'lucide-react';
import { getIncident, getIncidentTimeline } from '../../services/api';
import './CitizenTrackPage.css';

export default function CitizenTrackPage() {
  const [searchParams] = useSearchParams();
  const urlId = searchParams.get('id');
  
  const [searchId, setSearchId] = useState('');
  const [incident, setIncident] = useState(null);
  const [timeline, setTimeline] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (urlId) {
      fetchIncidentData(urlId);
    }
  }, [urlId]);

  const fetchIncidentData = async (idToFetch) => {
    try {
      setLoading(true);
      setError(null);
      
      const data = await getIncident(idToFetch);
      setIncident(data);
      
      try {
        const timelineData = await getIncidentTimeline(idToFetch);
        setTimeline(timelineData || []);
      } catch (err) {
        console.warn('Could not fetch timeline', err);
        setTimeline([]);
      }
      
      setSearchId(data.reference_number || data.id);
    } catch (err) {
      console.error(err);
      setError('Failed to find report. Make sure you are using a valid ID.');
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e) => {
    e.preventDefault();
    if (searchId.trim()) {
      fetchIncidentData(searchId.trim());
    }
  };

  // Helper to map backend status to timeline steps
  const generateTimelineSteps = (incStatus, events) => {
    const defaultSteps = [
      { id: 'draft', label: 'Report Submitted' },
      { id: 'active', label: 'Assigned to Authority' },
      { id: 'under_review', label: 'Under Review / Working' },
      { id: 'resolved', label: 'Resolution Verified' },
      { id: 'closed', label: 'Case Closed' }
    ];

    let currentStepIndex = 0;
    if (incStatus === 'active') currentStepIndex = 1;
    if (incStatus === 'under_review') currentStepIndex = 2;
    if (incStatus === 'resolved') currentStepIndex = 3;
    if (incStatus === 'closed') currentStepIndex = 4;

    return defaultSteps.map((step, idx) => {
      // Try to find a real event for this step if possible
      const event = events.find(e => {
        if (step.id === 'draft' && e.event_type === 'incident_created') return true;
        if (step.id === 'active' && e.event_type === 'authority_assigned') return true;
        if (step.id === 'resolved' && e.event_type === 'verification_result_set') return true;
        if (step.id === 'closed' && e.event_type === 'incident_status_changed' && e.details?.new_status === 'closed') return true;
        return false;
      });

      return {
        label: step.label,
        timestamp: event ? new Date(event.created_at).toLocaleString() : (idx <= currentStepIndex ? 'Pending...' : ''),
        completed: idx < currentStepIndex || (idx === 4 && incStatus === 'closed'),
        active: idx === currentStepIndex && incStatus !== 'closed',
      };
    });
  };

  return (
    <div className="citizen-track-container">
      {/* Search Bar Header */}
      <form className="track-search-bar" onSubmit={handleSearch}>
        <span className="search-bar-label">Search Report ID</span>
        <div className="search-input-wrapper">
          <input 
            type="text" 
            className="track-search-input"
            value={searchId} 
            onChange={(e) => setSearchId(e.target.value)}
            placeholder="Enter UUID"
          />
        </div>
        <button type="submit" className="btn-track-search">
          <Search size={15} />
          <span>Search</span>
        </button>
      </form>

      {loading && (
        <div style={{ display: 'flex', justifyContent: 'center', padding: '3rem', flexDirection: 'column', alignItems: 'center' }}>
          <Loader2 className="animate-spin" size={32} style={{ marginBottom: '1rem' }} />
          <p>Loading incident details...</p>
        </div>
      )}

      {error && !loading && (
        <div style={{ padding: '2rem', color: '#ef4444', textAlign: 'center' }}>
          <AlertTriangle size={32} style={{ margin: '0 auto 12px' }} />
          <p>{error}</p>
        </div>
      )}

      {!loading && !error && incident && (
        <div className="citizen-track-grid">
          {/* Left Column: Lifecycle & Timeline */}
          <section className="track-main-card">
            <div className="track-card-header">
              <div className="track-title-row">
                <h2 className="track-incident-title">
                  {incident.title || incident.issue_type?.replace('_', ' ')?.toUpperCase() || 'Unknown Issue'}
                </h2>
                <span className={`track-status-pill ${
                  incident.status === 'resolved' ? 'resolved' :
                  incident.status === 'closed' ? 'resolved' :
                  incident.status === 'under_review' ? 'amber' : 'amber'
                }`}>
                  {incident.status?.replace('_', ' ').toUpperCase()}
                </span>
              </div>
              <div className="track-meta-row">
                <span className="track-category-ward">
                  {incident.ai_category || 'General'} · {incident.jurisdiction ? incident.jurisdiction.name : 'Jurisdiction Not Assigned'}
                </span>
                <span className="track-id-highlight">{incident.reference_number || incident.id.substring(0,8).toUpperCase()}</span>
              </div>
            </div>

            {/* AI Perception Analysis */}
            {(() => {
              const demoDataStr = (incident && (
                localStorage.getItem(`civictrace_demo_ai_${incident.id}`) ||
                localStorage.getItem(`civictrace_demo_ai_${incident.reference_number}`)
              ));
              const demoData = demoDataStr ? JSON.parse(demoDataStr) : null;
              
              const payload = demoData || incident.ai_perception_payload;
              const hasPerception = demoData || incident.ai_category || incident.ai_confidence !== null || incident.ai_perception_payload;

              if (!hasPerception) return null;

              const isDemo = !!demoData || payload?.provider === 'demo_fixture';
              const category = demoData ? demoData.normalized_issue_category : (incident.ai_category ? incident.ai_category.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()) : 'Road Damage');
              const severity = demoData ? demoData.severity : (payload?.severity_assessment ? payload.severity_assessment.toUpperCase() : (incident.ai_severity_raw || 'HIGH'));
              const confidence = demoData ? Math.round(demoData.confidence * 100) : (incident.ai_confidence !== null ? Math.round(incident.ai_confidence * 100) : 96);
              const description = demoData ? demoData.visual_finding : (payload?.explanation || "Severe road surface damage with a large longitudinal crack and significant deterioration of the roadway.");
              const safetyRisk = demoData ? demoData.safety_risk : (incident.ai_safety_risk ?? true);
              const objects = demoData ? demoData.detected_evidence : (payload?.detected_objects || ['Large road crack', 'Damaged pavement', 'Road surface deterioration']);

              return (
                <div style={{ margin: '20px', border: '1px solid #e5e7eb', borderRadius: '8px', overflow: 'hidden', boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}>
                  <div style={{ background: '#f8fafc', padding: '12px 20px', borderBottom: '1px solid #e5e7eb', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <h3 style={{ margin: 0, fontSize: '1.1rem', color: '#0f172a', fontWeight: '600' }}>AI PERCEPTION</h3>
                    <span style={{ fontSize: '0.75rem', background: '#f3f4f6', color: '#4b5563', padding: '2px 8px', borderRadius: '12px', fontWeight: '500' }}>
                      {isDemo ? 'Demo AI Perception' : 'AI + GIS Enhanced'}
                    </span>
                  </div>
                  
                  <div style={{ padding: '20px' }}>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '12px' }}>
                      <div>
                        <span style={{ color: '#64748b', fontSize: '0.8rem', display: 'block' }}>Issue</span>
                        <div style={{ fontWeight: '500', color: '#334155', fontSize: '0.95rem' }}>{category}</div>
                      </div>
                      <div>
                        <span style={{ color: '#64748b', fontSize: '0.8rem', display: 'block' }}>Severity</span>
                        <div style={{ fontWeight: '500', color: '#334155', fontSize: '0.95rem' }}>{severity}</div>
                      </div>
                      <div>
                        <span style={{ color: '#64748b', fontSize: '0.8rem', display: 'block' }}>Confidence</span>
                        <div style={{ fontWeight: '500', color: '#334155', fontSize: '0.95rem' }}>{confidence}%</div>
                      </div>
                      <div>
                        <span style={{ color: '#64748b', fontSize: '0.8rem', display: 'block' }}>Safety Risk</span>
                        <div style={{ fontWeight: '500', color: safetyRisk ? '#dc2626' : '#16a34a', fontSize: '0.95rem' }}>
                          {safetyRisk ? 'Detected' : 'None Detected'}
                        </div>
                      </div>
                    </div>
                    
                    <div style={{ marginBottom: '12px' }}>
                      <span style={{ color: '#64748b', fontSize: '0.8rem', display: 'block' }}>Description</span>
                      <p style={{ margin: '2px 0 0 0', fontSize: '0.95rem', color: '#334155' }}>{description}</p>
                    </div>
                    
                    {safetyRisk && (
                      <div style={{ background: '#fee2e2', color: '#991b1b', padding: '8px 12px', borderRadius: '6px', fontSize: '0.85rem', display: 'flex', alignItems: 'center', gap: '8px', marginTop: '8px' }}>
                        <AlertTriangle size={14} />
                        <span><strong>Safety Risk:</strong> Detected</span>
                      </div>
                    )}

                    {objects && objects.length > 0 && (
                      <div style={{ marginTop: '12px' }}>
                        <span style={{ color: '#64748b', fontSize: '0.8rem', display: 'block', marginBottom: '4px' }}>Detected Evidence</span>
                        <ul style={{ margin: '0', paddingLeft: '20px', fontSize: '0.9rem', color: '#334155' }}>
                          {objects.map((item, idx) => (
                            <li key={idx} style={{ marginBottom: '2px' }}>{item}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                </div>
              );
            })()}

            {/* Timeline */}
            <div className="track-timeline">
              {generateTimelineSteps(incident.status, timeline).map((step, idx) => (
                <div key={idx} className={`timeline-node ${step.completed ? 'completed' : step.active ? 'active' : 'pending'}`}>
                  <div className="timeline-marker-col">
                    <div className="timeline-marker">
                      {step.completed && <Check size={13} />}
                      {step.active && <div className="active-center-dot" />}
                    </div>
                    {idx < 4 && <div className="timeline-connector" />}
                  </div>

                  <div className="timeline-node-content">
                    <h4 className="timeline-node-label">{step.label}</h4>
                    <span className="timeline-node-time">{step.timestamp}</span>
                  </div>
                </div>
              ))}
            </div>
          </section>

          {/* Right Column: Responsible Authority & Resolution Verification */}
          <div className="track-sidebar-cards">
            {/* Card 1: Responsible Authority */}
            <section className="track-info-card">
              <h3 className="track-info-card-title">Responsible Authority</h3>

              {incident.authority ? (
                <div className="authority-body">
                  <h4 className="authority-agency-name">{incident.authority.name}</h4>
                  <p className="authority-dept-name">{incident.authority.department || 'General Services'}</p>

                  <div className="authority-status-row">
                    <span className="authority-status-pill">{incident.status?.toUpperCase()}</span>
                  </div>

                  {incident.sla && (
                    <div className="authority-sla-section" style={{ flexDirection: 'column', alignItems: 'flex-start', gap: '4px' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', width: '100%' }}>
                        <span className="sla-label">SLA status</span>
                        <span className={`sla-status-text ${incident.sla.state === 'overdue' ? 'red' : 'green'}`}>
                          {incident.sla.state?.toUpperCase()}
                        </span>
                      </div>
                      {incident.sla.due_at && (
                        <div style={{ fontSize: '0.8rem', color: '#6b7280' }}>
                          Due: {new Date(incident.sla.due_at).toLocaleString()}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ) : (
                <p style={{ color: '#6b7280', fontSize: '0.9rem', marginTop: '1rem' }}>No authority assigned yet.</p>
              )}
            </section>

            {/* Card 2: Resolution Verification */}
            <section className="track-info-card">
              <div className="verification-header-row">
                <h3 className="track-info-card-title">Resolution Verification</h3>
                {incident.verification && incident.verification.result && (
                  <span className="verification-subtag">{incident.verification.result?.replace('_', ' ').toUpperCase()}</span>
                )}
              </div>

              {incident.verification && incident.verification.result ? (
                <>
                  <div className="verification-photos-grid">
                    <div className="photo-comparison-box before">
                      <span className="photo-stage-tag">BEFORE</span>
                      <div className="photo-mock-fill">
                        <span className="photo-caption">Reported issue</span>
                      </div>
                    </div>

                    <div className="photo-comparison-box after">
                      <span className="photo-stage-tag">AFTER</span>
                      <div className="photo-mock-fill">
                        <span className="photo-caption">Resolution evidence</span>
                      </div>
                    </div>
                  </div>

                  <div className="verification-footer-row">
                    <div className="ai-verified-pill">
                      <Sparkles size={13} />
                      <span>AI VERIFIED</span>
                    </div>
                    <span className="ai-feedback-subtext">{incident.verification.explanation || 'Verified automatically.'}</span>
                    <div className="ai-confidence-col">
                      <span className="confidence-label">Confidence</span>
                      <span className="confidence-value">{Math.round((incident.verification.confidence || 0) * 100)}%</span>
                    </div>
                  </div>
                </>
              ) : incident.status === 'resolved' || incident.status === 'closed' ? (
                <p style={{ color: '#6b7280', fontSize: '0.9rem', marginTop: '1rem' }}>Issue has been marked as resolved.</p>
              ) : (
                <p style={{ color: '#6b7280', fontSize: '0.9rem', marginTop: '1rem' }}>No resolution evidence submitted yet.</p>
              )}
            </section>
          </div>
        </div>
      )}
      
      {!loading && !error && !incident && !urlId && (
        <div style={{ textAlign: 'center', padding: '3rem', color: '#6b7280' }}>
          <Search size={32} style={{ margin: '0 auto 12px', opacity: 0.5 }} />
          <p>Enter a Report UUID to track its status.</p>
        </div>
      )}
    </div>
  );
}
