import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { apiJson, logout } from "../../api";
function Overview() {
  

  const [complaints, setComplaints] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const handleSignOut = () => {
    logout();
  };

  useEffect(() => {
    const loadComplaints = async () => {
      try {
        setLoading(true);
        setError("");
const data = await apiJson("/complaints/");

const complaintList = Array.isArray(data)
  ? data
  : Array.isArray(data.results)
  ? data.results
  : [];

setComplaints(complaintList);
      } catch (err) {
        console.error("Failed to load complaints:", err);
        setError(err.message);
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
    <div className="citizen-page">

      {/* HEADER */}

      <header className="citizen-header">

        <Link
          to="/citizen"
          className="citizen-brand"
        >
          <div className="brand-mark">
            UE
          </div>

          <span>
            UrbanEye
          </span>
        </Link>

        <div className="citizen-header-right">

          <span className="citizen-user">
            Citizen
          </span>

          <Link
            to="/citizen/profile"
            className="profile-header-link"
          >
            Profile
          </Link>

          <button
            type="button"
            className="logout-button"
            onClick={handleSignOut}
          >
            Sign Out
          </button>

        </div>

      </header>


      {/* MAIN */}

      <main className="citizen-content">

        <section className="citizen-welcome">

          <p className="page-label">
            CITIZEN PORTAL
          </p>

          <h1>
            Welcome to UrbanEye
          </h1>

          <p>
            Report civic issues, track complaints,
            and help make your city safer and smarter.
          </p>

        </section>


        {/* COMPLAINT STATISTICS */}

        <section className="complaint-stats-section">

          <div className="complaint-stat-card">

            <div className="complaint-stat-number">
              {loading ? "—" : totalComplaints}
            </div>

            <div className="complaint-stat-label">
              Total Complaints
            </div>

          </div>


          <div className="complaint-stat-card">

            <div className="complaint-stat-number">
              {loading ? "—" : pendingComplaints}
            </div>

            <div className="complaint-stat-label">
              Pending
            </div>

          </div>


          <div className="complaint-stat-card">

            <div className="complaint-stat-number">
              {loading ? "—" : underReviewComplaints}
            </div>

            <div className="complaint-stat-label">
              Under Review
            </div>

          </div>


          <div className="complaint-stat-card">

            <div className="complaint-stat-number">
              {loading ? "—" : resolvedComplaints}
            </div>

            <div className="complaint-stat-label">
              Resolved
            </div>

          </div>

        </section>


        {error && (
          <div className="complaint-dashboard-error">
            {error}
          </div>
        )}


        {/* ACTION CARDS */}

        <section className="citizen-action-grid">

          {/* REPORT */}

          <Link
            to="/citizen/report"
            className="citizen-action-card"
          >

            <div className="action-icon">
              +
            </div>

            <h3>
              Report an Issue
            </h3>

            <p>
              Report roads, garbage, drainage,
              encroachment and other civic issues.
            </p>

            <span className="card-link">
              Report Issue →
            </span>

          </Link>


          {/* TRACK */}

          <Link
            to="/citizen/track"
            className="citizen-action-card"
          >

            <div className="action-icon">
              ✓
            </div>

            <h3>
              Track Complaint
            </h3>

            <p>
              Track the current status and progress
              of complaints submitted by you.
            </p>

            <span className="card-link">
              Track Complaint →
            </span>

          </Link>


          {/* DANGER */}

          <Link
            to="/citizen/danger"
            className="citizen-action-card"
          >

            <div className="action-icon danger-icon">
              !
            </div>

            <h3>
              Danger Zones
            </h3>

            <p>
              View reported danger zones and
              safety-related information.
            </p>

            <span className="card-link">
              View Danger Zones →
            </span>

          </Link>

        </section>


        {/* ANONYMOUS INFORMATION */}

        <section className="anonymous-dashboard-note">

          <div className="anonymous-note-icon">
            ✓
          </div>

          <div>

            <strong>
              Anonymous complaint protection
            </strong>

            <p>
              If you selected the anonymous complaint
              option during Citizen Sign In, your identity
              will be treated as confidential when you
              submit an anonymous complaint.
            </p>

          </div>

        </section>


        {/* QUICK LINKS */}

        <section className="quick-links-section">

          <h2>
            Quick Access
          </h2>

          <div className="quick-links">

            <Link
              to="/citizen/report"
              className="quick-link"
            >
              Report Issue
            </Link>

            <Link
              to="/citizen/track"
              className="quick-link"
            >
              My Complaints
            </Link>

            {/* SAFETY ZONES */}

            <Link
              to="/citizen/safety"
              className="quick-link"
            >
              Safety Zones
            </Link>

            <Link
              to="/citizen/profile"
              className="quick-link"
            >
              My Profile
            </Link>

          </div>

        </section>

      </main>

    </div>
  );
}

export default Overview;