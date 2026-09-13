import React, { useState } from 'react';
import { mockAdminDepartments } from '../../data/mockData';
import { 
  Plus, 
  Building2, 
  User, 
  CheckCircle2, 
  AlertTriangle, 
  Clock, 
  ChevronRight,
  SlidersHorizontal,
  X
} from 'lucide-react';
import './AdminDepartmentPage.css';

const AdminDepartmentPage = () => {
  const [departments, setDepartments] = useState(mockAdminDepartments);
  const [selectedZone, setSelectedZone] = useState('All Zones');
  const [selectedDeptModal, setSelectedDeptModal] = useState(null);
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [newDeptName, setNewDeptName] = useState('');
  const [newNodalOfficer, setNewNodalOfficer] = useState('');

  const filteredDepartments = departments.filter(d => {
    if (selectedZone === 'All Zones') return true;
    return d.zone.toLowerCase().includes(selectedZone.toLowerCase());
  });

  const handleAddDept = (e) => {
    e.preventDefault();
    if (!newDeptName) return;
    const newDept = {
      id: departments.length + 1,
      name: newDeptName,
      assigned: 0,
      resolved: 0,
      sla: '100%',
      open: 0,
      nodalOfficer: newNodalOfficer || 'Designated Officer',
      zone: 'Citywide'
    };
    setDepartments([...departments, newDept]);
    setIsAddModalOpen(false);
    setNewDeptName('');
    setNewNodalOfficer('');
  };

  return (
    <div className="ct-admin-departments-page">
      {/* Top Filter and Add Bar */}
      <div className="ct-depts-top-bar">
        <div className="ct-depts-filters">
          <select 
            value={selectedZone}
            onChange={(e) => setSelectedZone(e.target.value)}
            className="ct-depts-select"
          >
            <option>All Zones</option>
            <option>Central</option>
            <option>East</option>
            <option>North</option>
            <option>South</option>
          </select>

          <select className="ct-depts-select">
            <option>Performance: All</option>
            <option>SLA &gt; 90%</option>
            <option>High Open Workload</option>
          </select>
        </div>

        <button 
          type="button" 
          className="ct-depts-add-btn"
          onClick={() => setIsAddModalOpen(true)}
        >
          <Plus size={16} />
          <span>Add Department</span>
        </button>
      </div>

      {/* 5 KPI Cards */}
      <div className="ct-depts-kpi-grid">
        <div className="ct-depts-kpi-card">
          <span className="ct-dept-dot blue"></span>
          <div className="ct-dept-kpi-meta">
            <span className="ct-dept-kpi-val">{departments.length}</span>
            <span className="ct-dept-kpi-sub">Departments</span>
          </div>
        </div>

        <div className="ct-depts-kpi-card">
          <span className="ct-dept-dot green"></span>
          <div className="ct-dept-kpi-meta">
            <span className="ct-dept-kpi-val">1,284</span>
            <span className="ct-dept-kpi-sub">Assigned</span>
          </div>
        </div>

        <div className="ct-depts-kpi-card">
          <span className="ct-dept-dot green"></span>
          <div className="ct-dept-kpi-meta">
            <span className="ct-dept-kpi-val">91%</span>
            <span className="ct-dept-kpi-sub">Avg SLA</span>
          </div>
        </div>

        <div className="ct-depts-kpi-card">
          <span className="ct-dept-dot amber"></span>
          <div className="ct-dept-kpi-meta">
            <span className="ct-dept-kpi-val">132</span>
            <span className="ct-dept-kpi-sub">Unresolved</span>
          </div>
        </div>

        <div className="ct-depts-kpi-card">
          <span className="ct-dept-dot red"></span>
          <div className="ct-dept-kpi-meta">
            <span className="ct-dept-kpi-val">8</span>
            <span className="ct-dept-kpi-sub">At Risk</span>
          </div>
        </div>
      </div>

      {/* Department Performance Table */}
      <div className="ct-depts-table-card">
        <div className="ct-table-card-header">
          <h2 className="ct-card-title">Department Performance</h2>
          <p className="ct-card-subtitle">Ownership, resolution rate and open workload</p>
        </div>

        <table className="ct-depts-table">
          <thead>
            <tr>
              <th>Department</th>
              <th>Assigned</th>
              <th>Resolved</th>
              <th>SLA</th>
              <th>Open</th>
              <th>Nodal Officer</th>
              <th className="text-right">Action</th>
            </tr>
          </thead>
          <tbody>
            {filteredDepartments.map((dept) => (
              <tr key={dept.id}>
                <td className="font-bold text-dark">{dept.name}</td>
                <td>{dept.assigned}</td>
                <td className="text-green font-semibold">{dept.resolved}</td>
                <td className="text-green font-semibold">{dept.sla}</td>
                <td className="text-amber font-semibold">{dept.open}</td>
                <td className="text-secondary">{dept.nodalOfficer}</td>
                <td className="text-right">
                  <button 
                    type="button" 
                    className="ct-dept-manage-btn"
                    onClick={() => setSelectedDeptModal(dept)}
                  >
                    Manage
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Manage Department Modal */}
      {selectedDeptModal && (
        <div className="ct-modal-backdrop" onClick={() => setSelectedDeptModal(null)}>
          <div className="ct-modal-window" onClick={(e) => e.stopPropagation()}>
            <div className="ct-modal-header">
              <h3 className="ct-modal-title">Manage {selectedDeptModal.name}</h3>
              <button 
                type="button" 
                className="ct-modal-close"
                onClick={() => setSelectedDeptModal(null)}
              >
                <X size={18} />
              </button>
            </div>

            <div className="ct-modal-body">
              <div className="ct-modal-meta-row">
                <span className="ct-modal-label">Nodal Officer:</span>
                <span className="ct-modal-val font-bold">{selectedDeptModal.nodalOfficer}</span>
              </div>
              <div className="ct-modal-meta-row">
                <span className="ct-modal-label">Zone Jurisdiction:</span>
                <span className="ct-modal-val">{selectedDeptModal.zone}</span>
              </div>
              <div className="ct-modal-meta-row">
                <span className="ct-modal-label">SLA Compliance:</span>
                <span className="ct-modal-val text-green font-bold">{selectedDeptModal.sla}</span>
              </div>
              <div className="ct-modal-meta-row">
                <span className="ct-modal-label">Active Workload:</span>
                <span className="ct-modal-val font-bold">{selectedDeptModal.open} unresolved cases</span>
              </div>

              <div className="ct-modal-actions-area">
                <button 
                  type="button" 
                  className="ct-btn-primary full-width"
                  onClick={() => {
                    alert(`Dispatched workload re-balancing notice to ${selectedDeptModal.nodalOfficer}`);
                    setSelectedDeptModal(null);
                  }}
                >
                  Send Workload Re-balance Notice
                </button>
                <button 
                  type="button" 
                  className="ct-btn-sec full-width"
                  onClick={() => {
                    alert(`Nodal officer re-assignment workflow initiated for ${selectedDeptModal.name}`);
                    setSelectedDeptModal(null);
                  }}
                >
                  Re-assign Nodal Officer
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Add Department Modal */}
      {isAddModalOpen && (
        <div className="ct-modal-backdrop" onClick={() => setIsAddModalOpen(false)}>
          <div className="ct-modal-window" onClick={(e) => e.stopPropagation()}>
            <div className="ct-modal-header">
              <h3 className="ct-modal-title">Add Municipal Department</h3>
              <button 
                type="button" 
                className="ct-modal-close"
                onClick={() => setIsAddModalOpen(false)}
              >
                <X size={18} />
              </button>
            </div>

            <form onSubmit={handleAddDept} className="ct-modal-body">
              <div className="ct-modal-input-group">
                <label className="ct-form-label">Department Name</label>
                <input
                  type="text"
                  placeholder="e.g. Parks & Gardens Department"
                  className="ct-form-input"
                  value={newDeptName}
                  onChange={(e) => setNewDeptName(e.target.value)}
                  required
                />
              </div>

              <div className="ct-modal-input-group">
                <label className="ct-form-label">Nodal Officer Name</label>
                <input
                  type="text"
                  placeholder="e.g. Vikramaditya Sen"
                  className="ct-form-input"
                  value={newNodalOfficer}
                  onChange={(e) => setNewNodalOfficer(e.target.value)}
                  required
                />
              </div>

              <div className="ct-modal-actions-area">
                <button type="submit" className="ct-btn-primary full-width">
                  Create Department
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminDepartmentPage;
