import React from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import './AuthorityLayout.css';

const AuthorityLayout = () => {
  return (
    <div className="ct-app-layout">
      <Sidebar />
      <main className="ct-main-content">
        <div className="ct-content-inner">
          <Outlet />
        </div>
      </main>
    </div>
  );
};

export default AuthorityLayout;
