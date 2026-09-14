import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { mockFieldWorkerData } from '../../data/mockData';
import { MapPin, Navigation, Compass, CheckCircle } from 'lucide-react';
import './FieldWorkerLocationPage.css';

const FieldWorkerLocationPage = () => {
  const navigate = useNavigate();
  const task = mockFieldWorkerData.tasks[0];
  const { locationChecks } = task;

  const [coords, setCoords] = useState(locationChecks.coordinates);
  const [accuracy, setAccuracy] = useState(locationChecks.accuracy);
  const [isSimulated, setIsSimulated] = useState(false);
  const [isConfirmed, setIsConfirmed] = useState(false);

  useEffect(() => {
    if ('geolocation' in navigator) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          const lat = position.coords.latitude.toFixed(4);
          const lon = position.coords.longitude.toFixed(4);
          setCoords(`${lat}° N, ${lon}° E`);
          setAccuracy(`± ${Math.round(position.coords.accuracy || 8)} m`);
          setIsSimulated(false);
        },
        () => {
          // Fallback to mock coordinates
          setIsSimulated(true);
        },
        { timeout: 5000 }
      );
    } else {
      setIsSimulated(true);
    }
  }, []);

  const handleConfirmLocation = () => {
    setIsConfirmed(true);
    setTimeout(() => {
      navigate('/field-worker/evidence');
    }, 400);
  };

  return (
    <div className="ct-fw-page-container">
      {/* Header */}
      <div className="ct-fw-page-header">
        <h1 className="ct-fw-page-title">Location & Map</h1>
        <p className="ct-fw-page-subtitle">Verify the work point before recording field action</p>
      </div>

      {/* Main Grid: Map view on left, Location checks on right */}
      <div className="ct-fw-location-grid">
        {/* Left Big Card: Work location and Map */}
        <div className="ct-fw-card ct-fw-work-location-card">
          <div className="ct-fw-location-header">
            <span className="ct-fw-card-header-label">Work location</span>
            <h2 className="ct-fw-location-title">{task.fullLocation}</h2>
            <div className="ct-fw-location-sub">
              {task.ward} • {task.roadSegment}
            </div>
          </div>

          {/* Interactive Simulated GIS / GPS Map Canvas */}
          <div className="ct-fw-map-canvas-container">
            <svg 
              className="ct-fw-map-svg" 
              viewBox="0 0 700 380" 
              preserveAspectRatio="xMidYMid slice"
            >
              {/* Background City Grid */}
              <defs>
                <pattern id="fwMapGrid" width="40" height="40" patternUnits="userSpaceOnUse">
                  <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#E2E8F0" strokeWidth="1" />
                </pattern>
                <radialGradient id="radarGlow" cx="50%" cy="50%" r="50%">
                  <stop offset="0%" stopColor="#2563EB" stopOpacity="0.4" />
                  <stop offset="100%" stopColor="#2563EB" stopOpacity="0.0" />
                </radialGradient>
              </defs>
              <rect width="700" height="380" fill="#F8FAFC" />
              <rect width="700" height="380" fill="url(#fwMapGrid)" />

              {/* Major Roads */}
              <path d="M 0 190 Q 300 210 700 160" stroke="#CBD5E1" strokeWidth="16" fill="none" strokeLinecap="round" />
              <path d="M 0 190 Q 300 210 700 160" stroke="#FFFFFF" strokeWidth="12" fill="none" strokeLinecap="round" />

              {/* Secondary Cross Road */}
              <path d="M 320 0 Q 340 180 380 380" stroke="#CBD5E1" strokeWidth="12" fill="none" strokeLinecap="round" />
              <path d="M 320 0 Q 340 180 380 380" stroke="#FFFFFF" strokeWidth="8" fill="none" strokeLinecap="round" />

              {/* Road Name Labels */}
              <text x="60" y="175" fill="#64748B" fontSize="11" fontWeight="600" letterSpacing="0.5">
                MAHATMA GANDHI ROAD (MG ROAD)
              </text>
              <text x="395" y="60" fill="#64748B" fontSize="10" fontWeight="600">
                HAZRATGANJ LANE 4
              </text>

              {/* Ward Boundary Polygon */}
              <polygon 
                points="180,60 560,50 620,320 220,330" 
                fill="#3B82F6" 
                fillOpacity="0.04" 
                stroke="#3B82F6" 
                strokeWidth="1.5" 
                strokeDasharray="4 4" 
              />
              <text x="235" y="85" fill="#3B82F6" fontSize="10" fontWeight="700">
                WARD 12 ZONE BOUNDARY
              </text>

              {/* Radar Pulsing Radius around pin */}
              <circle cx="340" cy="190" r="50" fill="url(#radarGlow)" className="ct-fw-radar-ring" />
              <circle cx="340" cy="190" r="28" fill="none" stroke="#2563EB" strokeWidth="1.5" strokeDasharray="3 3" />

              {/* Incident Pin */}
              <g transform="translate(340, 190)">
                <circle cx="0" cy="0" r="14" fill="#EF4444" fillOpacity="0.2" />
                <circle cx="0" cy="0" r="8" fill="#EF4444" />
                <circle cx="0" cy="0" r="3" fill="#FFFFFF" />
              </g>

              {/* Worker Current Location Pin (Within 6m) */}
              <g transform="translate(352, 182)">
                <circle cx="0" cy="0" r="8" fill="#2563EB" />
                <circle cx="0" cy="0" r="3" fill="#FFFFFF" />
              </g>

              {/* Center Banner Label */}
              <rect x="260" y="130" width="160" height="28" rx="6" fill="#0F172A" fillOpacity="0.85" />
              <text x="340" y="148" fill="#FFFFFF" fontSize="11" fontWeight="700" textAnchor="middle" letterSpacing="0.8">
                MAP / GPS VIEW
              </text>
            </svg>
          </div>

          {/* Bottom GPS Metrics Row */}
          <div className="ct-fw-gps-metrics-row">
            <div className="ct-fw-metric-col">
              <span className="ct-fw-metric-label">Current GPS accuracy</span>
              <span className="ct-fw-metric-val ct-fw-val-success">{accuracy}</span>
            </div>

            <div className="ct-fw-metric-col">
              <span className="ct-fw-metric-label">Distance to incident pin</span>
              <span className="ct-fw-metric-val ct-fw-val-success">{locationChecks.distance}</span>
            </div>

            <div className="ct-fw-metric-col ct-fw-metric-col-coords">
              <span className="ct-fw-metric-label">
                Coordinates {isSimulated && <span className="ct-fw-sim-tag">(Simulated)</span>}
              </span>
              <span className="ct-fw-metric-val">{coords}</span>
            </div>
          </div>
        </div>

        {/* Right Card: Location checks */}
        <div className="ct-fw-card ct-fw-location-checks-card">
          <div className="ct-fw-checks-header">
            <span className="ct-fw-card-header-label">Location checks</span>
            <span className="ct-fw-gps-locked-badge">
              {locationChecks.gpsStatus}
            </span>
          </div>

          <div className="ct-fw-checks-list">
            <div className="ct-fw-check-item">
              <span className="ct-fw-check-label">Ward match</span>
              <span className="ct-fw-check-val ct-fw-val-success">
                {locationChecks.wardMatch}
              </span>
            </div>

            <div className="ct-fw-check-item">
              <span className="ct-fw-check-label">Incident pin</span>
              <span className="ct-fw-check-val ct-fw-val-success">
                {locationChecks.incidentPin}
              </span>
            </div>

            <div className="ct-fw-check-item">
              <span className="ct-fw-check-label">Field boundary</span>
              <span className="ct-fw-check-val">
                {locationChecks.fieldBoundary}
              </span>
            </div>
          </div>

          <div className="ct-fw-checks-footer">
            <button
              type="button"
              className={`ct-fw-confirm-location-btn ${isConfirmed ? 'confirmed' : ''}`}
              onClick={handleConfirmLocation}
            >
              {isConfirmed ? (
                <>
                  <CheckCircle size={18} />
                  <span>Location Confirmed</span>
                </>
              ) : (
                <span>Confirm Location</span>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default FieldWorkerLocationPage;
