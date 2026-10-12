import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  MapContainer,
  TileLayer,
  GeoJSON,
  Rectangle,
  useMapEvents,
} from "react-leaflet";
import "leaflet/dist/leaflet.css";
import { apiFetch, apiJson, logout } from "../../api";

const DEFAULT_CENTER = [20.5937, 78.9629];
const DEFAULT_COLLECTION = "ResourceSat-2_LISS4-MX70_L2";

function AreaSelector({ onSelect }) {
  useMapEvents({
    click(event) {
      onSelect(event.latlng);
    },
  });

  return null;
}

function boundsToGeoJson(bounds) {
  const southWest = bounds[0];
  const northEast = bounds[1];
  return {
    type: "Polygon",
    coordinates: [[
      [southWest[1], southWest[0]],
      [northEast[1], southWest[0]],
      [northEast[1], northEast[0]],
      [southWest[1], northEast[0]],
      [southWest[1], southWest[0]],
    ]],
  };
}

function Detection() {
  const [corners, setCorners] = useState([]);
  const [startDate, setStartDate] = useState("2020-01-01");
  const [endDate, setEndDate] = useState("2024-12-31");
  const [collection, setCollection] = useState(DEFAULT_COLLECTION);
  const [job, setJob] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const aoi = corners.length === 2
    ? boundsToGeoJson([
      [
        Math.min(corners[0].lat, corners[1].lat),
        Math.min(corners[0].lng, corners[1].lng),
      ],
      [
        Math.max(corners[0].lat, corners[1].lat),
        Math.max(corners[0].lng, corners[1].lng),
      ],
    ])
    : null;

  useEffect(() => {
    if (!job || !["PENDING", "RUNNING"].includes(job.status)) {
      return undefined;
    }

    const poll = window.setInterval(async () => {
      try {
        const latest = await apiJson(`/detections/${job.id}/`);
        setJob(latest);
      } catch (err) {
        setError(err.message || "Unable to update detection status.");
      }
    }, 3000);

    return () => window.clearInterval(poll);
  }, [job]);

  const handleMapSelection = (latlng) => {
    if (corners.length === 2) {
      setCorners([latlng]);
    } else {
      setCorners((current) => [...current, latlng]);
    }
    setError("");
  };

  const submitJob = async (event) => {
    event.preventDefault();
    if (!aoi) {
      setError("Select an area by clicking two opposite corners on the map.");
      return;
    }

    try {
      setLoading(true);
      setError("");
      const created = await apiJson("/detections/", {
        method: "POST",
        body: JSON.stringify({
          aoi,
          start_date: startDate,
          end_date: endDate,
          collection,
        }),
      });
      setJob(created);
    } catch (err) {
      setError(err.message || "Unable to start detection.");
    } finally {
      setLoading(false);
    }
  };

  const resetJob = () => {
    setJob(null);
    setCorners([]);
    setError("");
  };

  return (
    <div className="portal-page">
      <header className="portal-header">
        <Link to="/admin" className="portal-brand">
          <div className="brand-mark">UE</div>
          <div className="brand-text">
            <strong>UrbanEye</strong>
            <span>Encroachment Detection System</span>
          </div>
        </Link>
        <div className="portal-header-right">
          <span>Admin</span>
          <Link to="/admin/profile">Profile</Link>
          <button type="button" onClick={logout} className="logout-button">
            Sign Out
          </button>
        </div>
      </header>

      <main className="portal-content">
        <div className="page-heading">
          <div>
            <p className="page-label">ADMIN PORTAL</p>
            <h1>Detection</h1>
            <p>Select an area and time range to find changes requiring verification.</p>
          </div>
          <Link to="/admin" className="outline-button">← Dashboard</Link>
        </div>

        {error && <div className="complaint-dashboard-error">{error}</div>}

        <section className="detection-layout">
          <div className="detection-map-panel">
            <div className="detection-map-help">
              Click two opposite corners to define the area of interest.
              Click again after the second corner to replace the selection.
            </div>
            <MapContainer center={DEFAULT_CENTER} zoom={5} className="detection-map">
              <TileLayer
                attribution="&copy; OpenStreetMap contributors"
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              />
              <AreaSelector onSelect={handleMapSelection} />
              {corners.length === 2 && (
                <Rectangle
                  bounds={[
                    [Math.min(corners[0].lat, corners[1].lat), Math.min(corners[0].lng, corners[1].lng)],
                    [Math.max(corners[0].lat, corners[1].lat), Math.max(corners[0].lng, corners[1].lng)],
                  ]}
                  pathOptions={{ color: "#8d390d", weight: 2 }}
                />
              )}
              {job?.candidates?.length > 0 && (
                <GeoJSON
                  data={{
                    type: "FeatureCollection",
                    features: job.candidates.map((candidate) => ({
                      type: "Feature",
                      geometry: candidate.geometry,
                      properties: candidate.attributes,
                    })),
                  }}
                  style={{ color: "#b3261e", weight: 2, fillOpacity: 0.35 }}
                />
              )}
            </MapContainer>
          </div>

          <form className="detection-control-card" onSubmit={submitJob}>
            <h2>Run detection</h2>
            <label htmlFor="detection-start-date">Baseline date</label>
            <input
              id="detection-start-date"
              type="date"
              value={startDate}
              onChange={(event) => setStartDate(event.target.value)}
              required
            />
            <label htmlFor="detection-end-date">Comparison date</label>
            <input
              id="detection-end-date"
              type="date"
              value={endDate}
              onChange={(event) => setEndDate(event.target.value)}
              required
            />
            <label htmlFor="detection-collection">Satellite collection</label>
            <select
              id="detection-collection"
              value={collection}
              onChange={(event) => setCollection(event.target.value)}
            >
              <option value={DEFAULT_COLLECTION}>{DEFAULT_COLLECTION}</option>
            </select>
            <p className="detection-selection">
              {aoi ? "AOI selected" : "No AOI selected"}
            </p>
            <button type="submit" className="primary-button" disabled={loading}>
              {loading ? "Starting..." : "Start detection"}
            </button>
            {job && (
              <button type="button" className="outline-button" onClick={resetJob}>
                New detection
              </button>
            )}
          </form>
        </section>

        {job && (
          <section className="detection-result-card">
            <div>
              <p className="page-label">JOB #{job.id}</p>
              <h2>{job.status}</h2>
              <p>{job.progress}% complete</p>
            </div>
            {job.status === "FAILED" && <p className="detection-error">{job.error_message}</p>}
            {job.status === "SUCCEEDED" && (
              <>
                <p>
                  {job.candidates?.length || 0} candidate regions found.
                  All results require official verification.
                </p>
              </>
            )}
          </section>
        )}
      </main>
    </div>
  );
}

export default Detection;
