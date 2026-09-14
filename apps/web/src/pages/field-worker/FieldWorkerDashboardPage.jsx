import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getWorkerTasks } from '../../services/api';
import './FieldWorkerDashboardPage.css';

const FieldWorkerDashboardPage = () => {
  const navigate = useNavigate();
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  
  const checklist = [
    "Ensure safety gear is worn",
    "Photograph before starting work",
    "Log any additional materials used",
    "Photograph completed work for verification"
  ];

  useEffect(() => {
    async function fetchTasks() {
      try {
        setLoading(true);
        
        const res = await getWorkerTasks();
        const myIncidents = res || [];
        
        // Filter out resolved, closed, etc. Field workers only see active work.
        const activeTasks = myIncidents.filter(inc => {
          const s = inc.status?.toUpperCase();
          return s === 'ACTIVE' || s === 'ASSIGNED' || s === 'IN_PROGRESS';
        });

        const mapped = activeTasks.map(inc => {
          const sla = inc.accountability_state?.toUpperCase() || 'PENDING';
          const isHigh = sla === 'OVERDUE' || sla === 'ESCALATION_ELIGIBLE';
          
          return {
            id: inc.id,
            code: inc.reference_number || inc.id.substring(0,8),
            title: inc.title || 'Untitled',
            incidentName: inc.title || 'Untitled',
            priority: isHigh ? 'HIGH' : 'NORMAL',
            priorityBadge: isHigh ? 'Critical SLA' : 'Routine',
            location: inc.location?.address_raw || 'Unknown Location',
            slaRemaining: sla
          };
        });

        setTasks(mapped);
      } catch (err) {
        console.error("Failed to load tasks", err);
      } finally {
        setLoading(false);
      }
    }
    fetchTasks();
  }, []);

  const handleOpenTask = (taskId) => {
    navigate(`/field-worker/tasks/${taskId}`);
  };

  const highRiskCount = tasks.filter(t => t.priority === 'HIGH').length;

  return (
    <div className="ct-fw-page-container">
      {/* Header */}
      <div className="ct-fw-page-header">
        <h1 className="ct-fw-page-title">Today's Assignments</h1>
        <p className="ct-fw-page-subtitle">Your active field jobs for today.</p>
      </div>

      {/* Task Cards List */}
      <div className="ct-fw-task-list">
        {loading ? <div style={{padding: '1rem'}}>Loading assignments...</div> : tasks.map((task, index) => {
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
        {!loading && tasks.length === 0 && (
          <div style={{padding: '1rem', color: '#666'}}>No active assignments for you.</div>
        )}
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
          <span className="ct-fw-count-pill jobs-pill">{tasks.length} jobs</span>
          <span className="ct-fw-count-pill risk-pill">{highRiskCount} high risk</span>
        </div>
      </div>
    </div>
  );
};

export default FieldWorkerDashboardPage;

