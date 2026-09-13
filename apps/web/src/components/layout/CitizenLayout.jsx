import React from 'react';
import { Outlet, useLocation, useNavigate } from 'react-router-dom';
import CitizenSidebar from './CitizenSidebar';
import { MapPin, Plus } from 'lucide-react';
import './CitizenLayout.css';

const CitizenLayout = () => {
  const location = useLocation();
  const navigate = useNavigate();

  const getHeaderInfo = () => {
    const path = location.pathname;
    if (path.includes('/citizen/dashboard')) {
      return {
        title: 'Welcome back, Citizen',
        subtitle: 'Stay informed about the civic issues you have reported.',
        showReportBtn: true
      };
    }
    if (path.includes('/citizen/report')) {
      return {
        title: 'Report a Civic Issue',
        subtitle: 'A simple guided flow — CivicTrace handles routing and verification.',
        showReportBtn: false
      };
    }
    if (path.includes('/citizen/track')) {
      return {
        title: 'Track Your Report',
        subtitle: 'See exactly what is happening to your civic issue.',
        showReportBtn: false
      };
    }
    if (path.includes('/citizen/history')) {
      return {
        title: 'Past Incidents',
        subtitle: 'View the civic issues you have previously reported.',
        showReportBtn: false
      };
    }
    if (path.includes('/citizen/feedback')) {
      return {
        title: 'Your Feedback',
        subtitle: 'Help us confirm whether civic issues were actually resolved.',
        showReportBtn: false
      };
    }
    if (path.includes('/citizen/settings')) {
      return {
        title: 'Settings',
        subtitle: 'Manage your account, notifications, location and privacy preferences.',
        showReportBtn: false
      };
    }
    return {
      title: 'Citizen Portal',
      subtitle: 'Civic issue reporting, telemetry and resolution tracking.',
      showReportBtn: false
    };
  };

  const headerInfo = getHeaderInfo();

  return (
    <div className="ct-citizen-app-container">
      <CitizenSidebar />
      <div className="ct-citizen-main-wrapper">
        <header className="ct-citizen-header">
          <div className="ct-citizen-header-left">
            <h1 className="ct-citizen-header-title">{headerInfo.title}</h1>
            <p className="ct-citizen-header-subtitle">{headerInfo.subtitle}</p>
          </div>

          <div className="ct-citizen-header-right">
            <div className="ct-citizen-location-pill">
              <div className="ct-location-title-row">
                <MapPin size={13} className="ct-loc-pin-icon" />
                <span className="ct-location-text">Lucknow · Your area</span>
              </div>
              <div className="ct-location-status-row">
                <span className="ct-loc-green-dot"></span>
                <span className="ct-location-subtext">Location services active</span>
              </div>
            </div>

            {headerInfo.showReportBtn && (
              <button 
                type="button" 
                className="ct-header-report-btn"
                onClick={() => navigate('/citizen/report')}
              >
                <Plus size={16} />
                <span>Report a Civic Issue</span>
              </button>
            )}
          </div>
        </header>

        <main className="ct-citizen-content">
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export default CitizenLayout;
