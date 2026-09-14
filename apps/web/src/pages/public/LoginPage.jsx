import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Shield, ArrowRight } from 'lucide-react';
import './LoginPage.css';

const LoginPage = () => {
  const navigate = useNavigate();
  const [selectedRole, setSelectedRole] = useState('Admin');
  const [email, setEmail] = useState('admin@lucknow.gov.in');
  const [password, setPassword] = useState('••••••••••••');

  const handleRoleChange = (role) => {
    setSelectedRole(role);
    if (role === 'Admin') setEmail('admin@lucknow.gov.in');
    else if (role === 'Authority') setEmail('officer.roads@lucknow.gov.in');
    else if (role === 'Field Worker') setEmail('worker.1@lucknow.gov.in');
    else setEmail('citizen.lucknow@example.in');
  };

  const handleSignIn = (e) => {
    e.preventDefault();
    if (selectedRole === 'Admin') {
      navigate('/admin/dashboard');
    } else if (selectedRole === 'Authority') {
      navigate('/authority/dashboard');
    } else if (selectedRole === 'Field Worker') {
      navigate('/field-worker/dashboard');
    } else {
      navigate('/citizen/dashboard');
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
            <div className="ct-form-group">
              <label htmlFor="email" className="ct-form-label">
                {selectedRole === 'Citizen' ? 'Mobile Number or Email' : 'Email or Employee ID'}
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

            <button type="submit" className="ct-login-submit-btn">
              Sign In
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

          <div className="ct-login-footer-hint">
            New here? <a href="#support">Contact your administrator</a>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
