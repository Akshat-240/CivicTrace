import React from 'react';
import PageHeader from '../../components/layout/PageHeader';
import './AssignmentPage.css';

const AssignmentPage = () => {
  return (
    <div className="ct-assignment-page">
      <PageHeader 
        title="Assignment"
        subtitle="Route work to officers and field teams with clear ownership."
      />

      <div className="ct-assignment-grid" style={{ display: 'block', padding: '2rem' }}>
        <div className="ct-card">
          <div className="ct-card-head">
            <h2 className="ct-card-title">Backend Limitation</h2>
          </div>
          <div style={{ padding: '1.5rem', color: '#4b5563', lineHeight: '1.6' }}>
            <p>
              <strong>Human officer/team assignment is not implemented in the current backend and is outside this Gate 4 scope.</strong>
            </p>
            <p style={{ marginTop: '1rem' }}>
              The existing API provides mapping from Incident → Jurisdiction → Authority, but it does not track individual personnel, field teams, or team loads. Creating fake backend officer assignment without a supporting data model violates the CivicTrace architecture principles.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AssignmentPage;
