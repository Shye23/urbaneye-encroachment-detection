import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { apiJson, logout } from "../../api";

function Encroachments() {
  const [cases, setCases] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    loadCases();
  }, []);

  const loadCases = async () => {
    try {
      setLoading(true);
      setError("");

      const data = await apiJson(
        "/complaints/admin/encroachment-cases/"
      );

      const caseList = Array.isArray(data)
        ? data
        : Array.isArray(data?.results)
        ? data.results
        : [];

      setCases(caseList);
    } catch (err) {
      console.error(
        "Failed to load encroachment cases:",
        err
      );

      setError(
        err.message ||
          "Unable to load encroachment cases."
      );
    } finally {
      setLoading(false);
    }
  };

  const getStatusLabel = (status) => {
    const labels = {
      OPEN: "Open",
      UNDER_REVIEW: "Under Review",
      ASSIGNED: "Assigned",
      IN_PROGRESS: "In Progress",
      RESOLVED: "Resolved",
      CLOSED: "Closed",
    };

    return labels[status] || status || "Unknown";
  };

  const getSourceLabel = (source) => {
    return source === "DETECTION"
      ? "Detection"
      : "Complaint";
  };

  // Backend now returns:
  // assigned_to -> officer ID
  // assigned_officer_name -> officer name
  const getAssignedOfficer = (item) => {
    return item.assigned_officer_name || "Not Assigned";
  };

  const isAssigned = (item) => {
    return Boolean(item.assigned_to);
  };

  return (
    <div className="portal-page">

      {/* HEADER */}
      <header className="portal-header">

        <Link
          to="/admin"
          className="portal-brand"
        >
          <div className="brand-mark">
            UE
          </div>

          <div className="brand-text">
            <strong>
              UrbanEye
            </strong>

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


      {/* MAIN */}
      <main className="portal-content">

        <div className="page-heading">

          <div>

            <p className="page-label">
              ADMIN PORTAL
            </p>

            <h1>
              Encroachment Cases
            </h1>

            <p>
              Monitor, manage and review all reported
              and detected encroachment cases.
            </p>

          </div>

          <Link
            to="/admin"
            className="outline-button"
          >
            ← Dashboard
          </Link>

        </div>


        {/* ERROR */}
        {error && (
          <div className="complaint-dashboard-error">
            {error}
          </div>
        )}


        {/* STATISTICS */}
        <section className="stats-grid">

          <div className="stat-card">

            <span>
              Total Cases
            </span>

            <strong>
              {loading ? "—" : cases.length}
            </strong>

          </div>


          <div className="stat-card">

            <span>
              Open
            </span>

            <strong>
              {loading
                ? "—"
                : cases.filter(
                    (item) =>
                      item.status === "OPEN"
                  ).length}
            </strong>

          </div>


          <div className="stat-card">

            <span>
              Assigned / Active
            </span>

            <strong>
              {loading
                ? "—"
                : cases.filter(
                    (item) =>
                      item.status === "ASSIGNED" ||
                      item.status === "IN_PROGRESS"
                  ).length}
            </strong>

          </div>


          <div className="stat-card">

            <span>
              Resolved
            </span>

            <strong>
              {loading
                ? "—"
                : cases.filter(
                    (item) =>
                      item.status === "RESOLVED"
                  ).length}
            </strong>

          </div>

        </section>


        {/* CASE LIST */}
        <section className="encroachment-section">

          <div className="encroachment-section-header">

            <div>

              <h2>
                All Encroachment Cases
              </h2>

              <p>
                Complaint-based and detection-based
                encroachment cases.
              </p>

            </div>

            <span className="encroachment-count">
              {loading
                ? "—"
                : `${cases.length} Cases`}
            </span>

          </div>


          {/* LOADING */}
          {loading && (
            <div className="encroachment-empty">
              Loading encroachment cases...
            </div>
          )}


          {/* EMPTY */}
          {!loading && cases.length === 0 && (
            <div className="encroachment-empty">

              <div className="encroachment-empty-icon">
                !
              </div>

              <h3>
                No Encroachment Cases
              </h3>

              <p>
                There are currently no encroachment
                cases available.
              </p>

            </div>
          )}


          {/* CASES */}
          {!loading && cases.length > 0 && (

            <div className="encroachment-list">

              {cases.map((item) => (

                <div
                  className="encroachment-case-card"
                  key={item.id}
                >

                  {/* CASE MAIN */}
                  <div className="encroachment-case-main">

                    <div className="encroachment-case-icon">
                      !
                    </div>

                    <div className="encroachment-case-info">

                      <div className="encroachment-case-title-row">

                        <h3>
                          {item.title}
                        </h3>

                        <span className="encroachment-status">
                          {getStatusLabel(
                            item.status
                          )}
                        </span>

                      </div>

                      <p className="encroachment-case-number">
                        {item.case_number}
                      </p>

                      {item.description && (
                        <p className="encroachment-description">
                          {item.description}
                        </p>
                      )}

                    </div>

                  </div>


                  {/* CASE META */}
                  <div className="encroachment-case-meta">

                    <div>

                      <span>
                        Source
                      </span>

                      <strong>
                        {getSourceLabel(
                          item.source
                        )}
                      </strong>

                    </div>


                    <div>

                      <span>
                        Assigned Officer
                      </span>

                      <strong>
                        {getAssignedOfficer(item)}
                      </strong>

                    </div>


                    <div>

                      <span>
                        Location
                      </span>

                      <strong>
                        {item.address ||
                          "Not available"}
                      </strong>

                    </div>


                    <div>

                      <span>
                        Created
                      </span>

                      <strong>
                        {item.created_at
                          ? new Date(
                              item.created_at
                            ).toLocaleDateString()
                          : "—"}
                      </strong>

                    </div>

                  </div>


                  {/* ACTIONS */}
                  <div className="encroachment-case-actions">

                    <Link
                      to={`/admin/encroachments/${item.id}/report`}
                      className="outline-button"
                    >
                      View Report
                    </Link>

                    <Link
                      to={`/admin/encroachments/${item.id}/assign`}
                      className="primary-button"
                    >
                      {isAssigned(item)
                        ? "Manage Assignment"
                        : "Assign Officer"}
                    </Link>

                  </div>

                </div>

              ))}

            </div>

          )}

        </section>

      </main>

    </div>
  );
}

export default Encroachments;