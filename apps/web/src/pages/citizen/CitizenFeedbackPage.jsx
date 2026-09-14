import React, { useState } from 'react';
import { Star, CheckCircle, ArrowRight } from 'lucide-react';
import { mockCitizenFeedbackTarget } from '../../data/mockData';
import './CitizenFeedbackPage.css';

export default function CitizenFeedbackPage() {
  const [resolutionStatus, setResolutionStatus] = useState('Completely resolved');
  const [rating, setRating] = useState(4);
  const [feedbackText, setFeedbackText] = useState('');
  const [submitted, setSubmitted] = useState(false);

  const options = [
    {
      title: 'Completely resolved',
      desc: 'The reported issue is fully fixed',
      val: 'Completely resolved'
    },
    {
      title: 'Partially resolved',
      desc: 'Some part of the issue remains',
      val: 'Partially resolved'
    },
    {
      title: 'Not resolved',
      desc: 'The issue is still present',
      val: 'Not resolved'
    }
  ];

  const handleSubmit = (e) => {
    e.preventDefault();
    setSubmitted(true);
  };

  return (
    <div className="citizen-feedback-container">
      {submitted ? (
        <div className="feedback-thankyou-card">
          <div className="thankyou-icon">
            <CheckCircle size={44} />
          </div>
          <h2 className="thankyou-title">Thank You for Your Feedback!</h2>
          <p className="thankyou-desc">
            Your verification for <strong>{mockCitizenFeedbackTarget.id}</strong> has been logged in the CivicTrace governance ledger and factored into the authority's SLA score.
          </p>
          <button
            type="button"
            className="btn-feedback-done"
            onClick={() => setSubmitted(false)}
          >
            Update Feedback Response
          </button>
        </div>
      ) : (
        <div className="citizen-feedback-grid">
          {/* Main Feedback Form */}
          <form className="feedback-form-panel" onSubmit={handleSubmit}>
            <div className="feedback-form-header">
              <h2 className="feedback-question">Was this issue actually resolved?</h2>
              <p className="feedback-target-incident">
                {mockCitizenFeedbackTarget.id} · {mockCitizenFeedbackTarget.title}
              </p>
            </div>

            {/* 3 Resolution Option Cards */}
            <div className="resolution-options-list">
              {options.map((opt) => (
                <label
                  key={opt.val}
                  className={`resolution-option-card ${resolutionStatus === opt.val ? 'selected' : ''}`}
                  onClick={() => setResolutionStatus(opt.val)}
                >
                  <div className="option-radio-indicator">
                    {resolutionStatus === opt.val && <div className="radio-dot" />}
                  </div>

                  <div className="option-content">
                    <span className="option-title">{opt.title}</span>
                    <span className="option-desc">{opt.desc}</span>
                  </div>
                </label>
              ))}
            </div>

            {/* Star Rating */}
            <div className="feedback-rating-section">
              <label className="rating-label">Rate your experience</label>
              <div className="stars-row">
                {[1, 2, 3, 4, 5].map((star) => (
                  <button
                    key={star}
                    type="button"
                    className={`star-btn ${rating >= star ? 'filled' : ''}`}
                    onClick={() => setRating(star)}
                  >
                    <Star size={22} />
                  </button>
                ))}
              </div>
            </div>

            {/* Optional Comment */}
            <div className="feedback-comment-section">
              <label className="comment-label">Tell us more (optional)</label>
              <textarea
                className="feedback-textarea"
                rows={3}
                placeholder="Share anything that could help us improve..."
                value={feedbackText}
                onChange={(e) => setFeedbackText(e.target.value)}
              />
            </div>

            <button type="submit" className="btn-submit-feedback">
              Submit Feedback
            </button>
          </form>

          {/* Side Card: CivicTrace Feedback Loop */}
          <div className="feedback-loop-card">
            <h3 className="loop-card-title">CivicTrace feedback loop</h3>

            <div className="loop-steps-list">
              <div className="loop-step-item">
                <div className="loop-num-badge">1</div>
                <div className="loop-text-col">
                  <h4 className="loop-step-heading">Authority says resolved</h4>
                  <p className="loop-step-body">Resolution evidence submitted</p>
                </div>
              </div>

              <div className="loop-step-item">
                <div className="loop-num-badge">2</div>
                <div className="loop-text-col">
                  <h4 className="loop-step-heading">CivicTrace verifies</h4>
                  <p className="loop-step-body">Evidence checked before closure</p>
                </div>
              </div>

              <div className="loop-step-item">
                <div className="loop-num-badge">3</div>
                <div className="loop-text-col">
                  <h4 className="loop-step-heading">You confirm</h4>
                  <p className="loop-step-body">Citizen feedback closes the loop</p>
                </div>
              </div>

              <div className="loop-step-item">
                <div className="loop-num-badge">4</div>
                <div className="loop-text-col">
                  <h4 className="loop-step-heading">Need another look?</h4>
                  <p className="loop-step-body">Request re-verification</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
