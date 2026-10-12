import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { apiJson, logout } from "../../api";

function Profile() {
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchProfile = async () => {
      try {
        const data = await apiJson("/auth/profile/");
        setProfile(data);
      } catch (err) {
        console.error("Profile fetch error:", err);
        setError(err.message || "Unable to load profile.");
      } finally {
        setLoading(false);
      }
    };

    fetchProfile();
  }, []);

  const displayName =
    profile?.full_name ||
    profile?.username ||
    "Citizen";

  const displayEmail =
    profile?.email ||
    "No email available";

  const avatarLetter =
    displayName.charAt(0).toUpperCase();

  return (
    <div className="portal-page">

      <header className="portal-header">

        <Link
          to="/citizen"
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

          <Link to="/citizen">
            Dashboard
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
              CITIZEN PORTAL
            </p>

            <h1>
              My Profile
            </h1>

            <p>
              View your UrbanEye account information.
            </p>

          </div>

        </div>


        {loading && (
          <section className="profile-card">
            <p>
              Loading profile...
            </p>
          </section>
        )}


        {error && !loading && (
          <section className="profile-card">
            <p>
              {error}
            </p>
          </section>
        )}


        {!loading && !error && profile && (
          <section className="profile-card">

            <div className="profile-header">

              <div className="profile-avatar-large">
                {avatarLetter}
              </div>

              <div className="profile-header-info">

                <h3>
                  {displayName}
                </h3>

                <p>
                  {displayEmail}
                </p>

                <span className="profile-status">
                  {profile.status}
                </span>

              </div>

            </div>


            <div className="profile-divider"></div>


            <div className="profile-section">

              <h3 className="profile-section-title">
                Personal Information
              </h3>


              <div className="profile-grid">

                <div className="profile-field">

                  <label>
                    FULL NAME
                  </label>

                  <input
                    value={displayName}
                    readOnly
                  />

                </div>


                <div className="profile-field">

                  <label>
                    EMAIL
                  </label>

                  <input
                    value={displayEmail}
                    readOnly
                  />

                </div>

              </div>

            </div>


            <div className="profile-section">

              <h3 className="profile-section-title">
                Preferences
              </h3>


              <div className="profile-preferences">

                <div className="preference-row">

                  <div>

                    <strong>
                      Complaint Notifications
                    </strong>

                    <span>
                      Receive updates about your complaints.
                    </span>

                  </div>

                  <input
                    type="checkbox"
                    defaultChecked
                  />

                </div>


                <div className="preference-row">

                  <div>

                    <strong>
                      Privacy Protection
                    </strong>

                    <span>
                      Keep anonymous complaint identity
                      protected.
                    </span>

                  </div>

                  <input
                    type="checkbox"
                    defaultChecked
                  />

                </div>

              </div>

            </div>

          </section>
        )}

      </main>

    </div>
  );
}

export default Profile;