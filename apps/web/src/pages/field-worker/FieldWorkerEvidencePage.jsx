import React, { useState, useRef, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { getIncident } from '../../services/api';
import { Camera, Upload, ArrowRight, CheckCircle2 } from 'lucide-react';
import './FieldWorkerEvidencePage.css';

const FieldWorkerEvidencePage = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const id = searchParams.get('id');
  
  const [task, setTask] = useState(null);
  const [loading, setLoading] = useState(true);

  const [capturedImage, setCapturedImage] = useState(null);
  const [notes, setNotes] = useState("");
  const fileInputRef = useRef(null);

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

  const handleCaptureClick = () => {
    // In a real mobile web app, this might trigger the device camera.
    // We simulate by clicking a hidden file input.
    fileInputRef.current?.click();
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      const url = URL.createObjectURL(file);
      setCapturedImage(url);
    }
  };

  const handleSimulateCapture = () => {
    // Demo fallback: just set a solid grey block if they don't upload a file
    setCapturedImage("data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIzMDAiIGhlaWdodD0iMjAwIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjNDc1NTY5Ii8+PHRleHQgeD0iNTAlIiB5PSI1MCUiIGZpbGw9IiNmZmYiIGZvbnQtZmFtaWx5PSJzYW5zLXNlcmlmIiBmb250LXNpemU9IjI0IiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBkeT0iLjNlbSI+Q2FwdHVyZWQgUGhvdG88L3RleHQ+PC9zdmc+");
  };

  const handleContinue = () => {
    // Pass notes via local storage or state. Let's just use local storage for demo to avoid complex context setup.
    if (notes) localStorage.setItem('fw_temp_notes', notes);
    navigate(`/field-worker/review?id=${id}`);
  };

  if (loading) return <div style={{padding: '2rem'}}>Loading...</div>;
  if (!task) return <div style={{padding: '2rem'}}>Incident not found.</div>;

  return (
    <div className="ct-fw-page-container">
      <div className="ct-fw-page-header">
        <h1 className="ct-fw-page-title">Capture Resolution</h1>
        <p className="ct-fw-page-subtitle">Submit proof of completed work.</p>
      </div>

      <div className="ct-fw-evidence-grid">
        <div className="ct-fw-card ct-fw-camera-card">
          <div className="ct-fw-card-header-label">Resolution Photo</div>
          
          <div className="ct-fw-camera-viewport">
            {capturedImage ? (
              <div className="ct-fw-captured-preview">
                <img src={capturedImage} alt="Captured resolution" />
                <button 
                  type="button"
                  className="ct-fw-retake-btn"
                  onClick={() => setCapturedImage(null)}
                >
                  Retake Photo
                </button>
              </div>
            ) : (
              <div className="ct-fw-camera-ui">
                <div className="ct-fw-viewfinder-frame"></div>
                <div className="ct-fw-camera-instructions">
                  Align completed work within frame
                </div>
              </div>
            )}
          </div>

          {!capturedImage && (
            <div className="ct-fw-camera-controls">
              <input 
                type="file" 
                accept="image/*" 
                capture="environment" 
                ref={fileInputRef}
                style={{ display: 'none' }}
                onChange={handleFileChange}
              />
              <button className="ct-fw-icon-btn outline" onClick={handleSimulateCapture}>
                <Upload size={20} />
              </button>
              <button className="ct-fw-capture-shutter" onClick={handleCaptureClick}>
                <div className="ct-fw-shutter-inner"></div>
              </button>
              <button className="ct-fw-icon-btn empty" disabled></button>
            </div>
          )}

          {capturedImage && (
            <div className="ct-fw-gps-stamp-row">
              <CheckCircle2 size={14} className="ct-fw-highlight-green" />
              <span>Location metadata matched to assignment coordinates.</span>
            </div>
          )}
        </div>

        <div className="ct-fw-card ct-fw-evidence-form-card">
          <div className="ct-fw-card-header-label">Field Notes</div>
          
          <div className="ct-fw-form-group">
            <label className="ct-fw-form-label">Material & Action Summary</label>
            <textarea 
              className="ct-fw-form-textarea"
              placeholder="e.g. Filled pothole with 2 bags of cold-mix asphalt and leveled surface."
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
            ></textarea>
          </div>

          <div className="ct-fw-evidence-action-area">
            <button 
              type="button" 
              className="ct-fw-continue-btn"
              disabled={!capturedImage}
              onClick={handleContinue}
            >
              <span>Review Submission</span>
              <ArrowRight size={16} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default FieldWorkerEvidencePage;
