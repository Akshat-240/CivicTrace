import React, { useState, useEffect } from 'react';
import PageHeader from '../../components/layout/PageHeader';
import { getIncidents, getCurrentUser, getAuthorityWorkers, assignWorker } from '../../services/api';
import './AssignmentPage.css';

const AssignmentPage = () => {
  const [incidents, setIncidents] = useState([]);
  const [workers, setWorkers] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        const user = await getCurrentUser();
        const authId = user?.authority_id;
        if (!authId) return;

        const [incRes, workersRes] = await Promise.all([
          getIncidents(0, 100, null, authId),
          getAuthorityWorkers()
        ]);

        setIncidents(incRes?.data || []);
        setWorkers(workersRes || []);
      } catch (err) {
        console.error("Failed to load assignment data", err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  const handleAssign = async (incidentId, workerId) => {
    try {
      await assignWorker(incidentId, workerId);
      // Refresh
      const user = await getCurrentUser();
      const res = await getIncidents(0, 100, null, user.authority_id);
      setIncidents(res?.data || []);
      alert("Worker assigned successfully!");
    } catch (err) {
      console.error(err);
      alert("Failed to assign worker");
    }
  };

  const openIncidents = incidents.filter(i => !['closed', 'resolved', 'invalid'].includes(i.status?.toLowerCase()));

  return (
    <div className="ct-assignment-page">
      <PageHeader
        title="Assignment"
        subtitle="Route work to officers and field teams with clear ownership."
      />

      <div className="ct-assignment-grid" style={{ display: 'block', padding: '1rem' }}>
        {loading ? (
          <p>Loading...</p>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse', background: 'white', borderRadius: '8px', overflow: 'hidden', boxShadow: '0 1px 3px rgba(0,0,0,0.1)' }}>
            <thead>
              <tr style={{ background: '#f9fafb', borderBottom: '1px solid #e5e7eb' }}>
                <th style={{ padding: '12px', textAlign: 'left' }}>Incident ID</th>
                <th style={{ padding: '12px', textAlign: 'left' }}>Title</th>
                <th style={{ padding: '12px', textAlign: 'left' }}>Status</th>
                <th style={{ padding: '12px', textAlign: 'left' }}>Priority</th>
                <th style={{ padding: '12px', textAlign: 'left' }}>Assigned Worker</th>
              </tr>
            </thead>
            <tbody>
              {openIncidents.map(inc => (
                <tr key={inc.id} style={{ borderBottom: '1px solid #e5e7eb' }}>
                  <td style={{ padding: '12px' }}>{inc.reference_number || inc.id.substring(0,8).toUpperCase()}</td>
                  <td style={{ padding: '12px' }}>{inc.title || inc.issue_type?.replace(/_/g, ' ')?.toUpperCase()}</td>
                  <td style={{ padding: '12px' }}>{inc.status?.replace(/_/g, ' ')?.toUpperCase()}</td>
                  <td style={{ padding: '12px' }}>{inc.priority_level?.toUpperCase()}</td>
                  <td style={{ padding: '12px' }}>
                    <select
                      defaultValue={inc.assigned_worker_id || ""}
                      onChange={(e) => handleAssign(inc.id, e.target.value)}
                      style={{ padding: '6px', borderRadius: '4px', border: '1px solid #d1d5db', width: '200px' }}
                    >
                      <option value="" disabled>-- Select Worker --</option>
                      {workers.map(w => (
                        <option key={w.id} value={w.id}>{w.name}</option>
                      ))}
                    </select>
                  </td>
                </tr>
              ))}
              {openIncidents.length === 0 && (
                <tr>
                  <td colSpan="5" style={{ padding: '12px', textAlign: 'center', color: '#6b7280' }}>
                    No open incidents available for assignment.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};

export default AssignmentPage;
