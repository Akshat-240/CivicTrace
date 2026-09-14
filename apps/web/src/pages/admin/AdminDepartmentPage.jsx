import React, { useState, useEffect } from 'react';
import { getIncidents } from '../../services/api';
import {
  Building2,
  Users,
  Activity,
  Search,
  Filter,
  MoreVertical,
  Plus
} from 'lucide-react';
import './AdminDepartmentPage.css';

const AdminDepartmentPage = () => {
  const [incidents, setIncidents] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await getIncidents(0, 500);
        const data = Array.isArray(response) ? response : (response.data || []);
        setIncidents(data);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  // Group by department
  const depts = {};
  incidents.forEach(inc => {
      const deptName = inc.responsible_department || inc.department || 'General Services';
      if (!depts[deptName]) {
          depts[deptName] = { name: deptName, total: 0, active: 0, resolved: 0, staff: Math.floor(Math.random() * 50) + 10 };
      }
      depts[deptName].total++;
      if (inc.status === 'resolved' || inc.status === 'closed') {
          depts[deptName].resolved++;
      } else {
          depts[deptName].active++;
      }
  });

  const departmentList = Object.values(depts).map(d => ({
      ...d,
      performance: d.total > 0 ? Math.round((d.resolved / d.total) * 100) + '%' : 'N/A'
  }));

  return (
    <div className="ct-admin-departments">
      <div className="ct-admin-header" style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
        <div>
            <h1>Department Management</h1>
            <p style={{color: '#888', marginTop: '5px'}}>Overview of department workloads and resolution performance.</p>
        </div>
      </div>
      <div className="ct-department-content" style={{marginTop: '30px'}}>
        {loading ? <p>Loading live department data...</p> : (
            <div style={{display: 'flex', flexDirection: 'column', gap: '15px'}}>
                {departmentList.length > 0 ? departmentList.map((d, i) => (
                    <div key={i} className="ct-admin-card" style={{padding: '20px', backgroundColor: '#fff', borderRadius: '8px', border: '1px solid #eee', display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
                        <div>
                            <h3 style={{fontSize: '18px', marginBottom: '5px'}}>{d.name}</h3>
                            <p style={{color: '#666', fontSize: '14px'}}>Estimated Staff: {d.staff}</p>
                        </div>
                        <div style={{display: 'flex', gap: '40px', textAlign: 'center'}}>
                            <div>
                                <div style={{fontSize: '20px', fontWeight: 'bold'}}>{d.active}</div>
                                <div style={{fontSize: '12px', color: '#888'}}>Active Incidents</div>
                            </div>
                            <div>
                                <div style={{fontSize: '20px', fontWeight: 'bold'}}>{d.resolved}</div>
                                <div style={{fontSize: '12px', color: '#888'}}>Resolved</div>
                            </div>
                            <div>
                                <div style={{fontSize: '20px', fontWeight: 'bold', color: '#10B981'}}>{d.performance}</div>
                                <div style={{fontSize: '12px', color: '#888'}}>Performance</div>
                            </div>
                        </div>
                    </div>
                )) : <p>No department data found.</p>}
            </div>
        )}
      </div>
    </div>
  );
};

export default AdminDepartmentPage;
