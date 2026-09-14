import React, { useState, useEffect } from 'react';
import { getIncidents } from '../../services/api';
import {
  BarChart2,
  TrendingUp,
  PieChart as PieChartIcon,
  Download,
  Calendar,
  Filter,
  ChevronDown
} from 'lucide-react';
import './AdminAnalysisPage.css';

const AdminAnalysisPage = () => {
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
  const resolved = incidents.filter(i => (i.status || '').toLowerCase() === 'resolved').length;
  const pending = incidents.filter(i => (i.status || '').toLowerCase() !== 'resolved').length;
  const resolutionRate = totalIncidents > 0 ? Math.round((resolved / totalIncidents) * 100) + '%' : '0%';

  const cats = {};
  incidents.forEach(inc => {
    const cat = inc.issue_type || inc.category || 'Other';
    cats[cat] = (cats[cat] || 0) + 1;
  });
  const categories = Object.keys(cats).map(k => ({
    name: k.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
    value: cats[k],
    percent: totalIncidents > 0 ? Math.round((cats[k] / totalIncidents) * 100) : 0
  })).sort((a,b) => b.value - a.value);

  return (
    <div className="ct-admin-analysis">
      <div className="ct-admin-header">
        <div>
            <h1>Advanced Analytics</h1>
            <p style={{color: '#888', marginTop: '5px'}}>Citywide performance, trends, SLA health and resolution intelligence.</p>
        </div>
      </div>
      <div className="ct-analysis-content" style={{marginTop: '30px'}}>
        {loading ? (
            <p>Loading analytics from live data...</p>
        ) : (
            <>
                <div style={{display: 'flex', gap: '20px', marginBottom: '30px'}}>
                    <div className="ct-admin-card" style={{flex: 1, padding: '20px', backgroundColor: '#fff', borderRadius: '8px', border: '1px solid #eee'}}>
                        <h3 style={{color: '#666', fontSize: '14px', marginBottom: '10px'}}>Total Incidents</h3>
                        <div style={{fontSize: '32px', fontWeight: 'bold'}}>{totalIncidents}</div>
                    </div>
                    <div className="ct-admin-card" style={{flex: 1, padding: '20px', backgroundColor: '#fff', borderRadius: '8px', border: '1px solid #eee'}}>
                        <h3 style={{color: '#666', fontSize: '14px', marginBottom: '10px'}}>Resolved</h3>
                        <div style={{fontSize: '32px', fontWeight: 'bold', color: '#10B981'}}>{resolved}</div>
                    </div>
                    <div className="ct-admin-card" style={{flex: 1, padding: '20px', backgroundColor: '#fff', borderRadius: '8px', border: '1px solid #eee'}}>
                        <h3 style={{color: '#666', fontSize: '14px', marginBottom: '10px'}}>Pending</h3>
                        <div style={{fontSize: '32px', fontWeight: 'bold', color: '#F59E0B'}}>{pending}</div>
                    </div>
                    <div className="ct-admin-card" style={{flex: 1, padding: '20px', backgroundColor: '#fff', borderRadius: '8px', border: '1px solid #eee'}}>
                        <h3 style={{color: '#666', fontSize: '14px', marginBottom: '10px'}}>Resolution Rate</h3>
                        <div style={{fontSize: '32px', fontWeight: 'bold', color: '#3B82F6'}}>{resolutionRate}</div>
                    </div>
                </div>

                <h3 style={{marginBottom: '15px'}}>Incidents by Category</h3>
                <div style={{display: 'flex', gap: '20px', flexWrap: 'wrap'}}>
                    {categories.length > 0 ? categories.map(c => (
                        <div key={c.name} className="ct-admin-card" style={{padding: '15px', minWidth: '200px', backgroundColor: '#fff', borderRadius: '8px', border: '1px solid #eee'}}>
                            <div style={{fontSize: '16px', fontWeight: '600', marginBottom: '8px'}}>{c.name}</div>
                            <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end'}}>
                                <span style={{fontSize: '24px'}}>{c.value}</span>
                                <span style={{color: '#888', fontSize: '14px'}}>{c.percent}%</span>
                            </div>
                        </div>
                    )) : <p>No category data available.</p>}
                </div>
            </>
        )}
      </div>
    </div>
  );
};

export default AdminAnalysisPage;
