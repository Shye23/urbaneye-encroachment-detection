import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { apiJson, logout } from "../../api";

function Profile() {
  const [profile, setProfile] = useState(null);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    loadProfile();
  }, []);

  const loadProfile = async () => {
    try {
      setLoading(true);
      setError("");

      const data = await apiJson("/auth/profile/");

      setProfile(data);
    } catch (err) {
      console.error(
        "Failed to load admin profile:",
        err
      );

      setError(
        err.message ||
          "Unable to load profile information."
      );
    } finally {
      setLoading(false);
    }
  };

  const getInitial = () => {
    if (profile?.full_name) {
      return profile.full_name
        .charAt(0)
        .toUpperCase();
    }

    if (profile?.username) {
      return profile.username
        .charAt(0)
        .toUpperCase();
    }

    return "A";
  };

  if (loading) {
    return (
      <div className="portal-page">

        <header className="portal-header">

          <Link
            to="/admin"
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

          <div className="profile-loading-card">

            <div className="profile-spinner" />

            <h2>
              Loading Profile
            </h2>

            <p>
              Fetching your administrator
              account information...
            </p>

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
            {profile?.role_label ||
              "Administrator"}
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

        {/* PAGE HEADING */}
        <div className="page-heading">

          <div>

            <p className="page-label">
              ADMIN PORTAL
            </p>

            <h1>
              My Profile
            </h1>

            <p>
              View your UrbanEye administrator
              account information.
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
          <div className="profile-error">

            <span>
              !
            </span>

            <p>
              {error}
            </p>

          </div>
        )}


        {profile && (
          <>
            {/* PROFILE HEADER */}
            <section className="department-profile-card">

              <div className="department-profile-header">

                <div className="department-profile-avatar">
                  {getInitial()}
                </div>


                <div className="department-profile-main">

                  <div className="department-profile-name-row">

                    <h2>
                      {profile.full_name}
                    </h2>

                    <span className="department-profile-status">
                      {profile.status}
                    </span>

                  </div>

                  <p className="department-profile-username">
                    @{profile.username}
                  </p>

                  <p className="department-profile-role">
                    {profile.role_label ||
                      "Administrator"}
                  </p>

                </div>

              </div>

            </section>


            {/* ACCOUNT INFORMATION */}
            <section className="department-profile-details">

              <div className="department-profile-section-header">

                <div>

                  <span className="department-profile-eyebrow">
                    ACCOUNT INFORMATION
                  </span>

                  <h2>
                    Administrator Details
                  </h2>

                  <p>
                    Information associated with
                    your UrbanEye administrator account.
                  </p>

                </div>

              </div>


              <div className="department-profile-grid">

                <div className="department-profile-field">

                  <span>
                    Full Name
                  </span>

                  <strong>
                    {profile.full_name ||
                      "Not available"}
                  </strong>

                </div>


                <div className="department-profile-field">

                  <span>
                    Username
                  </span>

                  <strong>
                    @{profile.username}
                  </strong>

                </div>


                <div className="department-profile-field">

                  <span>
                    Email Address
                  </span>

                  <strong>
                    {profile.email ||
                      "Not available"}
                  </strong>

                </div>


                <div className="department-profile-field">

                  <span>
                    Account Role
                  </span>

                  <strong>
                    {profile.role_label ||
                      profile.role}
                  </strong>

                </div>


                <div className="department-profile-field">

                  <span>
                    Account Status
                  </span>

                  <strong className="profile-active-text">
                    {profile.status}
                  </strong>

                </div>


                <div className="department-profile-field">

                  <span>
                    Account ID
                  </span>

                  <strong>
                    #{profile.id}
                  </strong>

                </div>

              </div>

            </section>


            {/* ADMIN ACCESS */}
            <section className="department-access-card">

              <div className="department-access-icon">
                ✓
              </div>

              <div>

                <span className="department-profile-eyebrow">
                  ADMIN ACCESS
                </span>

                <h3>
                  Administrator Workspace
                </h3>

                <p>
                  Your administrator account can
                  manage complaints, encroachment
                  cases, department officers,
                  assignments, reports and system
                  information.
                </p>

              </div>

            </section>

          </>
        )}

      </main>

    </div>
  );
}

export default Profile;