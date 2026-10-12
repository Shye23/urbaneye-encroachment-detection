"""ML-environment entry point for one portal detection job."""

import argparse
from datetime import date, timedelta
import json
import os
from pathlib import Path
import zipfile

import rasterio
from rasterio.mask import mask as mask_raster
from shapely.geometry import mapping, shape
from shapely.ops import transform as transform_geometry
from pyproj import Transformer

from inference.live_preprocessing import prepare_scene_pair
from inference.providers.bhoonidhi import (
    BhoonidhiClient,
    BhoonidhiCredentials,
    BhoonidhiError,
)
from inference.run_urbaneye_pipeline import PipelineConfig, run_pipeline


def _geometry(aoi: dict) -> dict:
    if aoi["type"] == "Feature":
        return aoi["geometry"]
    if aoi["type"] == "FeatureCollection":
        geometries = [shape(feature["geometry"]) for feature in aoi["features"]]
        merged = geometries[0]
        for geometry in geometries[1:]:
            merged = merged.union(geometry)
        return mapping(merged)
    return aoi


def _search_scenes(client, geometry, start, end, collection):
    scenes = []
    cursor = start
    while cursor <= end:
        window_end = min(cursor + timedelta(days=365), end)
        scenes.extend(
            client.search(
                geometry,
                cursor,
                window_end,
                extra_filters={
                    "collections": [collection],
                    "filter": {"op": "=", "args": [{"property": "Online"}, "Y"]},
                    "filter-lang": "cql2-json",
                },
            )
        )
        cursor = window_end + timedelta(days=1)
    return scenes


def _bands(scene_dir: Path) -> list[Path]:
    by_name = {path.name.upper(): path for path in scene_dir.rglob("BAND*.tif")}
    required = ["BAND2.TIF", "BAND3.TIF", "BAND4.TIF"]
    if any(name not in by_name for name in required):
        raise BhoonidhiError(f"Downloaded scene is missing one of {required}.")
    return [by_name[name] for name in required]


def _download_bands(client, scene, destination: Path) -> list[Path]:
    archive = destination / f"{scene.product_id}.download"
    destination.mkdir(parents=True, exist_ok=True)
    client.download(scene, archive)
    scene_root = destination / scene.product_id
    if zipfile.is_zipfile(archive):
        with zipfile.ZipFile(archive) as zipped:
            root = scene_root.resolve()
            for member in zipped.infolist():
                target = (root / member.filename).resolve()
                if root not in target.parents and target != root:
                    raise BhoonidhiError("Downloaded archive contains an unsafe path.")
            zipped.extractall(root)
        archive.unlink()
    else:
        scene_root.mkdir(parents=True, exist_ok=True)
        archive.rename(scene_root / "scene.tif")
    return _bands(scene_root)


def _bands_have_valid_pixels(band_paths: list[Path], geometry: dict) -> bool:
    for band_path in band_paths:
        with rasterio.open(band_path) as source:
            if source.crs is None:
                return False
            transformer = Transformer.from_crs(
                "EPSG:4326",
                source.crs,
                always_xy=True,
            )
            projected_geometry = transform_geometry(
                transformer.transform,
                shape(geometry),
            )
            try:
                clipped, _ = mask_raster(
                    source,
                    [projected_geometry],
                    crop=True,
                    indexes=1,
                    filled=True,
                    nodata=0,
                )
            except ValueError:
                return False
            if not clipped.any():
                return False
    return True


