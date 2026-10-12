import React from "react";
import { Link } from "react-router-dom";

function Layout({
  children,
  role = "citizen",
}) {
  return (
    <div className="portal-page">

      <header className="portal-header">

        <Link
          to={
            role === "admin"
              ? "/admin"
              : role === "department"
              ? "/department"
              : "/citizen/report"
          }
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
            {role === "admin"
              ? "Admin"
              : role === "department"
              ? "Department"
              : "Citizen"}
          </span>

          <Link to="/">
            Sign Out
          </Link>

        </div>

      </header>


      {children}

    </div>
  );
}

export default Layout;