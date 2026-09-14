import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Shield, ArrowRight, Loader2, AlertTriangle } from 'lucide-react';
import { fetchAPI } from '../../services/api';
import './LoginPage.css';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL !== undefined ? import.meta.env.VITE_API_BASE_URL : '';

const LoginPage = () => {
  const navigate = useNavigate();
  const [selectedRole, setSelectedRole] = useState('Citizen');
  const [email, setEmail] = useState('citizen@demo.local');
  const [password, setPassword] = useState('citizen123');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    const token = localStorage.getItem('ct_auth_token');
    const role = localStorage.getItem('ct_user_role');
    if (token && role) {
      if (role === 'admin') {
        navigate('/admin/dashboard');
      } else if (role === 'authority') {
        navigate('/authority/dashboard');
      } else if (role === 'field_worker') {
        navigate('/field-worker/dashboard');
      } else {
        navigate('/citizen/dashboard');
      }
    }
  }, [navigate]);

  const handleRoleChange = (role) => {
    setSelectedRole(role);
    if (role === 'Admin') {
      setEmail('admin@demo.local');
      setPassword('admin123');
    } else if (role === 'Authority') {
      setEmail('authority@demo.local');
      setPassword('authority123');
    } else if (role === 'Field Worker') {
      setEmail('worker@demo.local');
      setPassword('worker123');
    } else {
      setEmail('citizen@demo.local');
      setPassword('citizen123');
    }
  };

  const parseJwt = (token) => {
    try {
      return JSON.parse(atob(token.split('.')[1]));
    } catch (e) {
      return null;
    }
  };

  const handleSignIn = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    const formData = new URLSearchParams();
    formData.append('username', email);
    formData.append('password', password);

    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/auth/token`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: formData.toString()
      });

      if (!response.ok) {
        let errorMsg = 'Invalid credentials';
        try {
          const errData = await response.json();
          errorMsg = errData.detail || errorMsg;
        } catch (e) {}
        throw new Error(errorMsg);
      }

      const data = await response.json();
      const token = data.access_token;

      const payload = parseJwt(token);
      if (!payload) throw new Error('Invalid token received from server');

      const role = (payload.role || 'citizen').toLowerCase();
      const userId = payload.sub;

      localStorage.setItem('ct_auth_token', token);
      localStorage.setItem('ct_user_id', userId);
      localStorage.setItem('ct_user_role', role);

      if (role === 'admin') {
        navigate('/admin/dashboard');
      } else if (role === 'authority') {
        navigate('/authority/dashboard');
      } else if (role === 'field_worker') {
        navigate('/field-worker/dashboard');
      } else {
        navigate('/citizen/dashboard');
      }
    } catch (err) {
      setError(err.message || 'Login failed. Please check your credentials.');
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
            A cleaner, safer, more accountable city starts with you.
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

          <h1 className="ct-login-title">Welcome Back</h1>
          <p className="ct-login-desc">Sign in to continue to CivicTrace</p>

          {/* Role selector tabs */}
          <div className="ct-login-role-tabs">
            {['Authority', 'Field Worker', 'Citizen', 'Admin'].map((role) => (
              <button
                key={role}
                type="button"
                className={`ct-role-tab ${selectedRole === role ? 'active' : ''}`}
                onClick={() => handleRoleChange(role)}
              >
                {role}
              </button>
            ))}
          </div>

          <form onSubmit={handleSignIn} className="ct-login-form">
            {error && (
              <div style={{ backgroundColor: '#fee2e2', color: '#b91c1c', padding: '0.75rem', borderRadius: '8px', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.85rem' }}>
                <AlertTriangle size={16} />
                <span>{error}</span>
              </div>
            )}

            <div className="ct-form-group">
              <label htmlFor="email" className="ct-form-label">
                {selectedRole === 'Citizen' ? 'Email' : 'Email'}
              </label>
              <input
                id="email"
                type="text"
                className="ct-form-input"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>

            <div className="ct-form-group">
              <div className="ct-label-row">
                <label htmlFor="password" className="ct-form-label">Password</label>
                <a href="#forgot" className="ct-forgot-link">Forgot password?</a>
              </div>
              <input
                id="password"
                type="password"
                className="ct-form-input"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>

            <button type="submit" className="ct-login-submit-btn" disabled={loading} style={{ opacity: loading ? 0.7 : 1, cursor: loading ? 'not-allowed' : 'pointer', display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '0.5rem' }}>
              {loading ? <Loader2 size={18} className="animate-spin" /> : null}
              <span>{loading ? 'Signing In...' : 'Sign In'}</span>
            </button>

            <div className="ct-login-divider">
              <span>or</span>
            </div>

            <button
              type="button"
              className="ct-sso-btn"
              onClick={handleSignIn}
            >
              <span className="ct-sso-emblem"></span>
              <span>Continue with Government SSO</span>
            </button>
          </form>

          {selectedRole === 'Authority' ? (
            <div className="ct-login-footer-hint">
              New here? <a href="#" onClick={(e) => { e.preventDefault(); navigate('/register?role=authority'); }}>Create an authority account</a>
            </div>
          ) : selectedRole === 'Field Worker' ? (
            <div className="ct-login-footer-hint">
              New here? <a href="#" onClick={(e) => { e.preventDefault(); navigate('/register?role=field_worker'); }}>Create a field worker account</a>
            </div>
          ) : selectedRole === 'Citizen' ? (
            <div className="ct-login-footer-hint">
              New here? <a href="#" onClick={(e) => { e.preventDefault(); navigate('/register'); }}>Create a citizen account</a>
            </div>
          ) : selectedRole === 'Admin' ? (
            <div className="ct-login-footer-hint">
              New here? <a href="#" onClick={(e) => { e.preventDefault(); navigate('/register?role=admin'); }}>Create an admin account</a>
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