def _download_closest_available(
    client,
    scenes,
    target_date: date,
    destination: Path,
    geometry: dict,
    *,
    excluded_product_ids: set[str] | None = None,
):
    excluded = excluded_product_ids or set()
    candidates = sorted(
        (
            scene
            for scene in scenes
            if scene.product_id not in excluded
            and scene.acquisition_date is not None
        ),
        key=lambda scene: abs(scene.acquisition_date - target_date),
    )
    if not candidates:
        raise BhoonidhiError(
            f"No downloadable scene candidates were returned near {target_date}."
        )

    unavailable = []
    for scene in candidates:
        try:
            bands = _download_bands(client, scene, destination)
            if not _bands_have_valid_pixels(bands, geometry):
                raise BhoonidhiError(
                    f"Scene {scene.product_id} contains no valid pixels in the AOI."
                )
            return scene, bands
        except BhoonidhiError as exc:
            if (
                "HTTP 404" not in str(exc)
                and "contains no valid pixels in the AOI" not in str(exc)
            ):
                raise
            unavailable.append(scene.product_id)

    raise BhoonidhiError(
        "Bhoonidhi catalogue entries were unavailable for download near "
        f"{target_date}; tried {len(unavailable)} product(s)."
    )


def run_manifest(manifest_path: Path) -> None:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    workspace = Path(manifest["workspace"])
    credentials = BhoonidhiCredentials(
        user_id=_required_env("BHOONIDHI_USER_ID"),
        password=_required_env("BHOONIDHI_PASSWORD"),
    )
    client = BhoonidhiClient(credentials)
    start = date.fromisoformat(manifest["start_date"])
    end = date.fromisoformat(manifest["end_date"])
    geometry = _geometry(manifest["aoi"])
    scenes = _search_scenes(client, geometry, start, end, manifest["collection"])
    baseline, baseline_bands = _download_closest_available(
        client,
        scenes,
        start,
        workspace / "baseline",
        geometry,
    )
    comparison, comparison_bands = _download_closest_available(
        client,
        scenes,
        end,
        workspace / "comparison",
        geometry,
        excluded_product_ids={baseline.product_id},
    )
    aoi_path = workspace / "aoi.geojson"
    aoi_path.write_text(json.dumps(manifest["aoi"]), encoding="utf-8")
    prepared = prepare_scene_pair(
        baseline_bands,
        comparison_bands,
        aoi=aoi_path,
        output_dir=workspace / "prepared",
        target_crs="EPSG:32643",
        target_resolution=(5.0, 5.0),
    )
    root = Path(__file__).resolve().parents[1]
    result = run_pipeline(
        PipelineConfig(
            image_baseline=prepared.baseline_path,
            image_comparison=prepared.comparison_path,
            checkpoint=Path(
                _required_env(
                    "URBANEYE_CHECKPOINT",
                    str(root / "training" / "checkpoints" / "snunet" / "baseline" / "best_model.pth"),
                )
            ),
            output_dir=workspace / "outputs",
            aoi=f"JOB_{manifest['job_id']}",
        )
    )
    geojson = json.loads(result.change_geojson.read_text(encoding="utf-8"))
    output = {
        "scene_metadata": {
            "baseline": {"product_id": baseline.product_id, "date": str(baseline.acquisition_date)},
            "comparison": {"product_id": comparison.product_id, "date": str(comparison.acquisition_date)},
        },
        "pipeline": result.as_dict(),
        "candidates": [
            {
                "candidate_id": feature["properties"]["candidate_id"],
                "geometry": feature["geometry"],
                "attributes": feature["properties"],
            }
            for feature in geojson["features"]
        ],
        "artifacts": [
            {"kind": "GEOJSON", "name": result.change_geojson.name, "path": str(result.change_geojson)},
            {"kind": "REPORT", "name": result.summary_report.name, "path": str(result.summary_report)},
            {"kind": "EVIDENCE", "name": result.evidence_json.name, "path": str(result.evidence_json)},
        ],
    }
    Path(manifest["result_file"]).write_text(
        json.dumps(output, default=str),
        encoding="utf-8",
    )


def _required_env(name: str, default: str | None = None) -> str:
    value = os.getenv(name, default)
    if not value:
        raise RuntimeError(f"Required environment variable {name} is not configured.")
    return value


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args()
    run_manifest(args.manifest)
