import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getIncidents } from '../../services/api';
import {
  Search,
  Download,
  ChevronRight,
  SlidersHorizontal,
  ChevronDown,
  Eye,
  Flag
} from 'lucide-react';
import './AdminIncidentsPage.css';

const AdminIncidentsPage = () => {
  const navigate = useNavigate();
  const [searchTerm, setSearchTerm] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('All');
  const [statusFilter, setStatusFilter] = useState('All');
  const [priorityFilter, setPriorityFilter] = useState('All');

  const [incidents, setIncidents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchIncidents = async () => {
      try {
        const data = await getIncidents();
        setIncidents(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };
    fetchIncidents();
  }, []);

  const filteredIncidents = incidents.filter((inc) => {
    const matchesSearch =
      (inc.id || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
      (inc.description || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
      (inc.location_name || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
      (inc.category || '').toLowerCase().includes(searchTerm.toLowerCase());

    const matchesCat = categoryFilter === 'All' || (inc.category || '').toLowerCase().includes(categoryFilter.toLowerCase());
    const matchesStatus = statusFilter === 'All' || (inc.status || '').toLowerCase().includes(statusFilter.toLowerCase());
    const matchesPriority = priorityFilter === 'All' || (inc.priority || '').toLowerCase().includes(priorityFilter.toLowerCase());

    return matchesSearch && matchesCat && matchesStatus && matchesPriority;
  });

  const totalIncidents = incidents.length;
  const criticalCount = incidents.filter(i => (i.priority || '').toLowerCase() === 'critical').length;
  const highCount = incidents.filter(i => (i.priority || '').toLowerCase() === 'high').length;

  return (
    <div className="ct-admin-incidents-page">
      {/* Top Stat row */}
      <div className="ct-incidents-stat-bar">
        <div className="ct-inc-stat-card">
          <div className="ct-inc-stat-dot blue"></div>
          <div className="ct-inc-stat-content">
            <span className="ct-inc-stat-val">{loading ? '-' : totalIncidents}</span>
            <span className="ct-inc-stat-label">Total Incidents</span>
          </div>
        </div>

        <div className="ct-inc-stat-card">
          <div className="ct-inc-stat-dot red"></div>
          <div className="ct-inc-stat-content">
            <span className="ct-inc-stat-val">{loading ? '-' : criticalCount}</span>
            <span className="ct-inc-stat-label">Critical</span>
          </div>
        </div>

        <div className="ct-inc-stat-card">
          <div className="ct-inc-stat-dot amber"></div>
          <div className="ct-inc-stat-content">
            <span className="ct-inc-stat-val">{loading ? '-' : highCount}</span>
            <span className="ct-inc-stat-label">High</span>
          </div>
        </div>

        <div className="ct-inc-stat-card">
          <div className="ct-inc-stat-dot yellow"></div>
          <div className="ct-inc-stat-content">
            <span className="ct-inc-stat-val">23</span>
            <span className="ct-inc-stat-label">SLA Breached</span>
          </div>
        </div>

        <div className="ct-inc-stat-actions">
          <button
            type="button"
            className="ct-inc-export-btn"
            onClick={() => alert("Generating full CSV export of citywide incidents...")}
          >
            <Download size={16} />
            <span>Export / Actions</span>
          </button>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="ct-incidents-filter-panel">
        <div className="ct-inc-search-box">
          <Search size={17} className="ct-inc-search-icon" />
          <input
            type="text"
            className="ct-inc-search-input"
            placeholder="Search incident, ID, location, department..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>

        <div className="ct-filter-pills-row">
          <div className="ct-filter-select-wrapper">
            <select
              value={categoryFilter}
              onChange={(e) => setCategoryFilter(e.target.value)}
              className="ct-filter-dropdown"
            >
              <option value="All">All Categories</option>
              <option value="Road">Road Damage</option>
              <option value="Sanitation">Sanitation</option>
              <option value="Streetlight">Streetlight</option>
              <option value="Water">Water Supply</option>
              <option value="Drainage">Drainage</option>
            </select>
            <ChevronDown size={14} className="ct-dropdown-chevron" />
          </div>

          <div className="ct-filter-select-wrapper">
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="ct-filter-dropdown"
            >
              <option value="All">All Status</option>
              <option value="reported">Reported</option>
              <option value="assigned">Assigned</option>
              <option value="in_progress">In Progress</option>
              <option value="resolved">Resolved</option>
              <option value="verified">Verified</option>
            </select>
            <ChevronDown size={14} className="ct-dropdown-chevron" />
          </div>

          <div className="ct-filter-select-wrapper">
            <select
              value={priorityFilter}
              onChange={(e) => setPriorityFilter(e.target.value)}
              className="ct-filter-dropdown"
            >
              <option value="All">All Priorities</option>
              <option value="Critical">Critical</option>
              <option value="High">High</option>
              <option value="Medium">Medium</option>
              <option value="Low">Low</option>
            </select>
            <ChevronDown size={14} className="ct-dropdown-chevron" />
          </div>
        </div>
      </div>

      {/* Incidents Table */}
      <div className="ct-incidents-table-container">
        {loading ? (
          <div style={{ padding: '2rem', textAlign: 'center' }}>Loading incidents...</div>
        ) : error ? (
          <div style={{ padding: '2rem', textAlign: 'center', color: 'red' }}>Error: {error}</div>
        ) : (
        <table className="ct-admin-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>ISSUE</th>
              <th>CATEGORY</th>
              <th>LOCATION</th>
              <th>PRIORITY</th>
              <th>STATUS</th>
              <th>REPORTED</th>
              <th className="text-right">ACTION</th>
            </tr>
          </thead>
          <tbody>
            {filteredIncidents.map((inc) => {
              const prio = (inc.priority || '').toLowerCase();
              let priorityClass = 'badge-amber';
              if (prio === 'critical') priorityClass = 'badge-red';
              else if (prio === 'medium') priorityClass = 'badge-yellow';
              else if (prio === 'low') priorityClass = 'badge-blue';

              const stat = (inc.status || '').toLowerCase();
              let statusClass = 'badge-status-blue';
              if (stat === 'in_progress' || stat === 'assigned') statusClass = 'badge-status-amber';
              else if (stat === 'resolved' || stat === 'verified') statusClass = 'badge-status-green';

              return (
                <tr
                  key={inc.id}
                  onClick={() => navigate(`/admin/incidents/${inc.id}`)}
                  className="ct-table-row-clickable"
                >
                  <td className="font-semibold text-primary">{inc.id}</td>
                  <td className="font-bold">{inc.description}</td>
                  <td className="text-muted">{inc.category || 'N/A'}</td>
                  <td className="text-secondary">{inc.location_name || 'N/A'}</td>
                  <td>
                    <span className={`ct-badge-pill ${priorityClass}`}>
                      {inc.priority || 'N/A'}
                    </span>
                  </td>
                  <td>
                    <span className={`ct-badge-pill ${statusClass}`}>
                      {inc.status || 'N/A'}
                    </span>
                  </td>
                  <td className="text-muted">
                    {inc.created_at ? new Date(inc.created_at).toLocaleDateString() : 'N/A'}
                  </td>
                  <td className="text-right" onClick={(e) => e.stopPropagation()}>
                    <button
                      type="button"
                      className="ct-action-view-btn"
                      onClick={() => navigate(`/admin/incidents/${inc.id}`)}
                    >
                      <span>View</span>
                      <ChevronRight size={14} />
                    </button>
                  </td>
                </tr>
              );
            })}
            {filteredIncidents.length === 0 && (
              <tr>
                <td colSpan="8" style={{ textAlign: 'center', padding: '2rem' }}>
                  No incidents found matching filters.
                </td>
              </tr>
            )}
          </tbody>
        </table>
        )}

        {/* Footer */}
        <div className="ct-table-footer">
          <span className="ct-showing-text">
            Showing {filteredIncidents.length > 0 ? 1 : 0}-{filteredIncidents.length} of {totalIncidents} incidents
          </span>

          <div className="ct-pagination-controls">
            <button type="button" className="ct-page-btn disabled" disabled>Previous</button>
            <button type="button" className="ct-page-btn active">1</button>
            <button type="button" className="ct-page-btn disabled" disabled>Next</button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdminIncidentsPage;
