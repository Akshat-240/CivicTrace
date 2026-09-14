import React from 'react';
import './Badges.css';

const PriorityBadge = ({ priority, variant = 'pill' }) => {
  const norm = priority?.toUpperCase() || 'MEDIUM';

  if (variant === 'text') {
    return <span className={`ct-priority-text ct-priority-${norm.toLowerCase()}`}>{norm}</span>;
  }

  return (
    <span className={`ct-priority-pill ct-pill-${norm.toLowerCase()}`}>
      {norm}
    </span>
  );
};

export default PriorityBadge;
