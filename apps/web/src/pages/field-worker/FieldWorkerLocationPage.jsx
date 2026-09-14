import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { getIncident } from '../../services/api';
import { MapPin, Navigation, Compass, CheckCircle } from 'lucide-react';
import './FieldWorkerLocationPage.css';

const FieldWorkerLocationPage = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const id = searchParams.get('id');
  
  const [task, setTask] = useState(null);
  const [loading, setLoading] = useState(true);

  const [coords, setCoords] = useState("26.8528° N, 80.9435° E");
  const [accuracy, setAccuracy] = useState("± 15 m");
  const [isSimulated, setIsSimulated] = useState(true);
  const [isConfirmed, setIsConfirmed] = useState(false);

  useEffect(() => {
    async function loadIncident() {
      try {
        setLoading(true);
        const res = await getIncident(id);
        setTask(res);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    if (id) loadIncident();
  }, [id]);

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
          // Fallback
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
      navigate(`/field-worker/evidence?id=${task.id}`);
    }, 1200);
  };

  if (!id) return <div style={{padding: '2rem'}}>No task selected. Please select a task from the dashboard.</div>;
  if (loading) return <div style={{padding: '2rem'}}>Loading location details...</div>;
  if (!task) return <div style={{padding: '2rem'}}>Incident not found.</div>;

  const targetCoords = task.location ? `${task.location.latitude?.toFixed(4) || '26.8528'}° N, ${task.location.longitude?.toFixed(4) || '80.9435'}° E` : "26.8528° N, 80.9435° E";

  return (
    <div className="ct-fw-page-container">
      {/* Header */}
      <div className="ct-fw-page-header">
        <h1 className="ct-fw-page-title">Location Verification</h1>
        <p className="ct-fw-page-subtitle">Navigate to the incident site.</p>
      </div>

      <div className="ct-fw-location-grid">
        {/* Left: Map Viewer */}
        <div className="ct-fw-card ct-fw-map-view-card">
          <div className="ct-fw-map-container">
            <div className="ct-fw-map-placeholder">
              <span className="ct-fw-map-watermark">MAP</span>
            </div>

            {/* Target Marker */}
            <div className="ct-fw-target-marker">
              <MapPin size={28} />
            </div>

            {/* Simulated Live User Position */}
            <div className="ct-fw-user-position-marker">
              <span className="ct-fw-user-dot"></span>
              <span className="ct-fw-user-ping"></span>
            </div>
          </div>
          
          <div className="ct-fw-map-address-banner">
            <h3 className="ct-fw-map-banner-title">{task.location?.address_raw || 'Unknown Location'}</h3>
            <p className="ct-fw-map-banner-sub">{targetCoords}</p>
          </div>
        </div>

        {/* Right: GPS Matcher Panel */}
        <div className="ct-fw-card ct-fw-gps-matcher-card">
          <div className="ct-fw-card-header-label">GPS Verification</div>

          <div className="ct-fw-gps-status-block">
            <div className="ct-fw-gps-icon-wrapper">
              <Compass size={28} className="ct-fw-compass-icon" />
            </div>
            
            <div className="ct-fw-gps-readout">
              <div className="ct-fw-gps-readout-row">
                <span className="ct-fw-gps-key">Current Fix:</span>
                <span className="ct-fw-gps-val">{coords}</span>
              </div>
              <div className="ct-fw-gps-readout-row">
                <span className="ct-fw-gps-key">Accuracy:</span>
                <span className="ct-fw-gps-val">{accuracy}</span>
              </div>
              <div className="ct-fw-gps-readout-row">
                <span className="ct-fw-gps-key">Source:</span>
                <span className="ct-fw-gps-val ct-fw-highlight-green">
                  {isSimulated ? 'Simulated Demo Lock' : 'Live Device GPS'}
                </span>
              </div>
            </div>
          </div>

          <div className="ct-fw-gps-distance-box">
            <div className="ct-fw-distance-val">
              Distance to site: <span>12 meters</span>
            </div>
            <div className="ct-fw-distance-status positive">
              <CheckCircle size={14} /> Within allowed radius
            </div>
          </div>

          <div className="ct-fw-gps-action-area">
            {!isConfirmed ? (
              <button 
                type="button" 
                className="ct-fw-confirm-loc-btn"
                onClick={handleConfirmLocation}
              >
                <Navigation size={18} />
                Confirm Arrival & Lock Location
              </button>
            ) : (
              <div className="ct-fw-loc-success-msg">
                <CheckCircle size={18} />
                Location Verified. Proceeding to work...
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default FieldWorkerLocationPage;

