import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { apiJson, logout } from "../../api";

function Overview() {
  const [complaints, setComplaints] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const loadComplaints = async () => {
      try {
        setLoading(true);
        setError("");

        const data = await apiJson("/complaints/admin/complaints/");

        setComplaints(Array.isArray(data) ? data : []);
      } catch (err) {
        console.error("Failed to load admin dashboard:", err);
        setError(err.message || "Unable to load dashboard data.");
      } finally {
        setLoading(false);
      }
    };

    loadComplaints();
  }, []);

  const totalComplaints = complaints.length;

  const pendingComplaints = complaints.filter(
    (complaint) => complaint.status === "PENDING"
  ).length;

  const underReviewComplaints = complaints.filter(
    (complaint) => complaint.status === "UNDER_REVIEW"
  ).length;

  const resolvedComplaints = complaints.filter(
    (complaint) => complaint.status === "RESOLVED"
  ).length;

  return (
    <div className="portal-page">

      <header className="portal-header">

        <Link to="/admin" className="portal-brand">

          <div className="brand-mark">
            UE
          </div>

          <div className="brand-text">
            <strong>UrbanEye</strong>

            <span>
              Encroachment Detection System
            </span>
          </div>

        </Link>


        <div className="portal-header-right">

          <span>
            Admin
          </span>

          <Link to="/admin/profile">
            Profile
          </Link>

          <button
            type="button"
            onClick={logout}
            className="logout-button"
          >
            Sign Out
          </button>

        </div>

      </header>


      <main className="portal-content">

        <div className="page-heading">

          <div>

            <p className="page-label">
              ADMIN PORTAL
            </p>

            <h1>
              Dashboard
            </h1>

            <p>
              Monitor complaints, encroachments and
              system activity.
            </p>

          </div>

        </div>


        {error && (
          <div className="complaint-dashboard-error">
            {error}
          </div>
        )}


        <div className="stats-grid">

          <div className="stat-card">
            <span>Total Complaints</span>

            <strong>
              {loading ? "—" : totalComplaints}
            </strong>
          </div>


          <div className="stat-card">
            <span>Pending</span>

            <strong>
              {loading ? "—" : pendingComplaints}
            </strong>
          </div>


          <div className="stat-card">
            <span>Under Review</span>

            <strong>
              {loading ? "—" : underReviewComplaints}
            </strong>
          </div>


          <div className="stat-card">
            <span>Resolved</span>

            <strong>
              {loading ? "—" : resolvedComplaints}
            </strong>
          </div>

        </div>


        <div className="admin-links">

          <Link to="/admin/complaints">
            Complaint Management
          </Link>

          <Link to="/admin/encroachments">
            Encroachments
          </Link>

          <Link to="/admin/detection">
            Detection
          </Link>
          <Link
  to="/admin/department-officers"
  className="dashboard-secondary-button"
>
  Manage Department Officers
</Link>

          <Link to="/admin/reports">
            Reports
          </Link>

        </div>

      </main>

    </div>
  );
}

export default Overview;