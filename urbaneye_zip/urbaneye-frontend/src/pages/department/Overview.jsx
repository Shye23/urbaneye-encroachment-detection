import React from "react";
import { Link } from "react-router-dom";

function Overview() {
  return (
    <DepartmentPage
      title="Department Dashboard"
      description="Manage complaints and encroachment cases assigned to your department."
    />
  );
}

function DepartmentPage({ title, description }) {
  return (
    <div className="portal-page">

      <header className="portal-header">

        <div className="portal-brand">

          <div className="brand-mark">
            UE
          </div>

          <div className="brand-text">
            <strong>UrbanEye</strong>

            <span>
              Encroachment Detection System
            </span>
          </div>

        </div>

      </header>

      <main className="portal-content">

        <div className="page-heading">

          <div>

            <p className="page-label">
              DEPARTMENT PORTAL
            </p>

            <h1>
              {title}
            </h1>

            <p>
              {description}
            </p>

          </div>

        </div>

        <section className="department-dashboard-grid">

          <div className="department-dashboard-card">

            <div className="dashboard-card-icon">
              📋
            </div>

            <h2>
              Assigned Cases
            </h2>

            <p>
              View encroachment cases assigned to you and
              manage their progress.
            </p>

            <Link
              to="/department/assigned"
              className="dashboard-primary-button"
            >
              View Assigned Cases
            </Link>

          </div>


          <div className="department-dashboard-card">

            <div className="dashboard-card-icon">
              🛠️
            </div>

            <h2>
              Case Actions
            </h2>

            <p>
              Record inspections, verification, notices,
              actions taken and case resolution.
            </p>

            <Link
              to="/department/assigned"
              className="dashboard-secondary-button"
            >
              Manage Cases
            </Link>

          </div>

        </section>

      </main>

    </div>
  );
}

export default Overview;