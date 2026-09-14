import React from 'react';
import './PageHeader.css';

const PageHeader = ({ title, subtitle, rightContext = "LMC Civil · Lucknow", rightSub = "Authority operations" }) => {
  return (
    <div className="ct-page-header">
      <div className="ct-header-left">
        <h1 className="ct-page-title">{title}</h1>
        {subtitle && <p className="ct-page-subtitle">{subtitle}</p>}
      </div>
      <div className="ct-header-right">
        <div className="ct-authority-label">{rightContext}</div>
        <div className="ct-authority-sub">{rightSub}</div>
      </div>
    </div>
  );
};

export default PageHeader;
