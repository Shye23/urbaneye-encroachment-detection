import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { apiJson, logout } from "../../api";

function Assigned() {
  const [cases, setCases] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    loadAssignedCases();
  }, []);

  const loadAssignedCases = async () => {
    try {
      setLoading(true);
      setError("");

      const data = await apiJson(
        "/complaints/department/assigned-cases/"
      );

      const caseList = Array.isArray(data)
        ? data
        : Array.isArray(data?.results)
        ? data.results
        : [];

      setCases(caseList);
    } catch (err) {
      console.error(
        "Failed to load assigned cases:",
        err
      );

      setError(
        err.message ||
          "Unable to load assigned cases."
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

  return (
    <div className="portal-page">

      {/* HEADER */}
      <header className="portal-header">

        <Link
          to="/department"
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
            Department Officer
          </span>

          <Link to="/department/profile">
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
              DEPARTMENT PORTAL
            </p>

            <h1>
              Assigned Cases
            </h1>

            <p>
              View and work on encroachment cases
              assigned to you.
            </p>

          </div>

          <Link
            to="/department"
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


        {/* STATS */}
        <section className="stats-grid">

          <div className="stat-card">

            <span>
              Total Assigned
            </span>

            <strong>
              {loading ? "—" : cases.length}
            </strong>

          </div>


          <div className="stat-card">

            <span>
              Assigned
            </span>

            <strong>
              {loading
                ? "—"
                : cases.filter(
                    (item) =>
                      item.status === "ASSIGNED"
                  ).length}
            </strong>

          </div>


          <div className="stat-card">

            <span>
              In Progress
            </span>

            <strong>
              {loading
                ? "—"
                : cases.filter(
                    (item) =>
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


        {/* CASES */}
        <section className="encroachment-section">

          <div className="encroachment-section-header">

            <div>

              <h2>
                My Assigned Cases
              </h2>

              <p>
                Only cases assigned to your department
                officer account are shown here.
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
              Loading assigned cases...
            </div>
          )}


          {/* EMPTY */}
          {!loading && cases.length === 0 && (

            <div className="encroachment-empty">

              <div className="encroachment-empty-icon">
                ✓
              </div>

              <h3>
                No Assigned Cases
              </h3>

              <p>
                You currently have no encroachment
                cases assigned to you.
              </p>

            </div>

          )}


          {/* LIST */}
          {!loading && cases.length > 0 && (

            <div className="encroachment-list">

              {cases.map((item) => (

                <div
                  className="encroachment-case-card"
                  key={item.id}
                >

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


                  <div className="encroachment-case-actions">

                    <Link
                      to={`/department/assigned/${item.id}`}
                      className="primary-button"
                    >
                      Open Case
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

export default Assigned;