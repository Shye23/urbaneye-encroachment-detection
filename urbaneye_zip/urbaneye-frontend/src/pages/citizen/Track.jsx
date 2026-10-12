import React, { useState } from "react";
import { Link } from "react-router-dom";
import { apiFetch } from "../../api";

function Track() {
  const [complaintId, setComplaintId] = useState("");
  const [complaint, setComplaint] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSearch = async (e) => {
    e.preventDefault();

    if (!complaintId.trim()) {
      setError("Please enter a complaint ID.");
      return;
    }

    setLoading(true);
    setError("");
    setComplaint(null);

    try {
      const response = await apiFetch("/complaints/", {
        method: "GET",
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail ||
            data.error ||
            "Unable to fetch complaints."
        );
      }

      // Accept both UE-3 and 3
      const enteredId = complaintId.trim().toUpperCase();
      const numericId = enteredId.startsWith("UE-")
        ? enteredId.replace("UE-", "")
        : enteredId;

      const foundComplaint = data.find(
        (item) => String(item.id) === numericId
      );

      if (!foundComplaint) {
        setError(
          "Complaint not found. Please check your Complaint ID."
        );
        return;
      }

      setComplaint(foundComplaint);
    } catch (err) {
      console.error("Track complaint error:", err);
      setError(
        err.message ||
          "Something went wrong while tracking the complaint."
      );
    } finally {
      setLoading(false);
    }
  };

  const getCategoryName = (category) => {
    const categories = {
      ENCROACHMENT: "Encroachment",
      ROAD: "Road",
      FOOTPATH: "Footpath",
      PUBLIC_LAND: "Public Land",
      OTHER: "Other",
    };

    return categories[category] || category;
  };

  const getStatusName = (status) => {
    const statuses = {
      PENDING: "Pending",
      UNDER_REVIEW: "Under Review",
      VERIFIED: "Verified",
      REJECTED: "Rejected",
      RESOLVED: "Resolved",
    };

    return statuses[status] || status;
  };

  const getProgressState = (status) => {
    switch (status) {
      case "PENDING":
        return 1;

      case "UNDER_REVIEW":
        return 2;

      case "VERIFIED":
        return 3;

      case "RESOLVED":
        return 4;

      case "REJECTED":
        return 2;

      default:
        return 1;
    }
  };

  const formatDate = (date) => {
    if (!date) {
      return "Not available";
    }

    return new Date(date).toLocaleDateString("en-GB", {
      day: "2-digit",
      month: "short",
      year: "numeric",
    });
  };

  const progressState = complaint
    ? getProgressState(complaint.status)
    : 0;

  return (
    <div className="portal-page">

      <header className="portal-header">

        <Link
          to="/citizen/report"
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

        <div className="portal-header-right">

          <span>
            Citizen
          </span>

          <Link to="/citizen/profile">
            Profile
          </Link>

          <Link to="/">
            Sign Out
          </Link>

        </div>

      </header>

      <main className="portal-content">

        <div className="page-heading">

          <div>

            <p className="page-label">
              CITIZEN PORTAL
            </p>

            <h1>
              Track Complaint
            </h1>

            <p>
              Check the current status of your
              submitted complaint.
            </p>

          </div>

          <Link
            to="/citizen/report"
            className="outline-button"
          >
            ← Report Issue
          </Link>

        </div>

        <section className="track-search-card">

          <h2>
            Find Your Complaint
          </h2>

          <p>
            Enter the complaint ID provided after
            submission.
          </p>

          <form
            onSubmit={handleSearch}
            className="track-search-form"
          >

            <div className="track-search-input">

              <label>
                COMPLAINT ID
              </label>

              <input
                type="text"
                value={complaintId}
                onChange={(e) =>
                  setComplaintId(e.target.value)
                }
                placeholder="Example: UE-10245"
              />

            </div>

            <button
              type="submit"
              className="complaint-button"
              disabled={loading}
            >
              {loading
                ? "Checking..."
                : "Track Complaint"}
            </button>

          </form>

          {error && (
            <div className="auth-error">
              {error}
            </div>
          )}

        </section>

        {!complaint && !error && (

          <section className="track-empty-card">

            <div className="track-empty-icon">
              ✓
            </div>

            <h3>
              No Complaint Selected
            </h3>

            <p>
              Enter your complaint ID above to view
              its latest status.
            </p>

          </section>

        )}

        {complaint && (

          <section className="track-result-card">

            <div className="track-result-header">

              <div>

                <p className="page-label">
                  COMPLAINT DETAILS
                </p>

                <h2>
                  {complaint.title}
                </h2>

              </div>

              <span className="complaint-status">
                {getStatusName(complaint.status)}
              </span>

            </div>

            <div className="complaint-progress">

              <div
                className={`progress-step ${
                  progressState >= 1
                    ? "completed"
                    : ""
                }`}
              >

                <div className="progress-circle">
                  {progressState >= 1 ? "✓" : "1"}
                </div>

                <span>
                  Submitted
                </span>

              </div>

              <div
                className={`progress-line ${
                  progressState >= 2
                    ? "active"
                    : ""
                }`}
              ></div>

              <div
                className={`progress-step ${
                  progressState >= 2
                    ? "active"
                    : ""
                }`}
              >

                <div className="progress-circle">
                  {progressState >= 2 ? "✓" : "2"}
                </div>

                <span>
                  Under Review
                </span>

              </div>

              <div
                className={`progress-line ${
                  progressState >= 3
                    ? "active"
                    : ""
                }`}
              ></div>

              <div
                className={`progress-step ${
                  progressState >= 3
                    ? "active"
                    : ""
                }`}
              >

                <div className="progress-circle">
                  {progressState >= 3 ? "✓" : "3"}
                </div>

                <span>
                  Assigned
                </span>

              </div>

              <div
                className={`progress-line ${
                  progressState >= 4
                    ? "active"
                    : ""
                }`}
              ></div>

              <div
                className={`progress-step ${
                  progressState >= 4
                    ? "active"
                    : ""
                }`}
              >

                <div className="progress-circle">
                  {progressState >= 4 ? "✓" : "4"}
                </div>

                <span>
                  Resolved
                </span>

              </div>

            </div>

            <div className="complaint-details-grid">

              <div className="complaint-detail">
                <span>COMPLAINT ID</span>
                <strong>
                  UE-{complaint.id}
                </strong>
              </div>

              <div className="complaint-detail">
                <span>CATEGORY</span>
                <strong>
                  {getCategoryName(complaint.category)}
                </strong>
              </div>

              <div className="complaint-detail">
                <span>LOCATION</span>
                <strong>
                  {complaint.address ||
                    "Location not provided"}
                </strong>
              </div>

              <div className="complaint-detail">
                <span>DEPARTMENT</span>
                <strong>
                  Municipal Department
                </strong>
              </div>

              <div className="complaint-detail">
                <span>SUBMITTED</span>
                <strong>
                  {formatDate(complaint.created_at)}
                </strong>
              </div>

              <div className="complaint-detail">
                <span>STATUS</span>
                <strong>
                  {getStatusName(complaint.status)}
                </strong>
              </div>

            </div>

            <div className="track-update-box">

              <div className="track-update-icon">
                i
              </div>

              <div>

                <strong>
                  Current Update
                </strong>

                <p>
                  {complaint.status === "PENDING"
                    ? "Your complaint has been successfully submitted and is waiting for review."
                    : complaint.status ===
                      "UNDER_REVIEW"
                    ? "Your complaint has been received and is currently being reviewed by the concerned department."
                    : complaint.status ===
                      "VERIFIED"
                    ? "Your complaint has been verified and forwarded for necessary action."
                    : complaint.status ===
                      "RESOLVED"
                    ? "Your complaint has been resolved by the concerned department."
                    : complaint.status ===
                      "REJECTED"
                    ? "Your complaint has been reviewed but was rejected by the concerned department."
                    : "Your complaint status has been updated."}
                </p>

              </div>

            </div>

          </section>

        )}

      </main>

    </div>
  );
}

export default Track;