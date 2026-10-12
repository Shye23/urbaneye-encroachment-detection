import React, { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { apiJson, logout } from "../../api";

function CaseDetail() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [caseData, setCaseData] = useState(null);
  const [history, setHistory] = useState([]);

  const [selectedAction, setSelectedAction] = useState("");
  const [remarks, setRemarks] = useState("");

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  useEffect(() => {
    loadCase();
  }, [id]);

  const loadCase = async () => {
    try {
      setLoading(true);
      setError("");

      const [casesResponse, historyResponse] =
        await Promise.all([
          apiJson(
            "/complaints/department/assigned-cases/"
          ),
          apiJson(
            `/complaints/department/assigned-cases/${id}/actions/`
          ),
        ]);

      const cases = Array.isArray(casesResponse)
        ? casesResponse
        : Array.isArray(casesResponse?.results)
        ? casesResponse.results
        : [];

      const selectedCase = cases.find(
        (item) => String(item.id) === String(id)
      );

      if (!selectedCase) {
        setError(
          "This case is not assigned to you."
        );
        setCaseData(null);
        return;
      }

      setCaseData(selectedCase);

      const actionList = Array.isArray(historyResponse)
        ? historyResponse
        : Array.isArray(historyResponse?.results)
        ? historyResponse.results
        : [];

      setHistory(actionList);
    } catch (err) {
      console.error(
        "Failed to load case:",
        err
      );

      setError(
        err.message ||
          "Unable to load case information."
      );
    } finally {
      setLoading(false);
    }
  };

  const handleAddAction = async (event) => {
    event.preventDefault();

    if (!selectedAction) {
      setError("Please select an action.");
      return;
    }

    try {
      setSaving(true);
      setError("");
      setSuccess("");

      await apiJson(
        `/complaints/department/assigned-cases/${id}/actions/`,
        {
          method: "POST",
          body: JSON.stringify({
            action: selectedAction,
            remarks: remarks.trim(),
          }),
        }
      );

      setSuccess("Action added successfully.");

      setSelectedAction("");
      setRemarks("");

      await loadCase();
    } catch (err) {
      console.error(
        "Failed to add action:",
        err
      );

      setError(
        err.message ||
          "Unable to add action."
      );
    } finally {
      setSaving(false);
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

  const getActionLabel = (action) => {
    const labels = {
      STARTED: "Started",
      INSPECTION: "Inspection",
      VERIFICATION: "Verification",
      NOTICE_ISSUED: "Notice Issued",
      ACTION_TAKEN: "Action Taken",
      RESOLVED: "Resolved",
    };

    return labels[action] || action;
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
            to="/department"
            className="portal-brand"
          >
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
        </header>

        <main className="portal-content">
          <div className="assign-loading-card">
            <div className="assign-spinner" />

            <h2>
              Loading case
            </h2>

            <p>
              Please wait while case information
              is being loaded.
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
            to="/department"
            className="portal-brand"
          >
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
        </header>

        <main className="portal-content">

          <div className="assign-page-error">
            <div className="assign-error-icon">
              !
            </div>

            <h2>
              Case unavailable
            </h2>

            <p>
              {error ||
                "This case is not available."}
            </p>

            <Link
              to="/department/assigned"
              className="assign-cancel-btn"
            >
              Back to Assigned Cases
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

        {/* PAGE HEADING */}

        <div className="assign-heading">

          <div>

            <p className="page-label">
              DEPARTMENT PORTAL
            </p>

            <h1>
              Case Details
            </h1>

            <p>
              Review the assigned case and update
              its action history.
            </p>

          </div>

          <Link
            to="/department/assigned"
            className="assign-back-link"
          >
            ← Back to Assigned Cases
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


        {/* CASE CARD */}

        <section className="assign-card">

          {/* CASE HEADER */}

          <div className="assign-card-header">

            <div>

              <span className="assign-case-label">
                ASSIGNED CASE
              </span>

              <h2>
                {caseData.title}
              </h2>

              <p className="assign-case-number">
                Case Number:
                <strong>
                  {" "}
                  {caseData.case_number}
                </strong>
              </p>

            </div>

            <span
              className={`assign-status-badge status-${(
                caseData.status || ""
              ).toLowerCase()}`}
            >
              {getStatusLabel(caseData.status)}
            </span>

          </div>


          {/* CASE INFORMATION */}

          <div className="assign-info-grid">

            <div className="assign-info-item">

              <span>
                Source
              </span>

              <strong>
                {getSourceLabel(
                  caseData.source
                )}
              </strong>

            </div>


            <div className="assign-info-item">

              <span>
                Location
              </span>

              <strong>
                {caseData.address ||
                  "Not available"}
              </strong>

            </div>


            <div className="assign-info-item">

              <span>
                Created
              </span>

              <strong>
                {caseData.created_at
                  ? new Date(
                      caseData.created_at
                    ).toLocaleDateString()
                  : "—"}
              </strong>

            </div>

          </div>


          {/* DESCRIPTION */}

          <div className="assign-description">

            <span>
              Description
            </span>

            <p>
              {caseData.description ||
                "No description available."}
            </p>

          </div>

        </section>


        {/* ACTION SECTION */}

        <section className="assign-card">

          <div className="assign-card-header">

            <div>

              <span className="assign-case-label">
                WORKFLOW
              </span>

              <h2>
                Add Action
              </h2>

              <p className="assign-case-number">
                Record the work performed on this case.
              </p>

            </div>

          </div>


          <form
            onSubmit={handleAddAction}
            className="assign-form"
          >

            <label
              htmlFor="case-action"
              className="assign-select-label"
            >
              Action
            </label>

            <div className="assign-select-container">

              <select
                id="case-action"
                className="assign-select"
                value={selectedAction}
                onChange={(event) =>
                  setSelectedAction(
                    event.target.value
                  )
                }
                disabled={saving}
              >

                <option value="">
                  Select Action
                </option>

                <option value="STARTED">
                  Started
                </option>

                <option value="INSPECTION">
                  Inspection
                </option>

                <option value="VERIFICATION">
                  Verification
                </option>

                <option value="NOTICE_ISSUED">
                  Notice Issued
                </option>

                <option value="ACTION_TAKEN">
                  Action Taken
                </option>

                <option value="RESOLVED">
                  Resolved
                </option>

              </select>

              <span className="assign-select-arrow">
                ▾
              </span>

            </div>


            <label
              htmlFor="remarks"
              className="assign-select-label"
              style={{
                marginTop: "20px",
              }}
            >
              Remarks
            </label>

            <textarea
              id="remarks"
              className="case-remarks-textarea"
              value={remarks}
              onChange={(event) =>
                setRemarks(event.target.value)
              }
              placeholder="Describe the action taken..."
              rows={5}
              disabled={saving}
            />


            <div className="assign-form-footer">

              <Link
                to="/department/assigned"
                className="assign-cancel-button"
              >
                Cancel
              </Link>

              <button
                type="submit"
                className="assign-submit-button"
                disabled={
                  saving ||
                  !selectedAction
                }
              >

                {saving ? (
                  <>
                    <span className="assign-button-spinner" />
                    Saving...
                  </>
                ) : (
                  "Add Action"
                )}

              </button>

            </div>

          </form>

        </section>


        {/* HISTORY */}

        <section className="assign-card">

          <div className="assign-card-header">

            <div>

              <span className="assign-case-label">
                CASE HISTORY
              </span>

              <h2>
                Action History
              </h2>

              <p className="assign-case-number">
                All actions recorded for this case.
              </p>

            </div>

          </div>


          <div className="case-history-list">

            {history.length === 0 ? (

              <div className="case-history-empty">
                <span>✓</span>

                <h3>
                  No actions recorded yet
                </h3>

                <p>
                  Add the first action for this case
                  using the workflow form above.
                </p>
              </div>

            ) : (

              history.map((item, index) => (

                <div
                  className="case-history-item"
                  key={item.id}
                >

                  <div className="case-history-marker">
                    {history.length - index}
                  </div>

                  <div className="case-history-content">

                    <div className="case-history-top">

                      <strong>
                        {getActionLabel(
                          item.action
                        )}
                      </strong>

                      <span>
                        {item.created_at
                          ? new Date(
                              item.created_at
                            ).toLocaleString()
                          : "—"}
                      </span>

                    </div>

                    {item.remarks && (
                      <p>
                        {item.remarks}
                      </p>
                    )}

                  </div>

                </div>

              ))

            )}

          </div>

        </section>

      </main>

    </div>
  );
}

export default CaseDetail;