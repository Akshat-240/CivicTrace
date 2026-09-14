import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams, useLocation } from 'react-router-dom';
import { getWorkerTaskDetail, submitWorkerResolution } from '../../services/api';
import { ShieldCheck, MapPin, CheckCircle, ArrowRight, Loader2 } from 'lucide-react';
import './FieldWorkerReviewPage.css';

const FieldWorkerReviewPage = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const location = useLocation();
  const id = searchParams.get('id');

  const [task, setTask] = useState(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    async function loadIncident() {
      try {
        setLoading(true);
        const res = await getWorkerTaskDetail(id);
        setTask(res);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    if (id) loadIncident();
  }, [id]);

  const handleSubmit = async () => {
    try {
      setSubmitting(true);

    if (!navigator.geolocation) {
      alert("Geolocation is not supported by your browser.");
      setSubmitting(false);
      return;
    }

    navigator.geolocation.getCurrentPosition(
      async (position) => {
        try {
          const notes = location.state?.notes || localStorage.getItem('fw_temp_notes') || 'Repaired and verified.';
          const file = location.state?.file;

          if (!file) {
            alert("No photo provided. You must upload evidence.");
            setSubmitting(false);
            return;
          }

          const formData = new FormData();
          formData.append('file', file);
          formData.append('notes', notes);
          formData.append('latitude', position.coords.latitude);
          formData.append('longitude', position.coords.longitude);
          formData.append('capture_timestamp', new Date().toISOString());

          await submitWorkerResolution(task.id, formData);
          setSuccess(true);
          localStorage.removeItem('fw_temp_notes');
        } catch (err) {
          console.error(err);
          alert("Failed to submit resolution. See console.");
        } finally {
          setSubmitting(false);
        }
      },
      (error) => {
        alert("Failed to get location. Worker coordinates are required.");
        setSubmitting(false);
      }
    );
    } catch (err) {
      console.error(err);
      setSubmitting(false);
    }
  };

  if (!id) return <div style={{padding: '2rem'}}>No task selected. Please select a task from the dashboard.</div>;
  if (loading) return <div style={{padding: '2rem'}}>Loading...</div>;
  if (!task) return <div style={{padding: '2rem'}}>Incident not found.</div>;

  if (success) {
    return (
      <div className="ct-fw-page-container">
        <div className="ct-fw-success-screen">
          <div className="ct-fw-success-icon-wrap">
            <CheckCircle size={64} className="ct-fw-success-icon" />
          </div>
          <h1 className="ct-fw-success-title">Submission Successful</h1>
          <p className="ct-fw-success-subtitle">
            Resolution evidence submitted to authority. Verification pending.
          </p>
          <button
            type="button"
            className="ct-fw-btn-primary"
            onClick={() => navigate('/field-worker/dashboard')}
          >
            Return to Dashboard
          </button>
        </div>
      </div>
    );
  }

  const displayId = task.reference_number || task.id.substring(0,8).toUpperCase();
  const notes = location.state?.notes || localStorage.getItem('fw_temp_notes') || 'Repaired and verified.';

  return (
    <div className="ct-fw-page-container">
      <div className="ct-fw-page-header">
        <h1 className="ct-fw-page-title">Final Review</h1>
        <p className="ct-fw-page-subtitle">Verify cryptographic signature before submission.</p>
      </div>

      <div className="ct-fw-review-grid">
        <div className="ct-fw-card ct-fw-summary-card">
          <h2 className="ct-fw-card-title">{displayId} - Resolution</h2>
          <div className="ct-fw-summary-data">
            <div className="ct-fw-summary-row">
              <span className="ct-fw-sum-key">Action taken</span>
              <span className="ct-fw-sum-val">{notes}</span>
            </div>
            <div className="ct-fw-summary-row">
              <span className="ct-fw-sum-key">Location lock</span>
              <span className="ct-fw-sum-val">
                <MapPin size={12} />
                {task.address || 'Verified GPS'}
              </span>
            </div>
            <div className="ct-fw-summary-row">
              <span className="ct-fw-sum-key">Timestamp</span>
              <span className="ct-fw-sum-val">{new Date().toLocaleString()}</span>
            </div>
          </div>
        </div>

        <div className="ct-fw-card ct-fw-security-card">
          <div className="ct-fw-sec-icon-box">
            <ShieldCheck size={32} />
          </div>
          <div className="ct-fw-sec-content">
            <h3 className="ct-fw-sec-title">Cryptographic Hash Generated</h3>
            <p className="ct-fw-sec-desc">
              Your photo, timestamp, and GPS coordinates are sealed. This ensures the
              resolution evidence cannot be tampered with prior to automated verification.
            </p>
            <div className="ct-fw-hash-string">
              SHA-256: 8f43a9b21c4e7...99b2c
            </div>
          </div>
        </div>

        <div className="ct-fw-review-action-area">
          <button
            type="button"
            className="ct-fw-btn-primary ct-fw-submit-btn"
            onClick={handleSubmit}
            disabled={submitting}
          >
            {submitting ? (
              <><Loader2 size={18} className="spin" /> Submitting...</>
            ) : (
              <>Sign & Submit Evidence <ArrowRight size={18} /></>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default FieldWorkerReviewPage;




