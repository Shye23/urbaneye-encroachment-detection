import React, { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { apiJson, logout } from "../../api";

function AssignOfficer() {
  const { id } = useParams();

  const [caseData, setCaseData] = useState(null);
  const [officers, setOfficers] = useState([]);

  const [selectedOfficer, setSelectedOfficer] = useState("");

  const [loading, setLoading] = useState(true);
  const [assigning, setAssigning] = useState(false);

  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  useEffect(() => {
    loadData();
  }, [id]);

  const loadData = async () => {
    try {
      setLoading(true);
      setError("");

      const [caseResponse, officersResponse] =
        await Promise.all([
          apiJson(
            `/complaints/admin/encroachment-cases/${id}/report/`
          ),
          apiJson(
            "/auth/admin/department-officers/"
          ),
        ]);

      setCaseData(caseResponse);

      const officerList = Array.isArray(officersResponse)
        ? officersResponse
        : Array.isArray(officersResponse?.results)
        ? officersResponse.results
        : [];

      setOfficers(officerList);

      if (caseResponse?.assigned_officer_name) {
        const currentOfficer = officerList.find(
          (officer) =>
            officer.full_name ===
              caseResponse.assigned_officer_name ||
            officer.username ===
              caseResponse.assigned_officer_name
        );

        if (currentOfficer) {
          setSelectedOfficer(
            String(currentOfficer.id)
          );
        }
      }
    } catch (err) {
      console.error(
        "Failed to load assignment data:",
        err
      );

      setError(
        err.message ||
          "Unable to load assignment information."
      );
    } finally {
      setLoading(false);
    }
  };

  const handleAssign = async (event) => {
    event.preventDefault();

    if (!selectedOfficer) {
      setError(
        "Please select a department officer."
      );
      return;
    }

    try {
      setAssigning(true);
      setError("");
      setSuccess("");

      const response = await apiJson(
        `/complaints/admin/encroachment-cases/${id}/assign/`,
        {
          method: "PUT",
          body: JSON.stringify({
            officer_id: Number(selectedOfficer),
          }),
        }
      );

      setSuccess(
        response.message ||
          "Officer assigned successfully."
      );

      await loadData();
    } catch (err) {
      console.error(
        "Failed to assign officer:",
        err
      );

      setError(
        err.message ||
          "Unable to assign officer."
      );
    } finally {
      setAssigning(false);
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

  if (loading) {
    return (
      <div className="portal-page">
        <header className="portal-header">
          <Link
            to="/admin"
            className="portal-brand"
          >
            <div className="brand-mark">UE</div>

            <div className="brand-text">
              <strong>UrbanEye</strong>
              <span>
                Encroachment Detection System
              </span>
            </div>
          </Link>
        </header>

        <main className="portal-content">
          <div className="assign-loading-card">
            <div className="assign-spinner" />

            <h2>
              Loading assignment workspace
            </h2>

            <p>
              Fetching case and department officer
              information.
            </p>
          </div>
        </main>
      </div>
    );
  }

  if (!caseData) {
    return (
      <div className="portal-page">
        <header className="portal-header">
          <Link
            to="/admin"
            className="portal-brand"
          >
            <div className="brand-mark">UE</div>

            <div className="brand-text">
              <strong>UrbanEye</strong>
              <span>
                Encroachment Detection System
              </span>
            </div>
          </Link>
        </header>

        <main className="portal-content">
          <div className="assign-page-error">
            <div className="assign-error-icon">
              !
            </div>

            <h2>Case unavailable</h2>

            <p>
              {error ||
                "The requested case could not be loaded."}
            </p>

            <Link
              to="/admin/encroachments"
              className="assign-cancel-btn"
            >
              Back to Encroachment Cases
            </Link>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="portal-page">
      {/* HEADER */}
      <header className="portal-header">
        <Link
          to="/admin"
          className="portal-brand"
        >
          <div className="brand-mark">UE</div>

          <div className="brand-text">
            <strong>UrbanEye</strong>
            <span>
              Encroachment Detection System
            </span>
          </div>
        </Link>

        <div className="portal-header-right">
          <span>Admin</span>

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
        {/* HEADING */}
        <div className="assign-heading">
          <div>
            <p className="page-label">
              ADMIN PORTAL
            </p>

            <h1>
              Assign Department Officer
            </h1>

            <p>
              Assign an active department officer
              to manage this encroachment case.
            </p>
          </div>

          <Link
            to="/admin/encroachments"
            className="assign-back-link"
          >
            ← Back to Cases
          </Link>
        </div>

        {/* MESSAGES */}
        {error && (
          <div className="assign-message assign-message-error">
            <span>!</span>
            <p>{error}</p>
          </div>
        )}

        {success && (
          <div className="assign-message assign-message-success">
            <span>✓</span>
            <p>{success}</p>
          </div>
        )}

        {/* CASE SUMMARY */}
        <section className="assignment-case-card">
          <div className="assignment-case-top">
            <div>
              <span className="assignment-eyebrow">
                CASE
              </span>

              <h2>
                {caseData.title}
              </h2>

              <p>
                {caseData.case_number}
              </p>
            </div>

            <span
              className={`assignment-status status-${(
                caseData.status || ""
              ).toLowerCase()}`}
            >
              {getStatusLabel(caseData.status)}
            </span>
          </div>

          <div className="assignment-case-grid">
            <div>
              <span>Source</span>
              <strong>
                {getSourceLabel(
                  caseData.source
                )}
              </strong>
            </div>

            <div>
              <span>Location</span>
              <strong>
                {caseData.address ||
                  "Not available"}
              </strong>
            </div>

            <div>
              <span>Created</span>
              <strong>
                {caseData.created_at
                  ? new Date(
                      caseData.created_at
                    ).toLocaleDateString()
                  : "—"}
              </strong>
            </div>
          </div>

          {caseData.description && (
            <div className="assignment-description">
              <span>Case Description</span>
              <p>
                {caseData.description}
              </p>
            </div>
          )}
        </section>

        {/* ASSIGNMENT WORKSPACE */}
        <section className="assignment-workspace">
          <div className="assignment-workspace-header">
            <div>
              <span className="assignment-eyebrow">
                OFFICER ASSIGNMENT
              </span>

              <h2>
                Select Department Officer
              </h2>

              <p>
                Only active Department Officer
                accounts are available here.
              </p>
            </div>
          </div>

          <form
            onSubmit={handleAssign}
            className="assignment-form"
          >
            <label
              htmlFor="department-officer"
              className="assignment-label"
            >
              Department Officer
            </label>

            <div className="assignment-select-wrap">
              <div className="assignment-select-icon">
                👤
              </div>

              <select
                id="department-officer"
                className="assignment-select"
                value={selectedOfficer}
                onChange={(event) =>
                  setSelectedOfficer(
                    event.target.value
                  )
                }
                disabled={
                  assigning ||
                  officers.length === 0
                }
              >
                <option value="">
                  Select an officer
                </option>

                {officers.map((officer) => (
                  <option
                    key={officer.id}
                    value={officer.id}
                  >
                    {officer.full_name ||
                      officer.username}{" "}
                    — @{officer.username}
                  </option>
                ))}
              </select>

              <span className="assignment-select-arrow">
                ▾
              </span>
            </div>

            {officers.length === 0 && (
              <div className="assignment-no-officers">
                <strong>
                  No active department officers
                </strong>

                <span>
                  Create an officer account before
                  assigning this case.
                </span>

                <Link
                  to="/admin/department-officers"
                  className="assignment-officer-link"
                >
                  Manage Department Officers →
                </Link>
              </div>
            )}

            <div className="assignment-form-footer">
              <Link
                to="/admin/encroachments"
                className="assignment-cancel-button"
              >
                Cancel
              </Link>

              <button
                type="submit"
                className="assignment-submit-button"
                disabled={
                  assigning ||
                  !selectedOfficer
                }
              >
                {assigning ? (
                  <>
                    <span className="assign-button-spinner" />
                    Assigning...
                  </>
                ) : (
                  <>
                    Assign Officer
                    <span>→</span>
                  </>
                )}
              </button>
            </div>
          </form>
        </section>

        {/* CURRENT ASSIGNMENT */}
        {caseData.assigned_officer_name && (
          <section className="current-officer-card">
            <div className="current-officer-icon">
              ✓
            </div>

            <div className="current-officer-content">
              <span className="assignment-eyebrow">
                CURRENT ASSIGNMENT
              </span>

              <h2>
                {caseData.assigned_officer_name}
              </h2>

              <p>
                This case is currently assigned to
                this Department Officer.
              </p>
            </div>

            <span className="current-officer-badge">
              Assigned
            </span>
          </section>
        )}
      </main>
    </div>
  );
}

export default AssignOfficer;