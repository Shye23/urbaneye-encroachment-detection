import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

function Register() {
  const navigate = useNavigate();

  const [role, setRole] = useState("citizen");

  const [fullName, setFullName] = useState("");
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();

    setError("");

    // Check passwords
    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    // Split Full Name into first_name and last_name
    const nameParts = fullName.trim().split(/\s+/);

    const firstName = nameParts[0] || "";
    const lastName = nameParts.slice(1).join(" ");

    setLoading(true);

    try {
      const response = await fetch(
        "http://127.0.0.1:8000/api/auth/register/",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            username: username,
            email: email,
            password: password,
            first_name: firstName,
            last_name: lastName,
          }),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        // Show backend validation errors
        const errorMessage =
          data.username?.[0] ||
          data.email?.[0] ||
          data.password?.[0] ||
          "Registration failed.";

        setError(errorMessage);
        return;
      }

      alert("Account created successfully!");

      navigate("/signin");

    } catch (err) {
      setError(
        "Cannot connect to backend. Make sure Django server is running."
      );
    } finally {
      setLoading(false);
    }
  };


  return (
    <div className="auth-page">

      <div className="auth-box">

        <Link
          to="/"
          className="auth-brand"
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


        <h1>
          Create Account
        </h1>

        <p className="auth-description">
          Register for access to the UrbanEye portal.
        </p>


        <div className="role-title">
          ACCOUNT TYPE
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


        {error && (
          <p style={{ color: "red", marginBottom: "15px" }}>
            {error}
          </p>
        )}


        <form onSubmit={handleSubmit}>

          <div className="form-group">

            <label>
              FULL NAME
            </label>

            <input
              type="text"
              placeholder="Enter full name"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              required
            />

          </div>


          {/* NEW USERNAME FIELD */}

          <div className="form-group">

            <label>
              USERNAME
            </label>

            <input
              type="text"
              placeholder="Choose a username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
            />

          </div>


          <div className="form-group">

            <label>
              EMAIL
            </label>

            <input
              type="email"
              placeholder="Enter email address"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />

          </div>


          <div className="form-group">

            <label>
              PASSWORD
            </label>

            <input
              type="password"
              placeholder="Create password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />

          </div>


          <div className="form-group">

            <label>
              CONFIRM PASSWORD
            </label>

            <input
              type="password"
              placeholder="Confirm password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
            />

          </div>


          <button
            type="submit"
            className="login-button"
            disabled={loading}
          >
            {loading ? "Creating Account..." : "Create Account"}
          </button>

        </form>


        <p className="auth-bottom">

          Already have an account?{" "}

          <Link to="/signin">
            Sign In
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

export default Register;