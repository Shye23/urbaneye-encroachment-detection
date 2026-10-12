import React from "react";
import { Link } from "react-router-dom";
import { logout } from "../../api";

function SafetyZone() {
  const safetyTips = [
    {
      title: "Stay Alert",
      description:
        "Stay aware of your surroundings, especially in crowded or high-risk public areas.",
      icon: "!",
    },
    {
      title: "Avoid Unsafe Areas",
      description:
        "Avoid areas marked as high-risk and follow local safety instructions when available.",
      icon: "✓",
    },
    {
      title: "Report Civic Issues",
      description:
        "Report encroachment, damaged roads, blocked footpaths and other civic issues through UrbanEye.",
      icon: "+",
    },
    {
      title: "Emergency Assistance",
      description:
        "For immediate danger or emergencies, contact the appropriate emergency services.",
      icon: "☎",
    },
  ];

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

            <h1>Safety Zone</h1>

            <p>
              Stay informed and follow simple safety practices while using
              public spaces.
            </p>
          </div>
        </div>

        <section className="safety-zone-intro">
          <div className="safety-zone-icon">✓</div>

          <div>
            <h2>Stay Safe with UrbanEye</h2>

            <p>
              UrbanEye helps citizens stay informed about civic issues and
              reported risk areas. Use the information available in the
              portal and report issues that may affect public safety.
            </p>
          </div>
        </section>

        <section className="safety-tips-section">
          <h2>Safety Guidelines</h2>

          <div className="safety-tips-grid">
            {safetyTips.map((tip) => (
              <article className="safety-tip-card" key={tip.title}>
                <div className="safety-tip-icon">
                  {tip.icon}
                </div>

                <div>
                  <h3>{tip.title}</h3>

                  <p>{tip.description}</p>
                </div>
              </article>
            ))}
          </div>
        </section>

        <section className="safety-zone-actions">
          <Link to="/citizen/danger" className="safety-action-button">
            View Danger Zones →
          </Link>

          <Link to="/citizen/report" className="safety-action-button">
            Report an Issue →
          </Link>
        </section>
      </main>
    </div>
  );
}

export default SafetyZone;