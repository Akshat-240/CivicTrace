import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { mockIncidentDetailCT1842 } from '../../data/mockData';
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

  const incident = mockIncidentDetailCT1842;

  const tabs = [
    'Overview',
    'Location & Map',
    'Evidence (3)',
    'AI Analysis',
    'Duplicates (2)',
    'SLA & Rules',
    'Audit Log'
  ];

  const handleRouting = () => {
    setRoutingSuccess(true);
    setTimeout(() => setRoutingSuccess(false), 3000);
  };

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
              <span className="ct-badge-pill badge-red font-bold">HIGH PRIORITY</span>
            </div>

            <h1 className="ct-detail-title">{incident.title}</h1>
            <p className="ct-detail-subtitle">{incident.subtitle}</p>

            <div className="ct-detail-context-row">
              <span className="ct-detail-loc">
                <MapPin size={14} />
                {incident.location}
              </span>
              <span className="ct-detail-dot">•</span>
              <span className="ct-detail-time">
                <Clock size={14} />
                {incident.reportedTime}
              </span>
            </div>
          </div>

          <div className="ct-detail-status-col">
            <div className="ct-status-field">
              <span className="ct-field-label">Status</span>
              <span className="ct-badge-pill badge-status-blue">{incident.status}</span>
            </div>
            <div className="ct-status-field">
              <span className="ct-field-label">Priority</span>
              <span className="ct-badge-pill badge-amber">{incident.priority}</span>
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
              {incident.description}
            </p>
          </div>

          {/* Evidence Card */}
          <div className="ct-detail-card">
            <h2 className="ct-card-heading">Evidence (3)</h2>
            <div className="ct-evidence-thumbnails-row">
              <div className="ct-evidence-thumb">
                <div className="ct-thumb-placeholder primary">
                  <span>REPORTED PHOTO</span>
                </div>
              </div>
              <div className="ct-evidence-thumb">
                <div className="ct-thumb-placeholder secondary">
                  <span>ANGLE 2</span>
                </div>
              </div>
              <div className="ct-evidence-thumb">
                <div className="ct-thumb-placeholder more">
                  <span>+2</span>
                </div>
              </div>
            </div>
            <div className="ct-evidence-footer-text">
              Reported image • {incident.reportedDate}
            </div>
          </div>

          {/* Duplicate / Related Incidents */}
          <div className="ct-detail-card">
            <h2 className="ct-card-heading">Duplicate / Related Incidents</h2>
            <div className="ct-duplicates-list">
              {incident.duplicates.map((dup) => (
                <div key={dup.id} className="ct-dup-row">
                  <div className="ct-dup-left">
                    <span className="ct-dup-id">{dup.id}</span>
                    <span className="ct-dup-match">{dup.match}</span>
                  </div>
                  <span className={`ct-badge-pill ${dup.status === 'Merged' ? 'badge-status-green' : 'badge-status-blue'}`}>
                    {dup.status}
                  </span>
                </div>
              ))}
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
                <div className="ct-map-location-name">Faizabad Road</div>
                <div className="ct-map-ward-name">LUCKNOW • WARD 12</div>
              </div>
            </div>
            <div className="ct-map-coords-row">
              <span>Lat {incident.coordinates.lat}</span>
              <span>Long {incident.coordinates.long}</span>
              <span>{incident.coordinates.zone}</span>
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
                AI Resolution Check • 92%
              </span>
            </div>

            <div className="ct-ai-metrics-row">
              <div className="ct-ai-col">
                <span className="ct-ai-label">Detected Issue</span>
                <span className="ct-ai-val font-bold">{incident.aiAnalysis.detectedIssue}</span>
              </div>
              <div className="ct-ai-col">
                <span className="ct-ai-label">Severity</span>
                <span className="ct-badge-pill badge-red">{incident.aiAnalysis.severity}</span>
              </div>
              <div className="ct-ai-col">
                <span className="ct-ai-label">Confidence</span>
                <span className="ct-badge-pill badge-status-green">{incident.aiAnalysis.confidence}</span>
              </div>
            </div>

            <div className="ct-ai-objects-detected">
              Objects: {incident.aiAnalysis.objects}
            </div>

            <div className="ct-ai-summary-box">
              {incident.aiAnalysis.summary}
            </div>
          </div>

          {/* Responsible Authority */}
          <div className="ct-detail-card">
            <h2 className="ct-card-heading">Responsible Authority</h2>
            <div className="ct-authority-row">
              <div className="ct-dept-badge">RD</div>
              <div className="ct-authority-details">
                <div className="ct-auth-dept">{incident.responsibleAuthority.department}</div>
                <div className="ct-auth-org">{incident.responsibleAuthority.org}</div>
              </div>
            </div>

            <div className="ct-officer-meta">
              <div className="ct-officer-row">
                <span className="ct-officer-label">Nodal Officer:</span>
                <span className="ct-officer-name">{incident.responsibleAuthority.nodalOfficer}</span>
              </div>
              <div className="ct-officer-row">
                <span className="ct-officer-label">Phone:</span>
                <span className="ct-officer-val">{incident.responsibleAuthority.phone}</span>
              </div>
              <div className="ct-officer-row">
                <span className="ct-officer-label">Email:</span>
                <span className="ct-officer-val">{incident.responsibleAuthority.email}</span>
              </div>
            </div>
          </div>

          {/* Audit Timeline */}
          <div className="ct-detail-card">
            <h2 className="ct-card-heading">Audit Timeline</h2>
            <div className="ct-timeline-list">
              {incident.auditTimeline.map((item, idx) => (
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
