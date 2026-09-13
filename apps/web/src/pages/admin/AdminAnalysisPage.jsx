import React, { useState } from 'react';
import { mockAdminAnalytics } from '../../data/mockData';
import { 
  Download, 
  TrendingUp, 
  BarChart2, 
  MapPin, 
  CheckCircle2, 
  AlertOctagon, 
  ChevronDown 
} from 'lucide-react';
import './AdminAnalysisPage.css';

const AdminAnalysisPage = () => {
  const [timeRange, setTimeRange] = useState('Last 30 Days');
  const [selectedDept, setSelectedDept] = useState('All Departments');

  const { 
    totalIncidents, 
    resolved, 
    slaBreached, 
    slaCompliance, 
    verifiedResolution, 
    trendData, 
    categoryMix, 
    hotspots, 
    departmentPerformance 
  } = mockAdminAnalytics;

  return (
    <div className="ct-admin-analytics-page">
      {/* Top Filter and Export Bar */}
      <div className="ct-analytics-top-bar">
        <div className="ct-analytics-filters">
          <span className="ct-filter-label">Reporting period</span>
          <select 
            value={timeRange} 
            onChange={(e) => setTimeRange(e.target.value)}
            className="ct-analytics-select"
          >
            <option>Last 30 Days</option>
            <option>Last 14 Days</option>
            <option>Last Quarter</option>
          </select>

          <select className="ct-analytics-select">
            <option>All Categories</option>
            <option>Road Damage</option>
            <option>Sanitation</option>
            <option>Water Supply</option>
          </select>

          <select 
            value={selectedDept}
            onChange={(e) => setSelectedDept(e.target.value)}
            className="ct-analytics-select"
          >
            <option>All Departments</option>
            <option>Roads Department</option>
            <option>Sanitation Department</option>
            <option>Water Supply</option>
          </select>

          <select className="ct-analytics-select">
            <option>All Wards</option>
            <option>Ward 12</option>
            <option>Ward 8</option>
            <option>Ward 14</option>
          </select>
        </div>

        <button 
          type="button" 
          className="ct-analytics-export-btn"
          onClick={() => alert("Exporting full analytics and trend PDF report...")}
        >
          <Download size={15} />
          <span>Export Report</span>
        </button>
      </div>

      {/* 5 KPI Cards */}
      <div className="ct-analytics-kpi-bar">
        <div className="ct-analytics-kpi-card">
          <span className="ct-kpi-dot blue"></span>
          <div className="ct-kpi-content">
            <span className="ct-kpi-number">{totalIncidents}</span>
            <span className="ct-kpi-sub">Total Incidents</span>
          </div>
        </div>

        <div className="ct-analytics-kpi-card">
          <span className="ct-kpi-dot green"></span>
          <div className="ct-kpi-content">
            <span className="ct-kpi-number">{resolved}</span>
            <span className="ct-kpi-sub">Resolved</span>
          </div>
        </div>

        <div className="ct-analytics-kpi-card">
          <span className="ct-kpi-dot red"></span>
          <div className="ct-kpi-content">
            <span className="ct-kpi-number">{slaBreached}</span>
            <span className="ct-kpi-sub">SLA Breached</span>
          </div>
        </div>

        <div className="ct-analytics-kpi-card">
          <span className="ct-kpi-dot green"></span>
          <div className="ct-kpi-content">
            <span className="ct-kpi-number">{slaCompliance}</span>
            <span className="ct-kpi-sub">SLA Compliance</span>
          </div>
        </div>

        <div className="ct-analytics-kpi-card">
          <span className="ct-kpi-dot gold"></span>
          <div className="ct-kpi-content">
            <span className="ct-kpi-number">{verifiedResolution}</span>
            <span className="ct-kpi-sub">Verified Resolution</span>
          </div>
        </div>
      </div>

      {/* Main Grid: Left Charts & Tables, Right Rail Metrics */}
      <div className="ct-analytics-grid">
        {/* Left Column */}
        <div className="ct-analytics-main-col">
          {/* Trend Chart Card */}
          <div className="ct-analytics-card">
            <div className="ct-card-top-row">
              <div>
                <h2 className="ct-card-title">Incident Volume & Resolution Trend</h2>
                <p className="ct-card-subtitle">Reports vs resolved incidents · last 30 days</p>
              </div>

              <div className="ct-chart-legend">
                <div className="ct-chart-legend-item">
                  <span className="ct-legend-line blue"></span>
                  <span>Reported</span>
                </div>
                <div className="ct-chart-legend-item">
                  <span className="ct-legend-line green"></span>
                  <span>Resolved</span>
                </div>
              </div>
            </div>

            {/* Responsive SVG Line Chart */}
            <div className="ct-svg-chart-container">
              <svg className="ct-trend-chart-svg" viewBox="0 0 800 240" preserveAspectRatio="none">
                {/* Horizontal Grid lines */}
                <line x1="40" y1="30" x2="780" y2="30" stroke="#F1F5F9" strokeWidth="1" />
                <line x1="40" y1="85" x2="780" y2="85" stroke="#F1F5F9" strokeWidth="1" />
                <line x1="40" y1="140" x2="780" y2="140" stroke="#F1F5F9" strokeWidth="1" />
                <line x1="40" y1="195" x2="780" y2="195" stroke="#E2E8F0" strokeWidth="1" />

                {/* Y-axis labels */}
                <text x="15" y="35" fill="#94A3B8" fontSize="11" fontWeight="600">60</text>
                <text x="15" y="90" fill="#94A3B8" fontSize="11" fontWeight="600">45</text>
                <text x="15" y="145" fill="#94A3B8" fontSize="11" fontWeight="600">30</text>
                <text x="15" y="200" fill="#94A3B8" fontSize="11" fontWeight="600">0</text>

                {/* Reported Path (Blue) */}
                <path
                  d="M 60 145 L 140 155 L 220 130 L 300 170 L 380 135 L 460 145 L 540 170 L 620 110 L 700 125 L 760 105"
                  fill="none"
                  stroke="#2563EB"
                  strokeWidth="3"
                  strokeLinecap="round"
                />

                {/* Resolved Path (Green) */}
                <path
                  d="M 60 190 L 140 185 L 220 195 L 300 180 L 380 170 L 460 165 L 540 185 L 620 155 L 700 140 L 760 130"
                  fill="none"
                  stroke="#10B981"
                  strokeWidth="3"
                  strokeLinecap="round"
                />

                {/* Reported Data Points */}
                {[
                  [60, 145], [140, 155], [220, 130], [300, 170], [380, 135],
                  [460, 145], [540, 170], [620, 110], [700, 125], [760, 105]
                ].map(([x, y], i) => (
                  <circle key={`rep-${i}`} cx={x} cy={y} r="4" fill="#2563EB" stroke="#FFFFFF" strokeWidth="2" />
                ))}

                {/* Resolved Data Points */}
                {[
                  [60, 190], [140, 185], [220, 195], [300, 180], [380, 170],
                  [460, 165], [540, 185], [620, 155], [700, 140], [760, 130]
                ].map(([x, y], i) => (
                  <circle key={`res-${i}`} cx={x} cy={y} r="4" fill="#10B981" stroke="#FFFFFF" strokeWidth="2" />
                ))}

                {/* X-axis labels */}
                {trendData.map((d, i) => {
                  const x = 60 + i * 77;
                  return (
                    <text key={d.date} x={x} y="225" textAnchor="middle" fill="#64748B" fontSize="11" fontWeight="500">
                      {d.date}
                    </text>
                  );
                })}
              </svg>
            </div>
          </div>

          {/* Department Performance Table */}
          <div className="ct-analytics-card">
            <h2 className="ct-card-title">Department Performance</h2>
            <p className="ct-card-subtitle">Resolution rate, SLA adherence and open workload</p>

            <table className="ct-perf-table">
              <thead>
                <tr>
                  <th>Department</th>
                  <th>Resolution</th>
                  <th>SLA</th>
                  <th className="text-right">Open</th>
                </tr>
              </thead>
              <tbody>
                {departmentPerformance.map((dept) => (
                  <tr key={dept.name}>
                    <td className="font-bold">{dept.name}</td>
                    <td className="text-green font-semibold">{dept.resolution}</td>
                    <td className="text-primary font-semibold">{dept.sla}</td>
                    <td className="text-right font-bold">{dept.open}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Right Rail */}
        <div className="ct-analytics-side-rail">
          {/* Incident Category Mix */}
          <div className="ct-analytics-card">
            <h2 className="ct-card-title">Incident Category Mix</h2>
            <div className="ct-category-mix-list">
              {categoryMix.map((cat) => (
                <div key={cat.label} className="ct-cat-mix-item">
                  <div className="ct-cat-mix-label-row">
                    <div className="ct-cat-name-dot">
                      <span className="ct-cat-dot" style={{ backgroundColor: cat.color }}></span>
                      <span className="ct-cat-name">{cat.label}</span>
                    </div>
                    <span className="ct-cat-count">{cat.count}</span>
                  </div>
                  <div className="ct-cat-bar-bg">
                    <div 
                      className="ct-cat-bar-fill" 
                      style={{ 
                        width: `${(cat.count / 93) * 100}%`,
                        backgroundColor: cat.color 
                      }}
                    ></div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Geographic Hotspots */}
          <div className="ct-analytics-card">
            <h2 className="ct-card-title">Geographic Hotspots</h2>
            <div className="ct-hotspots-list">
              {hotspots.map((spot, i) => (
                <div key={spot.ward} className="ct-hotspot-item">
                  <div className="ct-hotspot-rank">{i + 1}</div>
                  <div className="ct-hotspot-info">
                    <span className="ct-hotspot-ward">{spot.ward}</span>
                    <span className="ct-hotspot-cnt">{spot.incidents} incidents</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Resolution Verification */}
          <div className="ct-analytics-card">
            <h2 className="ct-card-title">Resolution Verification</h2>
            <div className="ct-res-status-row">
              <div className="ct-res-pill verified">
                <span className="ct-res-dot"></span>
                <span>Verified</span>
              </div>
              <div className="ct-res-pill pending">
                <span className="ct-res-dot"></span>
                <span>Pending Review</span>
              </div>
              <div className="ct-res-pill rejected">
                <span className="ct-res-dot"></span>
                <span>Rejected</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdminAnalysisPage;
