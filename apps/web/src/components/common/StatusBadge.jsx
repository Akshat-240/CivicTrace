import React from 'react';
import './Badges.css';

const StatusBadge = ({ status }) => {
  return (
    <span className="ct-status-badge">
      {status}
    </span>
  );
};

export default StatusBadge;
