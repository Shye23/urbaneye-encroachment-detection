import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { apiJson } from "../../api";

function SignIn() {
  const navigate = useNavigate();

  const [role, setRole] = useState("citizen");
  const [anonymous, setAnonymous] = useState(false);

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e) => {
  e.preventDefault();

  setError("");
  setLoading(true);

  try {
    const data = await apiJson(
      "/auth/login/",
      {
        method: "POST",
        body: JSON.stringify({
          username: email,
          password: password,
        }),
      }
    );

    // Save JWT tokens
    localStorage.setItem("access_token", data.access);
    localStorage.setItem("refresh_token", data.refresh);
    localStorage.setItem("username", data.username);
    localStorage.setItem("role", role);

    // Save anonymous preference
    localStorage.setItem(
      "anonymous_complaint",
      anonymous ? "true" : "false"
    );

    // Redirect according to role
    if (role === "citizen") {
      navigate("/citizen");
    } else if (role === "admin") {
      navigate("/admin");
    } else if (role === "department") {
      navigate("/department");
    }
  } catch (err) {
    setError(err.message);
  } finally {
    setLoading(false);
  }
};

  return (
    <div className="auth-page">

      <div className="auth-box">

        <Link to="/" className="auth-brand">

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

        <h1>
          Sign In
        </h1>

        <p className="auth-description">
          Access the UrbanEye portal according
          to your role.
        </p>

        <div className="role-title">
          SELECT YOUR ROLE
        </div>

        <div className="role-buttons">

          <button
            type="button"
            className={
              role === "citizen"
                ? "role-button active"
                : "role-button"
            }
            onClick={() => setRole("citizen")}
          >
            Citizen
          </button>

          <button
            type="button"
            className={
              role === "admin"
                ? "role-button active"
                : "role-button"
            }
            onClick={() => setRole("admin")}
          >
            Admin
          </button>

          <button
            type="button"
            className={
              role === "department"
                ? "role-button active"
                : "role-button"
            }
            onClick={() => setRole("department")}
          >
            Department
          </button>

        </div>

        {/* ERROR MESSAGE */}

        {error && (
          <div className="auth-error">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>

          <div className="form-group">

            <label>
              EMAIL / USERNAME
            </label>

            <input
              type="text"
              value={email}
              onChange={(e) =>
                setEmail(e.target.value)
              }
              placeholder="Enter your username"
              required
            />

          </div>

          <div className="form-group">

            <label>
              PASSWORD
            </label>

            <input
              type="password"
              value={password}
              onChange={(e) =>
                setPassword(e.target.value)
              }
              placeholder="Enter your password"
              required
            />

          </div>

          {/* CITIZEN ANONYMOUS OPTION */}

          {role === "citizen" && (

            <div
              className={
                anonymous
                  ? "login-anonymous-box selected"
                  : "login-anonymous-box"
              }
            >

              <label className="login-anonymous-label">

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

                <span className="login-anonymous-text">

                  <strong>
                    Submit complaint anonymously
                  </strong>

                  <small>
                    Choose this option if you do not
                    want your identity to be displayed
                    with your complaint.
                  </small>

                </span>

              </label>

              {anonymous && (

                <div className="login-anonymous-message">

                  <strong>
                    Anonymous Complaint Information
                  </strong>

                  <p>
                    Your identity will not be displayed
                    to other users with the complaint.
                    The information you submit will be
                    considered for verification and
                    appropriate action by the concerned
                    authority.
                  </p>

                </div>

              )}

            </div>

          )}

          <button
            type="submit"
            className="login-button"
            disabled={loading}
          >
            {loading
              ? "Signing In..."
              : `Sign In as ${
                  role === "citizen"
                    ? "Citizen"
                    : role === "admin"
                    ? "Admin"
                    : "Department"
                }`
            }
          </button>

        </form>

        <p className="auth-bottom">

          Don't have an account?{" "}

          <Link to="/register">
            Register
          </Link>

        </p>

        <Link
          to="/"
          className="back-home"
        >
          ← Back to Home
        </Link>

      </div>

    </div>
  );
}

export default SignIn;