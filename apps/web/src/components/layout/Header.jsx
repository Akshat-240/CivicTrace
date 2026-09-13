import React from 'react';
import { useLocation } from 'react-router-dom';
import { Bell, MapPin } from 'lucide-react';
import './Header.css';

const Header = () => {
  const location = useLocation();
  
  const getPageTitle = () => {
    const path = location.pathname;
    if (path.includes('dashboard')) return 'Dashboard Overview';
    if (path.includes('incidents')) return 'Incident Management';
    if (path.includes('assignment')) return 'Officer Assignment';
    if (path.includes('map')) return 'Live Monitor';
    if (path.includes('verification')) return 'Incident Verification';
    if (path.includes('settings')) return 'Authority Settings';
    return 'Authority Portal';
  };

  return (
    <header className="header">
      <div className="header-left">
        <h1 className="page-title">{getPageTitle()}</h1>
      </div>
      
      <div className="header-right">
        <div className="location-context">
          <MapPin size={16} className="context-icon" />
          <span className="context-text">LMC Civil · Lucknow</span>
        </div>
        
        <button className="notification-btn">
          <Bell size={20} />
          <span className="notification-badge"></span>
        </button>
      </div>
    </header>
  );
};

export default Header;
