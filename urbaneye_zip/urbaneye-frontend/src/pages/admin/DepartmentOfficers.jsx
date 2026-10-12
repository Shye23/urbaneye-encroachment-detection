import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { apiJson, logout } from "../../api";

function DepartmentOfficers() {
  const [officers, setOfficers] = useState([]);

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const [showForm, setShowForm] = useState(false);

  const [formData, setFormData] = useState({
    first_name: "",
    last_name: "",
    username: "",
    email: "",
    password: "",
    password_confirm: "",
  });

  useEffect(() => {
    loadOfficers();
  }, []);

  const loadOfficers = async () => {
    try {
      setLoading(true);
      setError("");

      const data = await apiJson(
        "/auth/admin/department-officers/"
      );

      const officerList = Array.isArray(data)
        ? data
        : Array.isArray(data?.results)
        ? data.results
        : [];

      setOfficers(officerList);
    } catch (err) {
      console.error(
        "Failed to load department officers:",
        err
      );

      setError(
        err.message ||
          "Unable to load department officers."
      );
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (event) => {
    const { name, value } = event.target;

    setFormData((previous) => ({
      ...previous,
      [name]: value,
    }));
  };

  const resetForm = () => {
    setFormData({
      first_name: "",
      last_name: "",
      username: "",
      email: "",
      password: "",
      password_confirm: "",
    });
  };

  const handleCreateOfficer = async (event) => {
    event.preventDefault();

    try {
      setSaving(true);
      setError("");
      setSuccess("");

      const data = await apiJson(
        "/auth/admin/department-officers/create/",
        {
          method: "POST",
          body: JSON.stringify(formData),
        }
      );

      setSuccess(
        data.message ||
          "Department Officer created successfully."
      );

      resetForm();
      setShowForm(false);

      await loadOfficers();
    } catch (err) {
      console.error(
        "Failed to create department officer:",
        err
      );

      setError(
        err.message ||
          "Unable to create department officer."
      );
    } finally {
      setSaving(false);
    }
  };

  const handleToggleForm = () => {
    setShowForm((previous) => !previous);
    setError("");
    setSuccess("");

    if (showForm) {
      resetForm();
    }
  };

  const getInitial = (officer) => {
    const name =
      officer.full_name ||
      officer.username ||
      "D";

    return name.charAt(0).toUpperCase();
  };

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


      {/* MAIN */}
      <main className="portal-content">

        {/* PAGE HEADING */}
        <div className="officer-page-heading">

          <div>

            <p className="page-label">
              ADMIN PORTAL
            </p>

            <h1>
              Department Officers
            </h1>

            <p>
              Create and manage department officer
              accounts for UrbanEye.
            </p>

          </div>

          <Link
            to="/admin"
            className="officer-back-link"
          >
            ← Dashboard
          </Link>

        </div>


        {/* MESSAGES */}
        {error && (
          <div className="officer-message officer-message-error">

            <span className="officer-message-icon">
              !
            </span>

            <div>
              {error}
            </div>

          </div>
        )}

        {success && (
          <div className="officer-message officer-message-success">

            <span className="officer-message-icon">
              ✓
            </span>

            <div>
              {success}
            </div>

          </div>
        )}


        {/* OFFICER MANAGEMENT */}
        <section className="officer-management-card">

          <div className="officer-card-header">

            <div className="officer-card-header-left">

              <span className="officer-card-eyebrow">
                OFFICER MANAGEMENT
              </span>

              <h2>
                Department Officers
              </h2>

              <p>
                Active officers available for
                encroachment case assignment.
              </p>

            </div>


            <div className="officer-total-badge">

              <span>
                Active
              </span>

              <strong>
                {loading ? "—" : officers.length}
              </strong>

            </div>


            <button
              type="button"
              className="officer-create-button"
              onClick={handleToggleForm}
            >
              {showForm
                ? "Close Form"
                : "+ Create Officer"}
            </button>

          </div>


          {/* CREATE OFFICER FORM */}
          {showForm && (

            <form
              onSubmit={handleCreateOfficer}
              className="officer-create-form"
              autoComplete="off"
            >

              <div className="officer-form-title">

                <h3>
                  Create Department Officer
                </h3>

                <p>
                  Create an account with Department
                  access. The officer can use these
                  credentials to sign in.
                </p>

              </div>


              <div className="officer-form-grid">

                {/* FIRST NAME */}
                <div className="officer-form-group">

                  <label htmlFor="first_name">
                    First Name
                  </label>

                  <input
                    id="first_name"
                    type="text"
                    name="first_name"
                    value={formData.first_name}
                    onChange={handleChange}
                    placeholder="Enter first name"
                    autoComplete="given-name"
                    required
                    disabled={saving}
                  />

                </div>


                {/* LAST NAME */}
                <div className="officer-form-group">

                  <label htmlFor="last_name">
                    Last Name
                  </label>

                  <input
                    id="last_name"
                    type="text"
                    name="last_name"
                    value={formData.last_name}
                    onChange={handleChange}
                    placeholder="Enter last name"
                    autoComplete="family-name"
                    required
                    disabled={saving}
                  />

                </div>


                {/* USERNAME */}
                <div className="officer-form-group">

                  <label htmlFor="username">
                    Username
                  </label>

                  <input
                    id="username"
                    type="text"
                    name="username"
                    value={formData.username}
                    onChange={handleChange}
                    placeholder="Create login username"
                    autoComplete="off"
                    required
                    disabled={saving}
                  />

                </div>


                {/* EMAIL */}
                <div className="officer-form-group">

                  <label htmlFor="email">
                    Email Address
                  </label>

                  <input
                    id="email"
                    type="email"
                    name="email"
                    value={formData.email}
                    onChange={handleChange}
                    placeholder="officer@urbaneye.local"
                    autoComplete="email"
                    required
                    disabled={saving}
                  />

                </div>


                {/* PASSWORD */}
                <div className="officer-form-group">

                  <label htmlFor="password">
                    Temporary Password
                  </label>

                  <input
                    id="password"
                    type="password"
                    name="password"
                    value={formData.password}
                    onChange={handleChange}
                    placeholder="Minimum 8 characters"
                    autoComplete="new-password"
                    minLength={8}
                    required
                    disabled={saving}
                  />

                </div>


                {/* CONFIRM PASSWORD */}
                <div className="officer-form-group">

                  <label htmlFor="password_confirm">
                    Confirm Password
                  </label>

                  <input
                    id="password_confirm"
                    type="password"
                    name="password_confirm"
                    value={
                      formData.password_confirm
                    }
                    onChange={handleChange}
                    placeholder="Re-enter password"
                    autoComplete="new-password"
                    minLength={8}
                    required
                    disabled={saving}
                  />

                </div>

              </div>


              {/* PASSWORD NOTE */}
              <div className="officer-password-note">

                <div className="officer-password-note-icon">
                  i
                </div>

                <div>

                  <strong>
                    Temporary credentials
                  </strong>

                  <span>
                    Share the username and temporary
                    password securely with the
                    department officer.
                  </span>

                </div>

              </div>


              {/* ACTIONS */}
              <div className="officer-form-actions">

                <button
                  type="button"
                  className="officer-cancel-button"
                  onClick={() => {
                    setShowForm(false);
                    resetForm();
                    setError("");
                  }}
                  disabled={saving}
                >
                  Cancel
                </button>

                <button
                  type="submit"
                  className="officer-save-button"
                  disabled={saving}
                >
                  {saving
                    ? "Creating Officer..."
                    : "Create Officer"}
                </button>

              </div>

            </form>
          )}


          {/* OFFICER LIST */}
          {!loading &&
            officers.length > 0 && (

              <div className="officer-list">

                {officers.map((officer) => (

                  <div
                    key={officer.id}
                    className="officer-list-item"
                  >

                    {/* AVATAR */}
                    <div className="officer-avatar">
                      {getInitial(officer)}
                    </div>


                    {/* MAIN INFORMATION */}
                    <div className="officer-list-main">

                      <div className="officer-name-row">

                        <h3>
                          {officer.full_name ||
                            officer.username}
                        </h3>

                        <span className="officer-active-badge">
                          Active
                        </span>

                      </div>

                      <p className="officer-username">
                        @{officer.username}
                      </p>

                    </div>


                    {/* META */}
                    <div className="officer-meta">

                      <div className="officer-meta-item">

                        <span>
                          Email
                        </span>

                        <strong>
                          {officer.email ||
                            "Not available"}
                        </strong>

                      </div>


                      <div className="officer-meta-item">

                        <span>
                          Role
                        </span>

                        <strong>
                          Department Officer
                        </strong>

                      </div>

                    </div>

                  </div>

                ))}

              </div>
            )}


          {/* LOADING */}
          {loading && (
            <div className="officer-loading">
              Loading department officers...
            </div>
          )}


          {/* EMPTY */}
          {!loading &&
            officers.length === 0 && (

              <div className="officer-empty">

                <div className="officer-empty-icon">
                  D
                </div>

                <h3>
                  No Department Officers
                </h3>

                <p>
                  Create a department officer account
                  to make them available for case
                  assignment.
                </p>

              </div>
            )}

        </section>

      </main>

    </div>
  );
}

export default DepartmentOfficers;