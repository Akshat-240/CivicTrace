import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { mockAdminIncidents } from '../../data/mockData';
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

  const filteredIncidents = mockAdminIncidents.filter((inc) => {
    const matchesSearch = 
      inc.id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      inc.issue.toLowerCase().includes(searchTerm.toLowerCase()) ||
      inc.location.toLowerCase().includes(searchTerm.toLowerCase()) ||
      inc.department.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesCat = categoryFilter === 'All' || inc.category.toLowerCase().includes(categoryFilter.toLowerCase());
    const matchesStatus = statusFilter === 'All' || inc.status.toLowerCase().includes(statusFilter.toLowerCase());
    const matchesPriority = priorityFilter === 'All' || inc.priority.toLowerCase().includes(priorityFilter.toLowerCase());

    return matchesSearch && matchesCat && matchesStatus && matchesPriority;
  });

  return (
    <div className="ct-admin-incidents-page">
      {/* Top Stat row */}
      <div className="ct-incidents-stat-bar">
        <div className="ct-inc-stat-card">
          <div className="ct-inc-stat-dot blue"></div>
          <div className="ct-inc-stat-content">
            <span className="ct-inc-stat-val">284</span>
            <span className="ct-inc-stat-label">Total Incidents</span>
          </div>
        </div>

        <div className="ct-inc-stat-card">
          <div className="ct-inc-stat-dot red"></div>
          <div className="ct-inc-stat-content">
            <span className="ct-inc-stat-val">18</span>
            <span className="ct-inc-stat-label">Critical</span>
          </div>
        </div>

        <div className="ct-inc-stat-card">
          <div className="ct-inc-stat-dot amber"></div>
          <div className="ct-inc-stat-content">
            <span className="ct-inc-stat-val">47</span>
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
              <option value="Open">Open</option>
              <option value="In Progress">In Progress</option>
              <option value="Resolved">Resolved</option>
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
              let priorityClass = 'badge-amber';
              if (inc.priority === 'Critical') priorityClass = 'badge-red';
              else if (inc.priority === 'Medium') priorityClass = 'badge-yellow';
              else if (inc.priority === 'Low') priorityClass = 'badge-blue';

              let statusClass = 'badge-status-blue';
              if (inc.status === 'In Progress') statusClass = 'badge-status-amber';
              else if (inc.status === 'Resolved') statusClass = 'badge-status-green';

              return (
                <tr 
                  key={inc.id}
                  onClick={() => navigate(`/admin/incidents/${inc.rawId}`)}
                  className="ct-table-row-clickable"
                >
                  <td className="font-semibold text-primary">{inc.id}</td>
                  <td className="font-bold">{inc.issue}</td>
                  <td className="text-muted">{inc.category}</td>
                  <td className="text-secondary">{inc.location}</td>
                  <td>
                    <span className={`ct-badge-pill ${priorityClass}`}>
                      {inc.priority}
                    </span>
                  </td>
                  <td>
                    <span className={`ct-badge-pill ${statusClass}`}>
                      {inc.status}
                    </span>
                  </td>
                  <td className="text-muted">{inc.reported}</td>
                  <td className="text-right" onClick={(e) => e.stopPropagation()}>
                    <button 
                      type="button" 
                      className="ct-action-view-btn"
                      onClick={() => navigate(`/admin/incidents/${inc.rawId}`)}
                    >
                      <span>View</span>
                      <ChevronRight size={14} />
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>

        {/* Footer */}
        <div className="ct-table-footer">
          <span className="ct-showing-text">
            Showing 1-{filteredIncidents.length} of 284 incidents
          </span>

          <div className="ct-pagination-controls">
            <button type="button" className="ct-page-btn disabled" disabled>Previous</button>
            <button type="button" className="ct-page-btn active">1</button>
            <button type="button" className="ct-page-btn">2</button>
            <button type="button" className="ct-page-btn">3</button>
            <button type="button" className="ct-page-btn">Next</button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdminIncidentsPage;
