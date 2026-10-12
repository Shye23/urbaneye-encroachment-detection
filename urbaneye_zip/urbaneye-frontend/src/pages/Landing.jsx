import React from "react";
import { Link } from "react-router-dom";

function Landing() {
  return (
    <div className="landing-page">

      <header className="landing-header">

        <Link to="/" className="brand">

          <div className="brand-mark">
            UE
          </div>

          <div className="brand-text">
            <strong>UrbanEye</strong>
            <span>Encroachment Detection System</span>
          </div>

        </Link>


        <nav className="landing-nav">

          <a href="#about">
            About
          </a>

          <a href="#features">
            Features
          </a>

          <a href="#how">
            How It Works
          </a>

        </nav>


        <div className="header-actions">

          <Link
            to="/signin"
            className="outline-button"
          >
            Sign In
          </Link>

          <Link
            to="/register"
            className="primary-button"
          >
            Register
          </Link>

        </div>

      </header>


      <main className="landing-main">

        <section className="hero-content">

          <p className="small-heading">
            SMARTER • SAFER • BETTER CITIES
          </p>

          <h1>
            UrbanEye
            <br />
            <span>
              Encroachment Detection System
            </span>
          </h1>

          <p>
            A simple digital platform for citizens,
            government departments and administrators
            to report, monitor and manage urban
            encroachments and civic issues.
          </p>


          <div className="hero-buttons">

            <Link
              to="/signin"
              className="primary-button"
            >
              Get Started
            </Link>

            <a
              href="#about"
              className="outline-button"
            >
              Learn More
            </a>

          </div>

        </section>


        <section className="hero-visual">

          <div className="city-card">

            <div className="city-sun"></div>

            <div className="city-building building-one">
              <span></span>
              <span></span>
              <span></span>
            </div>

            <div className="city-building building-two">
              <span></span>
              <span></span>
              <span></span>
              <span></span>
            </div>

            <div className="city-building building-three">
              <span></span>
              <span></span>
              <span></span>
            </div>

            <div className="city-road"></div>

          </div>

        </section>

      </main>


      <section
        id="about"
        className="simple-section"
      >

        <p className="small-heading">
          ABOUT URBANEYE
        </p>

        <h2>
          Making urban monitoring simpler.
        </h2>

        <p>
          UrbanEye connects citizens and authorities
          through one easy-to-use platform.
        </p>

      </section>


      <section
        id="features"
        className="simple-section"
      >

        <p className="small-heading">
          FEATURES
        </p>

        <div className="feature-grid">

          <div className="feature-card">

            <h3>
              Citizen Reporting
            </h3>

            <p>
              Citizens can report encroachments and
              other civic issues directly through the
              portal.
            </p>

          </div>


          <div className="feature-card">

            <h3>
              Detection
            </h3>

            <p>
              Authorities can review reported locations
              and detected encroachment information.
            </p>

          </div>


          <div className="feature-card">

            <h3>
              Transparent Tracking
            </h3>

            <p>
              Citizens can track the progress of their
              submitted complaints.
            </p>

          </div>

        </div>

      </section>


      <section
        id="how"
        className="simple-section"
      >

        <p className="small-heading">
          HOW IT WORKS
        </p>

        <h2>
          Report. Review. Resolve.
        </h2>

        <p>
          Citizens submit information, departments
          review and process it, and administrators
          monitor the overall system.
        </p>

      </section>

    </div>
  );
}

export default Landing;