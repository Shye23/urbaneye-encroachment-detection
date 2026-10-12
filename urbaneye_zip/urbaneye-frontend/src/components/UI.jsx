import React from "react";

export function PageTitle({
  label,
  title,
  description,
}) {
  return (
    <div className="page-heading">

      <div>

        <p className="page-label">
          {label}
        </p>

        <h1>
          {title}
        </h1>

        <p>
          {description}
        </p>

      </div>

    </div>
  );
}


export function StatusBadge({
  children,
}) {
  return (
    <span className="status-badge">
      {children}
    </span>
  );
}


export function EmptyState({
  title,
  message,
}) {
  return (
    <section className="empty-admin-card">

      <h2>
        {title}
      </h2>

      <p>
        {message}
      </p>

    </section>
  );
}