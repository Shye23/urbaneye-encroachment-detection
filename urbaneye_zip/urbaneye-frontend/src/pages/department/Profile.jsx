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
        "Failed to load profile:",
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

    return "D";
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

          <div className="profile-loading-card">

            <div className="profile-spinner" />

            <h2>
              Loading Profile
            </h2>

            <p>
              Fetching your department account
              information...
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
            {profile?.role_label ||
              "Department Officer"}
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
        <div className="page-heading">

          <div>

            <p className="page-label">
              DEPARTMENT PORTAL
            </p>

            <h1>
              My Profile
            </h1>

            <p>
              View your UrbanEye department
              officer account information.
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
          <div className="profile-error">
            <span>!</span>
            <p>
              {error}
            </p>
          </div>
        )}


        {profile && (
          <>
            {/* PROFILE HERO */}
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
                      "Department Officer"}
                  </p>

                </div>

              </div>

            </section>


            {/* ACCOUNT DETAILS */}
            <section className="department-profile-details">

              <div className="department-profile-section-header">

                <div>
                  <span className="department-profile-eyebrow">
                    ACCOUNT INFORMATION
                  </span>

                  <h2>
                    Personal Details
                  </h2>

                  <p>
                    Information associated with
                    your UrbanEye account.
                  </p>
                </div>

              </div>


              <div className="department-profile-grid">

                {/* FULL NAME */}
                <div className="department-profile-field">

                  <span>
                    Full Name
                  </span>

                  <strong>
                    {profile.full_name ||
                      "Not available"}
                  </strong>

                </div>


                {/* USERNAME */}
                <div className="department-profile-field">

                  <span>
                    Username
                  </span>

                  <strong>
                    @{profile.username}
                  </strong>

                </div>


                {/* EMAIL */}
                <div className="department-profile-field">

                  <span>
                    Email Address
                  </span>

                  <strong>
                    {profile.email ||
                      "Not available"}
                  </strong>

                </div>


                {/* ROLE */}
                <div className="department-profile-field">

                  <span>
                    Account Role
                  </span>

                  <strong>
                    {profile.role_label ||
                      profile.role}
                  </strong>

                </div>


                {/* ACCOUNT STATUS */}
                <div className="department-profile-field">

                  <span>
                    Account Status
                  </span>

                  <strong className="profile-active-text">
                    {profile.status}
                  </strong>

                </div>


                {/* ACCOUNT ID */}
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


            {/* ACCESS INFORMATION */}
            <section className="department-access-card">

              <div className="department-access-icon">
                ✓
              </div>

              <div>

                <span className="department-profile-eyebrow">
                  DEPARTMENT ACCESS
                </span>

                <h3>
                  Officer Workspace
                </h3>

                <p>
                  Your account can access cases
                  assigned to you and record
                  case actions and resolution
                  history.
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