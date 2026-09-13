import React, { useState } from 'react';
import { 
  Search, 
  Check, 
  Clock, 
  ShieldCheck, 
  CheckCircle2, 
  MapPin, 
  Building2, 
  Sparkles 
} from 'lucide-react';
import { mockCitizenTrackingData } from '../../data/mockData';
import './CitizenTrackPage.css';

export default function CitizenTrackPage() {
  const [searchId, setSearchId] = useState('CT-INC-024');
  const [data, setData] = useState(mockCitizenTrackingData);

  const handleSearch = (e) => {
    e.preventDefault();
    if (searchId.trim()) {
      // In a real app we would fetch by searchId
      setData({ ...mockCitizenTrackingData, id: searchId.toUpperCase() });
    }
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
            placeholder="e.g. CT-INC-024"
          />
        </div>
        <button type="submit" className="btn-track-search">
          <Search size={15} />
          <span>Search</span>
        </button>
      </form>

      {/* Main 2-Column Grid */}
      <div className="citizen-track-grid">
        {/* Left Column: Lifecycle & Timeline */}
        <section className="track-main-card">
          <div className="track-card-header">
            <div className="track-title-row">
              <h2 className="track-incident-title">{data.title}</h2>
              <span className="track-status-pill amber">{data.status}</span>
            </div>
            <div className="track-meta-row">
              <span className="track-category-ward">{data.category} · {data.ward}</span>
              <span className="track-id-highlight">{data.id}</span>
            </div>
          </div>

          {/* 6-Stage Timeline */}
          <div className="track-timeline">
            {data.timeline.map((step, idx) => (
              <div key={idx} className={`timeline-node ${step.completed ? 'completed' : step.active ? 'active' : 'pending'}`}>
                <div className="timeline-marker-col">
                  <div className="timeline-marker">
                    {step.completed && <Check size={13} />}
                    {step.active && <div className="active-center-dot" />}
                  </div>
                  {idx < data.timeline.length - 1 && <div className="timeline-connector" />}
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

            <div className="authority-body">
              <h4 className="authority-agency-name">{data.authority.agency}</h4>
              <p className="authority-dept-name">{data.authority.department}</p>

              <div className="authority-status-row">
                <span className="authority-status-pill">{data.authority.status}</span>
              </div>

              <div className="authority-sla-section">
                <span className="sla-label">SLA status</span>
                <span className="sla-status-text green">{data.authority.slaStatus}</span>
              </div>
            </div>
          </section>

          {/* Card 2: Resolution Verification */}
          <section className="track-info-card">
            <div className="verification-header-row">
              <h3 className="track-info-card-title">Resolution Verification</h3>
              <span className="verification-subtag">{data.verification.comparison}</span>
            </div>

            <div className="verification-photos-grid">
              <div className="photo-comparison-box before">
                <span className="photo-stage-tag">BEFORE</span>
                <div className="photo-mock-fill">
                  <span className="photo-caption">{data.verification.beforeLabel}</span>
                </div>
              </div>

              <div className="photo-comparison-box after">
                <span className="photo-stage-tag">AFTER</span>
                <div className="photo-mock-fill">
                  <span className="photo-caption">{data.verification.afterLabel}</span>
                </div>
              </div>
            </div>

            <div className="verification-footer-row">
              <div className="ai-verified-pill">
                <Sparkles size={13} />
                <span>AI VERIFIED</span>
              </div>
              <span className="ai-feedback-subtext">{data.verification.message}</span>
              <div className="ai-confidence-col">
                <span className="confidence-label">Confidence</span>
                <span className="confidence-value">{data.verification.confidence}</span>
              </div>
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}
