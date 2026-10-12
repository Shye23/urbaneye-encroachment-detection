import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { apiFetch, apiJson, logout } from "../../api";

function Reports() {
  const [jobs, setJobs] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    apiJson("/detections/reports/")
      .then(setJobs)
      .catch((err) => setError(err.message || "Unable to load reports."));
  }, []);

  const downloadReport = async (job, artifact) => {
    const response = await apiFetch(
      `/detections/${job.id}/artifacts/${artifact.id}/download/`
    );
    if (!response.ok) {
      setError("The PDF report is unavailable.");
      return;
    }
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = artifact.name;
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="portal-page">

      <header className="portal-header">

        <div className="portal-brand">

          <div className="brand-mark">
            UE
          </div>

          <div className="brand-text">
            <strong>UrbanEye</strong>
            <span>
              Encroachment Detection System
            </span>
          </div>

        </div>

      </header>


      <main className="portal-content">

        <div className="page-heading">

          <div>

            <p className="page-label">
              ADMIN PORTAL
            </p>

            <h1>
              Reports
            </h1>

            <p>View detection job history and download official reports.</p>

          </div>

        </div>


        {error && <div className="complaint-dashboard-error">{error}</div>}
        <section className="empty-admin-card">
          <h2>Detection job history</h2>
          {jobs.length === 0 && <p>No detection jobs are available yet.</p>}
          {jobs.map((job) => {
            const pdf = job.artifacts?.find(
              (artifact) =>
                artifact.kind === "REPORT" &&
                artifact.name.toLowerCase().endsWith(".pdf")
            );
            return (
              <div className="report-job-row" key={job.id}>
                <div>
                  <strong>Job #{job.id}</strong>
                  <span>{job.start_date} to {job.end_date}</span>
                </div>
                <strong>{job.status === "SUCCEEDED" ? "Passed" : "Failed"}</strong>
                {pdf && (
                  <button
                    type="button"
                    className="outline-button"
                    onClick={() => downloadReport(job, pdf)}
                  >
                    Download PDF report
                  </button>
                )}
              </div>
            );
          })}
        </section>

      </main>

    </div>
  );
}

export default Reports;