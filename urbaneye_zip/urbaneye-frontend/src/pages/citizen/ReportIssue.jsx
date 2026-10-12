import React, { useState } from "react";
import { Link } from "react-router-dom";
import { apiFetch } from "../../api";

function ReportIssue() {
  const [anonymous, setAnonymous] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  const [category, setCategory] = useState("");
  const [location, setLocation] = useState("");
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [evidence, setEvidence] = useState(null);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [complaintId, setComplaintId] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();

    setError("");
    setLoading(true);

    try {
      // Create complaint
      const response = await apiFetch("/complaints/", {
        method: "POST",
        body: JSON.stringify({
          title,
          description,
          category,
          address: location,
          is_anonymous: anonymous,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail ||
          data.error ||
          "Failed to submit complaint."
        );
      }

      // Upload evidence if selected
      if (evidence) {
        const formData = new FormData();
        formData.append("image", evidence);

        const imageResponse = await apiFetch(
          `/complaints/${data.id}/images/`,
          {
            method: "POST",
            body: formData,
          }
        );

        const imageData = await imageResponse.json();

        if (!imageResponse.ok) {
          throw new Error(
            imageData.detail ||
            imageData.error ||
            "Complaint submitted, but image upload failed."
          );
        }
      }

      // Success only after complaint and evidence upload
      // are both successful
      setComplaintId(data.id);
      setSubmitted(true);

    } catch (err) {
      console.error("Complaint submission error:", err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleClear = () => {
    setCategory("");
    setLocation("");
    setTitle("");
    setDescription("");
    setAnonymous(false);
    setError("");
    setEvidence(null);
  };

  const handleSubmitAnother = () => {
    setSubmitted(false);
    setComplaintId(null);
    handleClear();
  };

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
              Report an Issue
            </h1>

            <p>
              Report an encroachment or civic issue
              to the concerned authority.
            </p>

          </div>

        </div>

        {submitted ? (

          <section className="success-card">

            <div className="success-icon">
              ✓
            </div>

            <h2>
              Complaint Submitted Successfully
            </h2>

            <p>
              Your complaint has been received by
              UrbanEye.
            </p>

            {anonymous && (

              <div className="submission-note">

                <strong>
                  Anonymous complaint information
                </strong>

                <p>
                  Your identity will not be displayed
                  with the complaint. The information
                  submitted will be considered for
                  verification and appropriate action
                  by the concerned authority.
                </p>

              </div>

            )}

            <p className="complaint-number">
              Complaint ID:{" "}
              <strong>
                UE-{complaintId}
              </strong>
            </p>

            <div className="success-actions">

              <Link
                to="/citizen/track"
                className="primary-button"
              >
                Track Complaint
              </Link>

              <button
                type="button"
                className="outline-button"
                onClick={handleSubmitAnother}
              >
                Submit Another
              </button>

            </div>

          </section>

        ) : (

          <section className="complaint-card">

            {error && (
              <div className="auth-error">
                {error}
              </div>
            )}

            <form onSubmit={handleSubmit}>

              <div className="complaint-grid">

                {/* CATEGORY */}

                <div className="complaint-field">

                  <label>
                    ISSUE CATEGORY
                  </label>

                  <select
                    value={category}
                    onChange={(e) =>
                      setCategory(e.target.value)
                    }
                    required
                  >

                    <option value="">
                      Select category
                    </option>

                    <option value="ENCROACHMENT">
                      Encroachment
                    </option>

                    <option value="ROAD">
                      Road
                    </option>

                    <option value="FOOTPATH">
                      Footpath
                    </option>

                    <option value="PUBLIC_LAND">
                      Public Land
                    </option>

                    <option value="OTHER">
                      Other
                    </option>

                  </select>

                </div>

                {/* LOCATION */}

                <div className="complaint-field">

                  <label>
                    LOCATION
                  </label>

                  <input
                    type="text"
                    value={location}
                    onChange={(e) =>
                      setLocation(e.target.value)
                    }
                    placeholder="Enter location"
                    required
                  />

                </div>

              </div>

              {/* TITLE */}

              <div className="complaint-field">

                <label>
                  COMPLAINT TITLE
                </label>

                <input
                  type="text"
                  value={title}
                  onChange={(e) =>
                    setTitle(e.target.value)
                  }
                  placeholder="Briefly describe the issue"
                  required
                />

              </div>

              {/* DESCRIPTION */}

              <div className="complaint-field">

                <label>
                  DESCRIPTION
                </label>

                <textarea
                  rows="6"
                  value={description}
                  onChange={(e) =>
                    setDescription(e.target.value)
                  }
                  placeholder="Provide details about the issue..."
                  required
                />

              </div>

              {/* EVIDENCE */}

              <div className="complaint-field">

                <label>
                  EVIDENCE
                </label>

                <input
                  type="file"
                  accept="image/*"
                  onChange={(e) =>
                    setEvidence(e.target.files[0])
                  }
                />

              </div>

              {/* ANONYMOUS */}

              <div
                className={
                  anonymous
                    ? "anonymous-complaint-box selected"
                    : "anonymous-complaint-box"
                }
              >

                <label className="anonymous-check-label">

                  <input
                    type="checkbox"
                    checked={anonymous}
                    onChange={(e) =>
                      setAnonymous(e.target.checked)
                    }
                  />

                  <span className="login-custom-checkbox">

                    {anonymous ? "✓" : ""}

                  </span>

                  <span>

                    <strong>
                      Submit this complaint anonymously
                    </strong>

                    <small>
                      Your identity will not be displayed
                      with this complaint.
                    </small>

                  </span>

                </label>

                {anonymous && (

                  <div className="anonymous-information">

                    <strong>
                      Please note
                    </strong>

                    <p>
                      Your identity will be kept private
                      from other users. The information
                      provided in this complaint will be
                      considered for verification and
                      necessary action by the concerned
                      authority.
                    </p>

                  </div>

                )}

              </div>

              {/* BUTTONS */}

              <div className="complaint-actions">

                <button
                  type="button"
                  className="cancel-button"
                  onClick={handleClear}
                  disabled={loading}
                >
                  Clear
                </button>

                <button
                  type="submit"
                  className="complaint-button"
                  disabled={loading}
                >

                  {loading
                    ? "Submitting..."
                    : "Submit Complaint"}

                </button>

              </div>

            </form>

          </section>

        )}

        {/* CITIZEN LINKS */}

        <nav className="citizen-links">

          <Link to="/citizen/track">
            Track Complaint
          </Link>

          <Link to="/citizen/danger">
            Danger Zones
          </Link>

          <Link to="/citizen/profile">
            My Profile
          </Link>

        </nav>

      </main>

    </div>
  );
}

export default ReportIssue;