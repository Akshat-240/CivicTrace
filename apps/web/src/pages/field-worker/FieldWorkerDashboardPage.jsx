import React from 'react';
import { useNavigate } from 'react-router-dom';
import { mockFieldWorkerData } from '../../data/mockData';
import './FieldWorkerDashboardPage.css';

const FieldWorkerDashboardPage = () => {
  const navigate = useNavigate();
  const { summary, checklist, tasks } = mockFieldWorkerData;

  const handleOpenTask = (taskId) => {
    navigate(`/field-worker/tasks/${taskId}`);
  };

  return (
    <div className="ct-fw-page-container">
      {/* Header */}
      <div className="ct-fw-page-header">
        <h1 className="ct-fw-page-title">{summary.title}</h1>
        <p className="ct-fw-page-subtitle">{summary.subtitle}</p>
      </div>

      {/* Task Cards List */}
      <div className="ct-fw-task-list">
        {tasks.map((task, index) => {
          const isHigh = task.priority === 'HIGH';
          return (
            <div 
              key={task.id} 
              className={`ct-fw-task-card ${isHigh ? 'priority-high' : ''}`}
              onClick={() => handleOpenTask(task.id)}
            >
              <div className="ct-fw-task-left">
                <div className="ct-fw-task-badge-row">
                  <span className={`ct-fw-priority-pill priority-${task.priority.toLowerCase()}`}>
                    {task.priorityBadge}
                  </span>
                </div>

                <div className="ct-fw-task-title-group">
                  {isHigh ? (
                    <h2 className="ct-fw-task-title-main">{task.title}</h2>
                  ) : (
                    <div className="ct-fw-task-title-stacked">
                      <span className="ct-fw-task-code">{task.code}</span>
                      <h3 className="ct-fw-task-name">{task.incidentName}</h3>
                    </div>
                  )}
                  <div className="ct-fw-task-location">{task.location}</div>
                </div>
              </div>

              <div className="ct-fw-task-right">
                <div className="ct-fw-task-sla-block">
                  <span className="ct-fw-sla-label">
                    {isHigh ? 'SLA remaining' : 'SLA'}
                  </span>
                  <span className={`ct-fw-sla-value ${isHigh ? 'sla-urgent' : ''}`}>
                    {task.slaRemaining}
                  </span>
                </div>

                <button
                  type="button"
                  className={`ct-fw-open-btn ${isHigh ? 'btn-primary' : 'btn-outline'}`}
                  onClick={(e) => {
                    e.stopPropagation();
                    handleOpenTask(task.id);
                  }}
                >
                  {isHigh ? 'Open Incident' : 'Open'}
                </button>
              </div>
            </div>
          );
        })}
      </div>

      {/* Field Checklist Card */}
      <div className="ct-fw-checklist-card">
        <div className="ct-fw-checklist-content">
          <h3 className="ct-fw-checklist-title">Field checklist</h3>
          <ol className="ct-fw-checklist-items">
            {checklist.map((item, idx) => (
              <li key={idx}>{item}</li>
            ))}
          </ol>
        </div>

        <div className="ct-fw-checklist-badges">
          <span className="ct-fw-count-pill jobs-pill">{summary.activeJobsCount} jobs</span>
          <span className="ct-fw-count-pill risk-pill">{summary.highRiskCount} high risk</span>
        </div>
      </div>
    </div>
  );
};

export default FieldWorkerDashboardPage;
