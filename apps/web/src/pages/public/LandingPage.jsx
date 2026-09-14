import React from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowRight, Play, Shield, CheckCircle2, Zap, Star } from 'lucide-react';
import './LandingPage.css';

const LandingPage = () => {
  const navigate = useNavigate();

  return (
    <div className="ct-landing-wrapper">
      {/* Top Navbar */}
      <header className="ct-landing-nav">
        <div className="ct-landing-brand" onClick={() => navigate('/')}>
          <div className="ct-landing-logo-dot"></div>
          <span className="ct-landing-brand-text">CivicTrace</span>
        </div>

        <nav className="ct-landing-nav-links">
          <a href="#home" className="ct-nav-anchor active">Home</a>
          <a href="#about" className="ct-nav-anchor">About</a>
          <a href="#impact" className="ct-nav-anchor">Impact</a>
          <button 
            type="button" 
            className="ct-nav-anchor-btn"
            onClick={() => navigate('/citizen/dashboard')}
          >
            For Citizens
          </button>
          <button 
            type="button" 
            className="ct-nav-anchor-btn"
            onClick={() => navigate('/authority/dashboard')}
          >
            For Authorities
          </button>
        </nav>

        <div className="ct-landing-nav-actions">
          <button 
            type="button" 
            className="ct-landing-login-btn"
            onClick={() => navigate('/login')}
          >
            Login
          </button>
        </div>
      </header>

      {/* Hero Section */}
      <main className="ct-landing-hero">
        {/* Star dots particles */}
        <div className="ct-hero-star-particles" aria-hidden="true">
          <span className="ct-star" style={{ top: '25%', left: '42%' }}></span>
          <span className="ct-star" style={{ top: '48%', left: '40%' }}></span>
          <span className="ct-star" style={{ top: '75%', left: '44%' }}></span>
          <span className="ct-star" style={{ top: '35%', left: '78%' }}></span>
          <span className="ct-star" style={{ top: '55%', left: '85%' }}></span>
          <span className="ct-star" style={{ top: '70%', left: '75%' }}></span>
          <span className="ct-star" style={{ top: '82%', left: '88%' }}></span>
        </div>

        <div className="ct-hero-content">
          <div className="ct-hero-badge">
            <span>ACCOUNTABILITY IN ACTION</span>
          </div>

          <h1 className="ct-hero-title">
            Cleaner Cities.<br />
            Stronger Trust.
          </h1>

          <p className="ct-hero-desc">
            From Complaints to change — with evidence.
            CivicTrace uses AI and geospatial intelligence to ensure every civic
            issue is not just reported, but actually resolved.
          </p>

          <div className="ct-hero-actions">
            <button 
              type="button" 
              className="ct-hero-btn-primary"
              onClick={() => navigate('/admin/dashboard')}
            >
              <span>Explore Admin Portal</span>
              <ArrowRight size={18} />
            </button>

            <button 
              type="button" 
              className="ct-hero-btn-secondary"
              onClick={() => navigate('/authority/dashboard')}
            >
              <Play size={16} fill="currentColor" />
              <span>Authority Demo</span>
            </button>
          </div>
        </div>

        {/* Right floating decorative typography */}
        <div className="ct-hero-aside-text">
          <span>Better</span>
          <span>Cities</span>
          <span>Brighter</span>
          <span>Tomorrows</span>
        </div>

        {/* Bottom Metrics Bar */}
        <div className="ct-hero-metrics-bar">
          <div className="ct-metric-col">
            <span className="ct-metric-number">12,480</span>
            <span className="ct-metric-label">Issues Reported</span>
          </div>

          <div className="ct-metric-col">
            <span className="ct-metric-number">9,320</span>
            <span className="ct-metric-label">Resolved with Evidence</span>
          </div>

          <div className="ct-metric-col">
            <span className="ct-metric-number">28%</span>
            <span className="ct-metric-label">Faster Response</span>
          </div>

          <div className="ct-metric-col">
            <span className="ct-metric-number">4.8/5</span>
            <span className="ct-metric-label">Citizen Satisfaction</span>
          </div>
        </div>
      </main>
    </div>
  );
};

export default LandingPage;
