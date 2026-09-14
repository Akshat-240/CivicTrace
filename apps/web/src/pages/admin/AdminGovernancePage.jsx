import React, { useState, useEffect } from 'react';
import { getIncidents } from '../../services/api';
import {
  Scale,
  FileText,
  ShieldCheck,
  Search,
  Filter,
  Eye,
  Plus
} from 'lucide-react';
import './AdminGovernancePage.css';

const AdminGovernancePage = () => {
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

  const totalIncidents = incidents.length;
  const escalations = incidents.filter(i => i.accountability_state === 'escalation_eligible').length;
  const overdue = incidents.filter(i => i.accountability_state === 'overdue').length;

  const [governanceData] = useState({
    policies: [
      { id: 'POL-01', title: 'Data Privacy Policy', status: 'Active', lastUpdated: '2026-08-15' },
      { id: 'POL-02', title: 'SLA Framework', status: 'Active', lastUpdated: '2026-09-01' }
    ]
  });

  return (
    <div className="ct-admin-governance">
      <div className="ct-admin-header" style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
        <div>
            <h1>Governance & Policies</h1>
            <p style={{color: '#888', marginTop: '5px'}}>Policy enforcement, escalation audits, and regulatory compliance.</p>
        </div>
      </div>
      <div className="ct-governance-content" style={{marginTop: '30px'}}>
        {loading ? <p>Loading live compliance data...</p> : (
            <>
                <div style={{display: 'flex', gap: '20px', marginBottom: '30px'}}>
                    <div className="ct-admin-card" style={{flex: 1, padding: '20px', backgroundColor: '#fff', borderRadius: '8px', border: '1px solid #eee'}}>
                        <h3 style={{color: '#666', fontSize: '14px', marginBottom: '10px'}}>Total Audited Incidents</h3>
                        <div style={{fontSize: '32px', fontWeight: 'bold'}}>{totalIncidents}</div>
                    </div>
                    <div className="ct-admin-card" style={{flex: 1, padding: '20px', backgroundColor: '#fff', borderRadius: '8px', border: '1px solid #eee'}}>
                        <h3 style={{color: '#666', fontSize: '14px', marginBottom: '10px'}}>Policy Violations (Overdue)</h3>
                        <div style={{fontSize: '32px', fontWeight: 'bold', color: '#EF4444'}}>{overdue}</div>
                    </div>
                    <div className="ct-admin-card" style={{flex: 1, padding: '20px', backgroundColor: '#fff', borderRadius: '8px', border: '1px solid #eee'}}>
                        <h3 style={{color: '#666', fontSize: '14px', marginBottom: '10px'}}>Active Escalations</h3>
                        <div style={{fontSize: '32px', fontWeight: 'bold', color: '#F59E0B'}}>{escalations}</div>
                    </div>
                </div>

                <h3 style={{marginBottom: '15px'}}>Active Policies</h3>
                <div style={{display: 'flex', flexDirection: 'column', gap: '10px'}}>
                    {governanceData.policies.map(p => (
                        <div key={p.id} className="ct-admin-card" style={{padding: '15px', backgroundColor: '#fff', borderRadius: '8px', border: '1px solid #eee', display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
                            <div>
                                <div style={{fontSize: '16px', fontWeight: '600'}}>{p.title}</div>
                                <div style={{fontSize: '12px', color: '#888'}}>ID: {p.id} | Last Updated: {p.lastUpdated}</div>
                            </div>
                            <div style={{padding: '5px 12px', backgroundColor: '#ECFDF5', color: '#10B981', borderRadius: '20px', fontSize: '12px', fontWeight: 'bold'}}>
                                {p.status}
                            </div>
                        </div>
                    ))}
                </div>
            </>
        )}
      </div>
    </div>
  );
};

export default AdminGovernancePage;
