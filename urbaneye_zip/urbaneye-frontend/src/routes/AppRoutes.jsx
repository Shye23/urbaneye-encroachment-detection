import React from "react";
import {
  BrowserRouter,
  Routes,
  Route,
  Navigate,
} from "react-router-dom";

// Public
import Landing from "../pages/Landing";
import SignIn from "../pages/auth/SignIn";
import Register from "../pages/auth/Register";

// Citizen
import Overview from "../pages/citizen/Overview";
import ReportIssue from "../pages/citizen/ReportIssue";
import Track from "../pages/citizen/Track";
import Danger from "../pages/citizen/Danger";
import CitizenProfile from "../pages/citizen/Profile";
import SafetyZone from "../pages/citizen/SafetyZone";

// Admin
import AdminOverview from "../pages/admin/Overview";
import Complaints from "../pages/admin/Complaints";
import Encroachments from "../pages/admin/Encroachments";
import Detection from "../pages/admin/Detection";
import Reports from "../pages/admin/Reports";
import AdminProfile from "../pages/admin/Profile";
import AssignOfficer from "../pages/admin/AssignOfficer";
import DepartmentOfficers from "../pages/admin/DepartmentOfficers";

// Department
import DepartmentOverview from "../pages/department/Overview";
import Assigned from "../pages/department/Assigned";
import Evidence from "../pages/department/Evidence";
import DepartmentProfile from "../pages/department/Profile";
import CaseDetail from "../pages/department/CaseDetail";


function AppRoutes() {
  return (
    <BrowserRouter>
      <Routes>

        {/* =========================
            PUBLIC
        ========================= */}

        <Route
          path="/"
          element={<Landing />}
        />

        <Route
          path="/signin"
          element={<SignIn />}
        />

        <Route
          path="/register"
          element={<Register />}
        />


        {/* =========================
            CITIZEN
        ========================= */}

        {/* Citizen Dashboard */}
        <Route
          path="/citizen"
          element={<Overview />}
        />

        {/* Report Issue */}
        <Route
          path="/citizen/report"
          element={<ReportIssue />}
        />

        {/* Track Complaint */}
        <Route
          path="/citizen/track"
          element={<Track />}
        />

        {/* Danger Zones */}
        <Route
          path="/citizen/danger"
          element={<Danger />}
        />
        <Route path="/citizen/safety" element={<SafetyZone />} />

        {/* Citizen Profile */}
        <Route
          path="/citizen/profile"
          element={<CitizenProfile />}
        />


        {/* =========================
            ADMIN
        ========================= */}

        {/* Admin Dashboard */}
        <Route
          path="/admin"
          element={<AdminOverview />}
        />

        {/* Complaints */}
        <Route
          path="/admin/complaints"
          element={<Complaints />}
        />

        {/* Encroachments */}
        <Route
          path="/admin/encroachments"
          element={<Encroachments />}
          

        />
        <Route
  path="/admin/department-officers"
  element={<DepartmentOfficers />}
/>
        <Route
  path="/admin/encroachments/:id/assign"
  element={<AssignOfficer />}
/>

        {/* AI Detection */}
        <Route
          path="/admin/detection"
          element={<Detection />}
        />

        {/* Reports */}
        <Route
          path="/admin/reports"
          element={<Reports />}
        />

        {/* Admin Profile */}
        <Route
          path="/admin/profile"
          element={<AdminProfile />}
        />


        {/* =========================
            DEPARTMENT
        ========================= */}

        {/* Department Dashboard */}
        <Route
          path="/department"
          element={<DepartmentOverview />}
        />

        {/* Assigned Complaints */}
        <Route
          path="/department/assigned"
          element={<Assigned />}
        />
        <Route
  path="/department/assigned/:id"
  element={<CaseDetail />}
/>

        {/* Evidence */}
        <Route
          path="/department/evidence"
          element={<Evidence />}
        />

        {/* Department Profile */}
        <Route
          path="/department/profile"
          element={<DepartmentProfile />}
        />


        {/* =========================
            FALLBACK
        ========================= */}

        <Route
          path="*"
          element={<Navigate to="/" replace />}
        />

      </Routes>
    </BrowserRouter>
  );
}

export default AppRoutes;