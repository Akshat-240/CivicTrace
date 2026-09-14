import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getIncident, getIncidentEvidence, getIncidentTimeline } from '../../services/api';
import {
  ArrowLeft,
  MapPin,
  Clock,
  CheckCircle2,
  AlertTriangle,
  ExternalLink,
  Bot,
  User,
  Shield,
  Layers,
  Sparkles
} from 'lucide-react';
import './AdminIncidentDetailPage.css';

const AdminIncidentDetailPage = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('Overview');
  const [routingSuccess, setRoutingSuccess] = useState(false);

  const [incident, setIncident] = useState(null);
  const [evidence, setEvidence] = useState([]);
  const [timeline, setTimeline] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchDetails = async () => {
      try {
        setLoading(true);
        const [inc, ev, time] = await Promise.all([
          getIncident(id),
          getIncidentEvidence(id).catch(() => []),
          getIncidentTimeline(id).catch(() => [])
        ]);
        setIncident(inc);
        setEvidence(ev || []);
        setTimeline(time || []);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };
    fetchDetails();
  }, [id]);

  const handleRouting = () => {
    setRoutingSuccess(true);
    setTimeout(() => setRoutingSuccess(false), 3000);
  };

  if (loading) return <div style={{ padding: '2rem', textAlign: 'center' }}>Loading incident details...</div>;
  if (error) return <div style={{ padding: '2rem', textAlign: 'center', color: 'red' }}>Error: {error}</div>;
  if (!incident) return <div style={{ padding: '2rem', textAlign: 'center' }}>Incident not found</div>;

  const reportedTime = incident.created_at ? new Date(incident.created_at).toLocaleString() : 'N/A';
  const reportedDate = incident.created_at ? new Date(incident.created_at).toLocaleDateString() : 'N/A';
  const duplicates = incident.duplicates || [];
  const coords = {
    lat: incident.latitude || '0.00',
    long: incident.longitude || '0.00',
    zone: incident.ward ? `Ward ${incident.ward}` : 'Unknown Zone'
  };
  const aiAnalysis = incident.ai_analysis || {
    detectedIssue: incident.description || 'Unknown',
    severity: incident.priority || 'Medium',
    confidence: 'N/A',
    objects: 'N/A',
    summary: 'AI analysis not available.'
  };
  const responsibleAuthority = incident.authority || {
    department: incident.category || 'General',
    org: 'Municipal Corporation',
    nodalOfficer: 'Unassigned',
    phone: 'N/A',
    email: 'N/A'
  };
  const auditTimeline = timeline.length > 0 ? timeline.map(t => ({
    event: t.action || 'Updated',
    time: t.timestamp ? new Date(t.timestamp).toLocaleString() : 'N/A'
  })) : [{ event: 'Incident Reported', time: reportedTime }];

  const tabs = [
    'Overview',
    'Location & Map',
    `Evidence (${evidence.length})`,
    'AI Analysis',
    `Duplicates (${duplicates.length})`,
    'SLA & Rules',
    'Audit Log'
  ];

  return (
    <div className="ct-admin-detail-page">
      {/* Breadcrumb navigation */}
      <div className="ct-detail-breadcrumb">
        <button
          type="button"
          className="ct-back-breadcrumb-btn"
          onClick={() => navigate('/admin/incidents')}
        >
          <ArrowLeft size={16} />
          <span>Incidents</span>
        </button>
        <span className="ct-breadcrumb-slash">/</span>
        <span className="ct-breadcrumb-current">{incident.id}</span>
      </div>

      {routingSuccess && (
        <div className="ct-alert-success">
          <CheckCircle2 size={18} />
          <span>Routing decision confirmed and notified to Rohit Rai (Roads Department).</span>
        </div>
      )}

      {/* Main Banner Header Card */}
      <div className="ct-detail-header-card">
        <div className="ct-detail-header-main">
          {/* Road image placeholder preview */}
          <div className="ct-detail-image-box">
            <div className="ct-detail-image-label">ROAD IMAGE</div>
          </div>

          <div className="ct-detail-header-meta">
            <div className="ct-detail-id-row">
              <span className="ct-detail-id-text">{incident.id}</span>
              <span className="ct-badge-pill badge-red font-bold">{(incident.priority || 'Medium').toUpperCase()}</span>
            </div>

            <h1 className="ct-detail-title">{incident.description || 'No description provided'}</h1>
            <p className="ct-detail-subtitle">{incident.category || 'General Issue'}</p>

            <div className="ct-detail-context-row">
              <span className="ct-detail-loc">
                <MapPin size={14} />
                {incident.location_name || 'Unknown Location'}
              </span>
              <span className="ct-detail-dot">•</span>
              <span className="ct-detail-time">
                <Clock size={14} />
                {reportedTime}
              </span>
            </div>
          </div>

          <div className="ct-detail-status-col">
            <div className="ct-status-field">
              <span className="ct-field-label">Status</span>
              <span className="ct-badge-pill badge-status-blue">{incident.status || 'Reported'}</span>
            </div>
            <div className="ct-status-field">
              <span className="ct-field-label">Priority</span>
              <span className="ct-badge-pill badge-amber">{incident.priority || 'Medium'}</span>
            </div>
          </div>

          <div className="ct-detail-header-actions">
            <button
              type="button"
              className="ct-btn-routing"
              onClick={handleRouting}
            >
              Routing Decision
            </button>
            <button
              type="button"
              className="ct-btn-flag"
              onClick={() => alert("Flagged for Municipal Governance Oversight")}
            >
              Flag / Escalate
            </button>
          </div>
        </div>

        {/* Tab navigation */}
        <div className="ct-detail-tabs-bar">
          {tabs.map((tab) => (
            <button
              key={tab}
              type="button"
              className={`ct-detail-tab-btn ${activeTab === tab ? 'active' : ''}`}
              onClick={() => setActiveTab(tab)}
            >
              {tab}
            </button>
          ))}
        </div>
      </div>

      {/* Tab Content Grid */}
      <div className="ct-detail-grid">
        {/* Left Column */}
        <div className="ct-detail-left-col">
          {/* Description Card */}
          <div className="ct-detail-card">
            <h2 className="ct-card-heading">Description</h2>
            <p className="ct-detail-desc-text">
              {incident.description || 'No further description available.'}
            </p>
          </div>

          {/* Evidence Card */}
          <div className="ct-detail-card">
            <h2 className="ct-card-heading">Evidence ({evidence.length})</h2>
            <div className="ct-evidence-thumbnails-row">
              {evidence.slice(0, 3).map((ev, idx) => (
                <div className="ct-evidence-thumb" key={idx}>
                  {ev.media_url ? (
                    <img src={ev.media_url} alt="Evidence" style={{width: '100%', height: '100%', objectFit: 'cover', borderRadius: '4px'}} />
                  ) : (
                    <div className={`ct-thumb-placeholder ${idx === 0 ? 'primary' : 'secondary'}`}>
                      <span>{idx === 0 ? 'REPORTED PHOTO' : `ANGLE ${idx + 1}`}</span>
                    </div>
                  )}
                </div>
              ))}
              {evidence.length === 0 && (
                <div style={{ color: '#888' }}>No evidence provided.</div>
              )}
            </div>
            {evidence.length > 0 && (
              <div className="ct-evidence-footer-text">
                Reported image • {reportedDate}
              </div>
            )}
          </div>

          {/* Duplicate / Related Incidents */}
          <div className="ct-detail-card">
            <h2 className="ct-card-heading">Duplicate / Related Incidents</h2>
            <div className="ct-duplicates-list">
              {duplicates.map((dup, idx) => (
                <div key={idx} className="ct-dup-row">
                  <div className="ct-dup-left">
                    <span className="ct-dup-id">{dup.id}</span>
                    <span className="ct-dup-match">{dup.match || 'High Match'}</span>
                  </div>
                  <span className={`ct-badge-pill ${dup.status === 'Merged' ? 'badge-status-green' : 'badge-status-blue'}`}>
                    {dup.status || 'Potential'}
                  </span>
                </div>
              ))}
              {duplicates.length === 0 && (
                <div style={{ color: '#888' }}>No duplicates found.</div>
              )}
            </div>
          </div>
        </div>

        {/* Right Column */}
        <div className="ct-detail-right-col">
          {/* Location & Map Card */}
          <div className="ct-detail-card">
            <h2 className="ct-card-heading">Location & Map</h2>
            <div className="ct-detail-map-box">
              <div className="ct-detail-map-overlay">
                <div className="ct-map-pin-circle">
                  <MapPin size={18} />
                </div>
                <div className="ct-map-location-name">{incident.location_name || 'Unknown Location'}</div>
                <div className="ct-map-ward-name">LUCKNOW • {coords.zone}</div>
              </div>
            </div>
            <div className="ct-map-coords-row">
              <span>Lat {coords.lat}</span>
              <span>Long {coords.long}</span>
              <span>{coords.zone}</span>
            </div>
          </div>

          {/* AI Analysis Card */}
          <div className="ct-detail-card ct-ai-card">
            <div className="ct-ai-card-header">
              <h2 className="ct-card-heading">
                <Sparkles size={16} className="ct-ai-icon" />
                AI Analysis
              </h2>
              <span className="ct-badge-pill badge-status-green font-bold">
                AI Check • {aiAnalysis.confidence}
              </span>
            </div>

            <div className="ct-ai-metrics-row">
              <div className="ct-ai-col">
                <span className="ct-ai-label">Detected Issue</span>
                <span className="ct-ai-val font-bold">{aiAnalysis.detectedIssue}</span>
              </div>
              <div className="ct-ai-col">
                <span className="ct-ai-label">Severity</span>
                <span className="ct-badge-pill badge-red">{aiAnalysis.severity}</span>
              </div>
              <div className="ct-ai-col">
                <span className="ct-ai-label">Confidence</span>
                <span className="ct-badge-pill badge-status-green">{aiAnalysis.confidence}</span>
              </div>
            </div>

            <div className="ct-ai-objects-detected">
              Objects: {aiAnalysis.objects}
            </div>

            <div className="ct-ai-summary-box">
              {aiAnalysis.summary}
            </div>
          </div>

          {/* Responsible Authority */}
          <div className="ct-detail-card">
            <h2 className="ct-card-heading">Responsible Authority</h2>
            <div className="ct-authority-row">
              <div className="ct-dept-badge">{responsibleAuthority.department.substring(0, 2).toUpperCase()}</div>
              <div className="ct-authority-details">
                <div className="ct-auth-dept">{responsibleAuthority.department}</div>
                <div className="ct-auth-org">{responsibleAuthority.org}</div>
              </div>
            </div>

            <div className="ct-officer-meta">
              <div className="ct-officer-row">
                <span className="ct-officer-label">Nodal Officer:</span>
                <span className="ct-officer-name">{responsibleAuthority.nodalOfficer}</span>
              </div>
              <div className="ct-officer-row">
                <span className="ct-officer-label">Phone:</span>
                <span className="ct-officer-val">{responsibleAuthority.phone}</span>
              </div>
              <div className="ct-officer-row">
                <span className="ct-officer-label">Email:</span>
                <span className="ct-officer-val">{responsibleAuthority.email}</span>
              </div>
            </div>
          </div>

          {/* Audit Timeline */}
          <div className="ct-detail-card">
            <h2 className="ct-card-heading">Audit Timeline</h2>
            <div className="ct-timeline-list">
              {auditTimeline.map((item, idx) => (
                <div key={idx} className="ct-timeline-item">
                  <span className="ct-timeline-dot"></span>
                  <div className="ct-timeline-content">
                    <span className="ct-timeline-event">{item.event}</span>
                    <span className="ct-timeline-time">{item.time}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdminIncidentDetailPage;
