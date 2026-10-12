import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { apiJson, logout } from "../../api";

function Complaints() {
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
        console.error("Failed to load admin complaints:", err);
        setError(err.message || "Unable to load complaints.");
      } finally {
        setLoading(false);
      }
    };

    loadComplaints();
  }, []);

  const getCategoryLabel = (category) => {
    const categoryLabels = {
      ENCROACHMENT: "Encroachment",
      ROAD: "Road Issue",
      FOOTPATH: "Footpath",
      PUBLIC_LAND: "Public Land",
      OTHER: "Other",
    };

    return categoryLabels[category] || category;
  };

  const getStatusLabel = (status) => {
    const statusLabels = {
      PENDING: "Pending",
      UNDER_REVIEW: "Under Review",
      VERIFIED: "Verified",
      REJECTED: "Rejected",
      RESOLVED: "Resolved",
    };

    return statusLabels[status] || status;
  };

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
              Complaints
            </h1>

            <p>
              Review and manage citizen complaints.
            </p>

          </div>

          <Link
            to="/admin"
            className="outline-button"
          >
            ← Dashboard
          </Link>

        </div>


        {loading && (
          <section className="data-card">
            <div className="data-row">
              <span>Loading complaints...</span>
            </div>
          </section>
        )}


        {error && !loading && (
          <section className="data-card">
            <div className="data-row">
              <span>{error}</span>
            </div>
          </section>
        )}


        {!loading && !error && complaints.length === 0 && (
          <section className="data-card">

            <div className="data-row">

              <span>
                No complaints found.
              </span>

            </div>

          </section>
        )}


        {!loading && !error && complaints.length > 0 && (
          <section className="data-card">

            <div className="data-row data-header">

              <span>
                ID
              </span>

              <span>
                Category
              </span>

              <span>
                Status
              </span>

              <span>
                Action
              </span>

            </div>


            {complaints.map((complaint) => (

              <div
                className="data-row"
                key={complaint.id}
              >

                <span>
                  UE-{complaint.id}
                </span>

                <span>
                  {getCategoryLabel(complaint.category)}
                </span>

                <span className="status-badge">
                  {getStatusLabel(complaint.status)}
                </span>

                <button
                  type="button"
                  onClick={() =>
                    alert(
                      `Complaint UE-${complaint.id}\n\nTitle: ${complaint.title}\n\nDescription: ${complaint.description}\n\nAddress: ${complaint.address || "Not provided"}`
                    )
                  }
                >
                  View
                </button>

              </div>

            ))}

          </section>
        )}

      </main>

    </div>
  );
}

export default Complaints;