import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';

// Public Pages
import LandingPage from '../pages/public/LandingPage';
import LoginPage from '../pages/public/LoginPage';

// Authority Portal
import AuthorityLayout from '../components/layout/AuthorityLayout';
import DashboardPage from '../pages/authority/DashboardPage';
import IncidentsPage from '../pages/authority/IncidentsPage';
import AssignmentPage from '../pages/authority/AssignmentPage';
import LiveMapPage from '../pages/authority/LiveMapPage';
import VerificationPage from '../pages/authority/VerificationPage';
import SettingsPage from '../pages/authority/SettingsPage';

// Admin Portal
import AdminLayout from '../components/layout/AdminLayout';
import AdminDashboardPage from '../pages/admin/AdminDashboardPage';
import AdminIncidentsPage from '../pages/admin/AdminIncidentsPage';
import AdminIncidentDetailPage from '../pages/admin/AdminIncidentDetailPage';
import AdminMapPage from '../pages/admin/AdminMapPage';
import AdminAnalysisPage from '../pages/admin/AdminAnalysisPage';
import AdminSLAMonitoringPage from '../pages/admin/AdminSLAMonitoringPage';
import AdminDepartmentPage from '../pages/admin/AdminDepartmentPage';
import AdminGovernancePage from '../pages/admin/AdminGovernancePage';
import AdminSettingsPage from '../pages/admin/AdminSettingsPage';

// Citizen Portal
import CitizenLayout from '../components/layout/CitizenLayout';
import CitizenDashboardPage from '../pages/citizen/CitizenDashboardPage';
import CitizenReportPage from '../pages/citizen/CitizenReportPage';
import CitizenTrackPage from '../pages/citizen/CitizenTrackPage';
import CitizenHistoryPage from '../pages/citizen/CitizenHistoryPage';
import CitizenFeedbackPage from '../pages/citizen/CitizenFeedbackPage';
import CitizenSettingsPage from '../pages/citizen/CitizenSettingsPage';

// Field Worker Portal
import FieldWorkerLayout from '../components/layout/FieldWorkerLayout';
import FieldWorkerDashboardPage from '../pages/field-worker/FieldWorkerDashboardPage';
import FieldWorkerIncidentPage from '../pages/field-worker/FieldWorkerIncidentPage';
import FieldWorkerLocationPage from '../pages/field-worker/FieldWorkerLocationPage';
import FieldWorkerEvidencePage from '../pages/field-worker/FieldWorkerEvidencePage';
import FieldWorkerReviewPage from '../pages/field-worker/FieldWorkerReviewPage';

const AppRoutes = () => {
  return (
    <Routes>
      {/* Public Routes */}
      <Route path="/" element={<LandingPage />} />
      <Route path="/login" element={<LoginPage />} />

      {/* Authority Portal Routes */}
      <Route path="/authority" element={<AuthorityLayout />}>
        <Route index element={<Navigate to="dashboard" replace />} />
        <Route path="dashboard" element={<DashboardPage />} />
        <Route path="incidents" element={<IncidentsPage />} />
        <Route path="assignment" element={<AssignmentPage />} />
        <Route path="map" element={<LiveMapPage />} />
        <Route path="verification" element={<VerificationPage />} />
        <Route path="settings" element={<SettingsPage />} />
      </Route>

      {/* Admin Portal Routes */}
      <Route path="/admin" element={<AdminLayout />}>
        <Route index element={<Navigate to="dashboard" replace />} />
        <Route path="dashboard" element={<AdminDashboardPage />} />
        <Route path="incidents" element={<AdminIncidentsPage />} />
        <Route path="incidents/:id" element={<AdminIncidentDetailPage />} />
        <Route path="map" element={<AdminMapPage />} />
        <Route path="analysis" element={<AdminAnalysisPage />} />
        <Route path="sla" element={<AdminSLAMonitoringPage />} />
        <Route path="departments" element={<AdminDepartmentPage />} />
        <Route path="governance" element={<AdminGovernancePage />} />
        <Route path="settings" element={<AdminSettingsPage />} />
      </Route>

      {/* Citizen Portal Routes */}
      <Route path="/citizen" element={<CitizenLayout />}>
        <Route index element={<Navigate to="dashboard" replace />} />
        <Route path="dashboard" element={<CitizenDashboardPage />} />
        <Route path="report" element={<CitizenReportPage />} />
        <Route path="track" element={<CitizenTrackPage />} />
        <Route path="track/:id" element={<CitizenTrackPage />} />
        <Route path="history" element={<CitizenHistoryPage />} />
        <Route path="feedback" element={<CitizenFeedbackPage />} />
        <Route path="feedback/:id" element={<CitizenFeedbackPage />} />
        <Route path="settings" element={<CitizenSettingsPage />} />
      </Route>

      {/* Field Worker Portal Routes */}
      <Route path="/field-worker" element={<FieldWorkerLayout />}>
        <Route index element={<Navigate to="dashboard" replace />} />
        <Route path="dashboard" element={<FieldWorkerDashboardPage />} />
        <Route path="tasks/:id" element={<FieldWorkerIncidentPage />} />
        <Route path="location" element={<FieldWorkerLocationPage />} />
        <Route path="evidence" element={<FieldWorkerEvidencePage />} />
        <Route path="review" element={<FieldWorkerReviewPage />} />
      </Route>

      {/* Fallback */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
};

export default AppRoutes;
