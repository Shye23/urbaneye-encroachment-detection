import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { apiJson, logout } from "../../api";

function Danger() {
  const [dangerZones, setDangerZones] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchDangerZones = async () => {
      try {
        const data = await apiJson("/complaints/danger-zones/");
        setDangerZones(Array.isArray(data) ? data : []);
      } catch (err) {
        console.error("Danger zones fetch error:", err);
        setError(err.message || "Unable to load danger zones.");
      } finally {
        setLoading(false);
      }
    };

    fetchDangerZones();
  }, []);

  const getRiskClass = (riskLevel) => {
    switch (riskLevel) {
      case "HIGH":
        return "high";
      case "MEDIUM":
        return "medium";
      case "LOW":
        return "low";
      default:
        return "medium";
    }
  };

  const getRiskLabel = (riskLevel) => {
    switch (riskLevel) {
      case "HIGH":
        return "HIGH RISK";
      case "MEDIUM":
        return "MEDIUM RISK";
      case "LOW":
        return "LOW RISK";
      default:
        return "MEDIUM RISK";
    }
  };

  const getRelativeTime = (dateString) => {
    if (!dateString) return "";

    const date = new Date(dateString);
    const now = new Date();

    const diffMs = now - date;
    const diffMinutes = Math.floor(diffMs / (1000 * 60));
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

    if (diffMinutes < 1) return "Just now";
    if (diffMinutes < 60) return `${diffMinutes} min ago`;
    if (diffHours < 24) return `${diffHours} hr ago`;
    if (diffDays === 1) return "Yesterday";
    if (diffDays < 7) return `${diffDays} days ago`;

    return date.toLocaleDateString();
  };

  return (
    <div className="portal-page">
      <header className="portal-header">
        <Link to="/citizen" className="portal-brand">
          <div className="brand-mark">UE</div>

          <div className="brand-text">
            <strong>UrbanEye</strong>
            <span>Encroachment Detection System</span>
          </div>
        </Link>

        <div className="portal-header-right">
          <span>Citizen</span>

          <Link to="/citizen/report">
            Report Issue
          </Link>

          <Link to="/citizen/profile">
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
            <p className="page-label">CITIZEN PORTAL</p>

            <h1>Danger Zones</h1>

            <p>
              Stay informed about areas with reported civic risks.
            </p>
          </div>
        </div>

        {loading && (
          <section className="danger-zones-section">
            <p>Loading danger zones...</p>
          </section>
        )}

        {error && !loading && (
          <section className="danger-zones-section">
            <p>{error}</p>
          </section>
        )}

        {!loading && !error && dangerZones.length === 0 && (
          <section className="danger-zones-section">
            <div className="empty-state">
              <h3>No danger zones available</h3>
              <p>
                There are currently no active danger zones to display.
              </p>
            </div>
          </section>
        )}

        {!loading && !error && dangerZones.length > 0 && (
          <section className="danger-zones-section">
            <div className="danger-zone-grid">
              {dangerZones.map((zone) => (
                <article
                  key={zone.id}
                  className={`danger-zone-card ${getRiskClass(
                    zone.risk_level
                  )}`}
                >
                  <div className="danger-zone-card-header">
                    <div>
                      <h3>{zone.name}</h3>

                      <span
                        className={`risk-badge ${getRiskClass(
                          zone.risk_level
                        )}`}
                      >
                        {getRiskLabel(zone.risk_level)}
                      </span>
                    </div>
                  </div>

                  <p className="danger-zone-description">
                    {zone.description}
                  </p>

                  {zone.address && (
                    <p className="danger-zone-address">
                      {zone.address}
                    </p>
                  )}

                  <div className="danger-zone-footer">
                    <span>
                      Updated {getRelativeTime(zone.updated_at)}
                    </span>
                  </div>
                </article>
              ))}
            </div>
          </section>
        )}
      </main>
    </div>
  );
}

export default Danger;