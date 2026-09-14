import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Loader2, AlertTriangle, CheckCircle } from 'lucide-react';
import { registerCitizen, getAuthorities } from '../../services/api';
import './LoginPage.css'; // Re-use styling

const RegisterPage = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const queryParams = new URLSearchParams(location.search);
  const roleParam = queryParams.get('role') || 'citizen';

  const [fullName, setFullName] = useState('');
  const [designation, setDesignation] = useState('');
  const [email, setEmail] = useState('');
  const [city, setCity] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);

  const [authorities, setAuthorities] = useState([]);
  const [authorityId, setAuthorityId] = useState('');

  useEffect(() => {
    if (roleParam === 'authority' || roleParam === 'field_worker') {
      getAuthorities().then(data => {
        if (data) {
          setAuthorities(data);
          if (data.length > 0) setAuthorityId(data[0].id);
        }
      }).catch(err => console.error("Failed to load authorities", err));
    }
  }, [roleParam]);

  useEffect(() => {
    // If logged in, redirect
    const token = localStorage.getItem('ct_auth_token');
    const role = localStorage.getItem('ct_user_role');
    if (token && role) {
      if (role === 'admin') navigate('/admin/dashboard');
      else if (role === 'authority') navigate('/authority/dashboard');
      else if (role === 'field_worker') navigate('/field-worker/dashboard');
      else navigate('/citizen/dashboard');
    }
  }, [navigate]);

  const handleRegister = async (e) => {
    e.preventDefault();
    setError(null);

    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    if (password.length < 6) {
      setError('Password must be at least 6 characters');
      return;
    }

    setLoading(true);

    try {
      const finalFullName = (roleParam === 'authority' || roleParam === 'field_worker') && designation
        ? `${fullName.trim()} - ${designation.trim()}`
        : fullName.trim();

      await registerCitizen({
        full_name: finalFullName,
        email: email.trim(),
        city: city.trim(),
        password,
        role: roleParam,
        authority_id: (roleParam === 'authority' || roleParam === 'field_worker') ? authorityId : null
      });
      setSuccess(true);
    } catch (err) {
      setError(err.message || 'Registration failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="ct-login-split-page">
      {/* Left Panel */}
      <div className="ct-login-left-panel">
        <div className="ct-login-left-brand" onClick={() => navigate('/')}>
          <div className="ct-login-brand-dot"></div>
          <span>CivicTrace</span>
        </div>

        {/* Decorative particles */}
        <div className="ct-login-particles">
          <span className="ct-login-star" style={{ top: '65%', left: '15%' }}></span>
          <span className="ct-login-star" style={{ top: '68%', left: '72%' }}></span>
          <span className="ct-login-star" style={{ top: '80%', left: '22%' }}></span>
          <span className="ct-login-star" style={{ top: '85%', left: '60%' }}></span>
          <span className="ct-login-star" style={{ top: '72%', left: '90%' }}></span>
        </div>

        <div className="ct-login-left-content">
          <div className="ct-login-accent-bar"></div>
          <h2 className="ct-login-hero-heading">
            Transparent<br />
            Governance<br />
            Stronger Communities
          </h2>
          <p className="ct-login-hero-subtext">
            Join CivicTrace and help make your city more accountable.
          </p>
        </div>

        <div className="ct-login-left-footer">
          <span>CivicTrace</span>
          <span>A Smarter Tomorrow</span>
        </div>
      </div>

      {/* Right Panel */}
      <div className="ct-login-right-panel">
        <div className="ct-login-card">
          <div className="ct-login-card-brand">
            <div className="ct-login-card-dot"></div>
            <span>CivicTrace</span>
          </div>

          <h1 className="ct-login-title">Create your account</h1>
          <p className="ct-login-desc">
            {roleParam === 'admin' ? 'Admin Registration' :
             roleParam === 'authority' ? 'Authority Registration' :
             roleParam === 'field_worker' ? 'Field Worker Registration' :
             'Citizen Registration'}
          </p>

          {success ? (
            <div style={{ textAlign: 'center', padding: '2rem 0' }}>
              <CheckCircle size={48} color="#10b981" style={{ margin: '0 auto 1rem auto' }} />
              <h2 style={{ fontSize: '1.25rem', marginBottom: '0.5rem', color: '#0F172A' }}>Account created successfully!</h2>
              <p style={{ color: '#64748B', marginBottom: '1.5rem' }}>You can now sign in with your new credentials.</p>
              <button
                className="ct-login-submit-btn"
                style={{ width: '100%' }}
                onClick={() => navigate('/login')}
              >
                Go to Sign In
              </button>
            </div>
          ) : (
            <form onSubmit={handleRegister} className="ct-login-form">
              {error && (
                <div style={{ backgroundColor: '#fee2e2', color: '#b91c1c', padding: '0.75rem', borderRadius: '8px', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.85rem' }}>
                  <AlertTriangle size={16} />
                  <span>{error}</span>
                </div>
              )}

              <div className="ct-form-group">
                <label htmlFor="fullName" className="ct-form-label">Full Name</label>
                <input
                  id="fullName"
                  type="text"
                  className="ct-form-input"
                  placeholder="Enter your full name"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  required
                />
              </div>

              {(roleParam === 'authority' || roleParam === 'field_worker') && (
                <div className="ct-form-group">
                  <label htmlFor="designation" className="ct-form-label">Role / Designation</label>
                  <select
                    id="designation"
                    className="ct-form-input"
                    value={designation}
                    onChange={(e) => setDesignation(e.target.value)}
                    required
                  >
                    <option value="" disabled>Select a role...</option>
                    <option value="Civic Operations Officer">Civic Operations Officer</option>
                    <option value="Field Inspector">Field Inspector</option>
                    <option value="Sanitation Worker">Sanitation Worker</option>
                    <option value="Traffic Enforcer">Traffic Enforcer</option>
                    <option value="General Authority">General Authority</option>
                    <option value="Department Head">Department Head</option>
                  </select>
                </div>
              )}

              <div className="ct-form-group">
                <label htmlFor="email" className="ct-form-label">Email</label>
                <input
                  id="email"
                  type="email"
                  className="ct-form-input"
                  placeholder="you@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
              </div>

              <div className="ct-form-group">
                <label htmlFor="city" className="ct-form-label">City</label>
                <input
                  id="city"
                  type="text"
                  className="ct-form-input"
                  placeholder="e.g. Lucknow"
                  value={city}
                  onChange={(e) => setCity(e.target.value)}
                  required
                />
              </div>

              {(roleParam === 'authority' || roleParam === 'field_worker') && (
                <div className="ct-form-group">
                  <label htmlFor="department" className="ct-form-label">Department / Authority</label>
                  <select
                    id="department"
                    className="ct-form-input"
                    value={authorityId}
                    onChange={(e) => setAuthorityId(e.target.value)}
                    required
                  >
                    {authorities.map(auth => (
                      <option key={auth.id} value={auth.id}>
                        {auth.name}
                      </option>
                    ))}
                  </select>
                </div>
              )}

              <div className="ct-form-group">
                <label htmlFor="password" className="ct-form-label">Password</label>
                <input
                  id="password"
                  type="password"
                  className="ct-form-input"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  minLength={6}
                />
              </div>

              <div className="ct-form-group">
                <label htmlFor="confirmPassword" className="ct-form-label">Confirm Password</label>
                <input
                  id="confirmPassword"
                  type="password"
                  className="ct-form-input"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  required
                  minLength={6}
                />
              </div>

              <button type="submit" className="ct-login-submit-btn" disabled={loading} style={{ opacity: loading ? 0.7 : 1, cursor: loading ? 'not-allowed' : 'pointer', display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '0.5rem' }}>
                {loading ? <Loader2 size={18} className="animate-spin" /> : null}
                <span>{loading ? 'Creating Account...' : 'Create Account'}</span>
              </button>
            </form>
          )}

          {!success && (
            <div className="ct-login-footer-hint">
              Already have an account? <a href="#" onClick={(e) => { e.preventDefault(); navigate('/login'); }}>Sign in</a>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default RegisterPage;
