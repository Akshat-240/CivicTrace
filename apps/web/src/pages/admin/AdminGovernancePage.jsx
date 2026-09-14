import React, { useState } from 'react';
import { mockAdminGovernance } from '../../data/mockData';
import { 
  ShieldCheck, 
  AlertCircle, 
  HelpCircle, 
  CheckCircle2, 
  FileText, 
  ArrowRight,
  Shield,
  Eye
} from 'lucide-react';
import './AdminGovernancePage.css';

const AdminGovernancePage = () => {
  const [selectedCase, setSelectedCase] = useState(mockAdminGovernance.queue[0]);
  const [resolutionAction, setResolutionAction] = useState(null);

  const handleAction = (actionName) => {
    setResolutionAction(actionName);
    setTimeout(() => setResolutionAction(null), 3500);
  };

  return (
    <div className="ct-admin-gov-page">
      {/* Ground-Truth Assessment Banner */}
      <div className="ct-ground-truth-banner">
        <div className="ct-banner-text-col">
          <div className="ct-banner-title">
            <ShieldCheck size={18} className="ct-shield-icon" />
            <span>GROUND-TRUTH ASSESSMENT</span>
          </div>
          <p className="ct-banner-sub">
            Actual backend resolution states — these are system states, not UI labels.
          </p>
        </div>

        <div className="ct-ground-truth-badges">
          {mockAdminGovernance.assessmentStates.map((st) => (
            <span 
              key={st.code} 
              className="ct-gt-badge"
              style={{ borderColor: st.color, color: st.color }}
              title={st.label}
            >
              {st.code}
            </span>
          ))}
        </div>
      </div>

      {resolutionAction && (
        <div className="ct-gov-alert-banner">
          <CheckCircle2 size={18} />
          <span>Action "{resolutionAction}" logged in immutable administrative audit trail for {selectedCase.id}.</span>
        </div>
      )}

      {/* Main Grid */}
      <div className="ct-gov-main-grid">
        {/* Left Column: Human Review Queue */}
        <div className="ct-gov-card">
          <div className="ct-gov-card-head">
            <h2 className="ct-gov-title">Human Review Queue</h2>
            <p className="ct-gov-subtitle">
              Cases that cannot be safely resolved by automated routing or evidence checks.
            </p>
          </div>

          {/* Conflict category cards */}
          <div className="ct-gov-conflicts-list">
            {mockAdminGovernance.queue.map((item) => {
              const isSelected = selectedCase?.id === item.id;
              let dotColor = '#F97316';
              if (item.category === 'Evidence conflict') dotColor = '#EF4444';

              return (
                <div 
                  key={item.id}
                  className={`ct-conflict-item ${isSelected ? 'active-case' : ''}`}
                  onClick={() => setSelectedCase(item)}
                >
                  <span className="ct-conflict-dot" style={{ backgroundColor: dotColor }}></span>
                  <div className="ct-conflict-text">
                    <div className="ct-conflict-title-row">
                      <span className="ct-conflict-name">{item.title}</span>
                      <span className="ct-conflict-case-id">{item.id}</span>
                    </div>
                    <p className="ct-conflict-desc">{item.desc}</p>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Interactive Example Action Box */}
          <div className="ct-gov-example-box">
            <div className="ct-example-header">
              <span className="ct-example-tag">ACTIVE CASE TRIAGE</span>
              <h3 className="ct-example-id">{selectedCase.id}</h3>
            </div>

            <div className="ct-example-reason-row">
              <span className="ct-reason-label">Reason for Review:</span>
              <span className="ct-reason-text">{selectedCase.reason}</span>
            </div>

            <div className="ct-example-actions-row">
              <span className="ct-actions-label">Actions:</span>
              <div className="ct-action-buttons-group">
                <button 
                  type="button" 
                  className="ct-gov-btn-link"
                  onClick={() => handleAction('Review Evidence')}
                >
                  <Eye size={14} />
                  <span>Review Evidence</span>
                </button>
                <button 
                  type="button" 
                  className="ct-gov-btn-action primary"
                  onClick={() => handleAction('Confirm Responsibility to Roads Dept')}
                >
                  Confirm Responsibility
                </button>
                <button 
                  type="button" 
                  className="ct-gov-btn-action secondary"
                  onClick={() => handleAction('Request Clarification from Sub-divisional Officer')}
                >
                  Request Clarification
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Why Human Review & Policies */}
        <div className="ct-gov-side-rail">
          <div className="ct-gov-card">
            <h2 className="ct-gov-title">Why Human Review?</h2>
            <h3 className="ct-gov-strong-title">The system doesn't guess.</h3>
            <p className="ct-gov-policy-text">
              Ambiguous jurisdiction, location or evidence is surfaced for explicit human review.
            </p>

            {/* Review Trigger Box */}
            <div className="ct-review-trigger-box">
              <span className="ct-box-sub-label">REVIEW TRIGGER</span>
              <h4 className="ct-trigger-title">{selectedCase.category}</h4>
              <p className="ct-trigger-desc">
                No automatic department assignment is made without verification.
              </p>
            </div>

            {/* Review Outcome Box */}
            <div className="ct-review-outcome-box">
              <span className="ct-box-sub-label">REVIEW OUTCOME</span>
              <h4 className="ct-outcome-title">Human reviewer decides</h4>
              <ul className="ct-outcome-list">
                <li>• Confirm responsibility</li>
                <li>• Request clarification</li>
                <li>• Keep incident open</li>
              </ul>
            </div>

            {/* Audit Trail Note */}
            <div className="ct-audit-trail-footer">
              <div className="ct-audit-label">Audit trail</div>
              <p className="ct-audit-desc">
                Every review decision is recorded for accountability.
              </p>
              <div className="ct-audit-pledge">
                No silent routing • No silent closure
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdminGovernancePage;
