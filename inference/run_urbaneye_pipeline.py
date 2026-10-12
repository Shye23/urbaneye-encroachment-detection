"""Reusable UrbanEye end-to-end change-detection pipeline.

The pipeline accepts any pair of aligned, three-band GeoTIFFs and writes all
job-specific outputs below the supplied output directory. The command-line
interface at the bottom of this file is retained for local/manual runs.
"""

import argparse
from dataclasses import asdict, dataclass
import sys
from pathlib import Path
from typing import Any

import geopandas as gpd
import numpy as np
import rasterio
from rasterio.features import shapes
from scipy import ndimage
from shapely.geometry import shape


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


@dataclass(frozen=True)
class PipelineConfig:
    """All inputs and tunable settings required for one pipeline run."""

    image_baseline: Path
    image_comparison: Path
    checkpoint: Path
    output_dir: Path
    aoi: str = "AOI"
    parcel_file: Path | None = None
    road_file: Path | None = None
    building_file: Path | None = None
    threshold: float = 0.60
    min_component_size: int = 4
    kernel_size: int = 3


@dataclass(frozen=True)
class PipelineResult:
    """Paths and summary values produced by :func:`run_pipeline`."""

    aoi: str
    candidate_count: int
    raw_changed_pixels: int
    postprocessed_changed_pixels: int
    change_polygons: Path
    change_geojson: Path
    spatial_analysis_gpkg: Path
    spatial_analysis_csv: Path
    evidence_csv: Path
    evidence_json: Path
    summary_report: Path
    output_dir: Path

    def as_dict(self) -> dict[str, Any]:
        """Return a JSON-friendly representation for an API worker."""
        result = asdict(self)
        return {
            key: str(value) if isinstance(value, Path) else value
            for key, value in result.items()
        }


def parse_args():
    parser = argparse.ArgumentParser(description="Run the UrbanEye pipeline.")
    parser.add_argument("--aoi", default="AOI10", help="AOI label used in output filenames.")
    parser.add_argument(
        "--image-2020",
        type=Path,
        default=ROOT / "output" / "2020" / "AOI10_2020.tif",
    )
    parser.add_argument(
        "--image-2024",
        type=Path,
        default=ROOT / "output" / "2024" / "AOI10_2024.tif",
    )
    parser.add_argument(
        "--checkpoint",
        type=Path,
        default=ROOT / "training" / "checkpoints" / "snunet" / "baseline" / "best_model.pth",
    )
    parser.add_argument("--threshold", type=float, default=0.60)
    parser.add_argument("--min-component-size", type=int, default=4)
    parser.add_argument("--kernel-size", type=int, default=3)
    return parser.parse_args()


def require_file(path: Path, description: str) -> None:
    if not path.exists():
        raise FileNotFoundError(f"{description} not found:\n{path}")


def postprocess_mask(
    prediction: np.ndarray,
    kernel_size: int = 3,
    min_component_size: int = 4,
) -> np.ndarray:
    """Apply 3x3 opening/closing and remove components smaller than 4 pixels."""
    mask = np.asarray(prediction).squeeze().astype(bool)

    if mask.ndim != 2:
        raise ValueError(
            f"Expected a 2D prediction mask after squeeze; got shape {mask.shape}."
        )
    if kernel_size < 1 or min_component_size < 1:
        raise ValueError("kernel_size and min_component_size must be positive.")

    structure = np.ones((kernel_size, kernel_size), dtype=bool)
    cleaned = ndimage.binary_opening(mask, structure=structure)
    cleaned = ndimage.binary_closing(cleaned, structure=structure)

    # 8-connected components, matching the polygonization connectivity.
    labels, count = ndimage.label(cleaned, structure=np.ones((3, 3), dtype=np.uint8))
    if count:
        sizes = np.bincount(labels.ravel())
        keep = sizes >= min_component_size
        keep[0] = False
        cleaned = keep[labels]

    return cleaned.astype(np.uint8)


def polygonize_mask(
    mask: np.ndarray,
    transform,
    crs,
    output_path: Path,
    aoi: str,
) -> gpd.GeoDataFrame:
    """Polygonize the cleaned mask using the inference result's own transform/CRS."""
    mask = np.asarray(mask).squeeze().astype(np.uint8)
    if mask.ndim != 2:
        raise ValueError(f"Expected 2D mask, got {mask.shape}.")

    pixel_area = abs(
        transform.a * transform.e - transform.b * transform.d
    )
    if pixel_area <= 0:
        raise ValueError(f"Invalid pixel area from transform: {transform}")

    records = []
    for geom, value in shapes(
        mask,
        mask=mask == 1,
        transform=transform,
        connectivity=8,
    ):
        if int(value) != 1:
            continue

        polygon = shape(geom)
        if polygon.is_empty:
            continue
        if not polygon.is_valid:
            polygon = polygon.buffer(0)
        if polygon.is_empty:
            continue

        area_m2 = float(polygon.area)
        records.append(
            {
                "candidate_id": f"C{len(records) + 1:03d}",
                "change_area_m2": area_m2,
                "change_pixels": int(round(area_m2 / pixel_area)),
                "source": "URBANEYE",
                "geometry": polygon,
            }
        )

    if not records:
        raise RuntimeError(
            "No change regions remain after postprocessing. "
            "The pipeline stopped rather than generating misleading empty reports. "
            "Inspect the prediction and threshold before continuing."
        )

    gdf = gpd.GeoDataFrame(records, geometry="geometry", crs=crs)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    gdf.to_file(output_path, layer="change_polygons", driver="GPKG")

    print(f"Polygon count: {len(gdf)}")
    print(f"Postprocessed change area: {gdf['change_area_m2'].sum():,.2f} m²")
    print(f"Polygon GeoPackage: {output_path}")
    return gdf


def _default_config(args: argparse.Namespace) -> PipelineConfig:
    """Build the legacy local-run configuration from CLI arguments."""
    return PipelineConfig(
        image_baseline=args.image_2020,
        image_comparison=args.image_2024,
        checkpoint=args.checkpoint,
        output_dir=ROOT / "outputs" / "runs" / args.aoi,
        aoi=args.aoi,
        parcel_file=ROOT / "processed_data" / "cadastral" / "synthetic_cadastral.gpkg",
        road_file=ROOT / "processed_data" / "cadastral" / "synthetic_roads.gpkg",
        building_file=ROOT / "processed_data" / "cadastral" / "synthetic_buildings.gpkg",
        threshold=args.threshold,
        min_component_size=args.min_component_size,
        kernel_size=args.kernel_size,
    )


def run_pipeline(config: PipelineConfig) -> PipelineResult:
    """Run inference, GIS analysis, and evidence-report generation.

    Inputs must already be spatially aligned. Live satellite downloads should
    be clipped, reprojected, resampled, and aligned in a separate
    preprocessing step before calling this function.
    """
    aoi = config.aoi.strip()
    if not aoi:
        raise ValueError("config.aoi must not be empty.")
    if not 0.0 <= config.threshold <= 1.0:
        raise ValueError("config.threshold must be between 0 and 1.")
    if config.kernel_size < 1 or config.min_component_size < 1:
        raise ValueError("Morphology settings must be positive.")

    parcel_file = config.parcel_file or (
        ROOT / "processed_data" / "cadastral" / "synthetic_cadastral.gpkg"
    )
    road_file = config.road_file or (
        ROOT / "processed_data" / "cadastral" / "synthetic_roads.gpkg"
    )
    building_file = config.building_file or (
        ROOT / "processed_data" / "cadastral" / "synthetic_buildings.gpkg"
    )

    require_file(config.image_baseline, "Baseline image")
    require_file(config.image_comparison, "Comparison image")
    require_file(config.checkpoint, "Model checkpoint")
    require_file(parcel_file, "Parcel layer")
    require_file(road_file, "Road layer")
    require_file(building_file, "Building layer")

    run_dir = config.output_dir
    dynamic_dir = run_dir / "dynamic"
    gis_dir = run_dir / "gis"
    reports_dir = run_dir / "reports"
    dynamic_dir.mkdir(parents=True, exist_ok=True)
    gis_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)

    print("\n" + "=" * 64)
    print(f"URBANEYE END-TO-END PIPELINE: {aoi}")
    print("=" * 64)
    print(f"Baseline image: {config.image_baseline}")
    print(f"Comparison image: {config.image_comparison}")
    print(f"Checkpoint: {config.checkpoint}")
    print(f"Threshold: {config.threshold:.2f}")

    # 1. Run the existing trained model.
    from inference.inference_engine import UrbanEyeInference

    engine = UrbanEyeInference(
        checkpoint_path=config.checkpoint,
        threshold=config.threshold,
    )
    result = engine.predict(config.image_baseline, config.image_comparison)

    probability = np.asarray(result["probability"]).squeeze()
    prediction = np.asarray(result["prediction"]).squeeze()
    transform = result["transform"]
    crs = result["crs"]

    if probability.ndim != 2 or prediction.ndim != 2:
        raise ValueError(
            f"Expected 2D stitched outputs; probability={probability.shape}, "
            f"prediction={prediction.shape}."
        )
    if probability.shape != prediction.shape:
        raise ValueError(
            f"Probability/mask shape mismatch: {probability.shape} vs {prediction.shape}."
        )
    if crs is None:
        raise ValueError("Inference result has no CRS; refusing to create unreferenced polygons.")

    np.save(dynamic_dir / "probability.npy", probability)
    np.save(dynamic_dir / "prediction_raw.npy", prediction.astype(np.uint8))

    # 2. Postprocess and save the cleaned mask.
    cleaned = postprocess_mask(
        prediction,
        kernel_size=config.kernel_size,
        min_component_size=config.min_component_size,
    )
    np.save(dynamic_dir / "prediction_postprocessed.npy", cleaned)

    print(f"\nRaw changed pixels: {int(np.count_nonzero(prediction)):,}")
    print(f"Postprocessed changed pixels: {int(np.count_nonzero(cleaned)):,}")
    print(f"Saved masks and probabilities: {dynamic_dir}")

    # 3. Polygonize with the transform and CRS returned by inference.
    change_gpkg = gis_dir / f"{aoi}_change_polygons.gpkg"
    polygons = polygonize_mask(cleaned, transform, crs, change_gpkg, aoi)

    # Also export GeoJSON for map/front-end use.
    geojson_path = gis_dir / f"{aoi}_change_polygons.geojson"
    polygons.to_file(geojson_path, driver="GeoJSON")
    print(f"GeoJSON: {geojson_path}")

    # 4. Existing spatial analysis, with explicit AOI-specific input/output paths.
    print("\nRunning parcel, road, and building spatial analysis...")
    from inference import spatial_analysis as sa

    spatial_analysis_gpkg = gis_dir / f"{aoi}_spatial_analysis.gpkg"
    spatial_analysis_csv = gis_dir / f"{aoi}_spatial_analysis.csv"
    sa.run_spatial_analysis(
        change_file=change_gpkg,
        parcel_file=parcel_file,
        road_file=road_file,
        building_file=building_file,
        output_gpkg=spatial_analysis_gpkg,
        output_csv=spatial_analysis_csv,
    )

    # 5. Evidence report generation with consistent classification mappings.
    from inference import generate_evidence_reports as reports

    evidence_csv = reports_dir / f"{aoi}_evidence_report.csv"
    evidence_json = reports_dir / f"{aoi}_evidence_records.json"
    summary_report = reports_dir / f"{aoi}_summary_report.txt"
    encroachment_classes = {
        "Potential Public-Space Encroachment",
        "Potential Government-Land Encroachment",
        "Potential Public-Land Encroachment",
        "Potential Parcel-Boundary Encroachment",
    }
    normal_classes = {
        "Normal Building Change",
        "Change Detected, No Encroachment Evidence",
        "Change on Government Land",
        "Change on Public Land",
    }
    print("\nGenerating evidence reports...")
    reports.run_evidence_report(
        input_gpkg=spatial_analysis_gpkg,
        input_csv=spatial_analysis_csv,
        output_dir=reports_dir,
        evidence_csv=evidence_csv,
        evidence_json=evidence_json,
        summary_txt=summary_report,
        encroachment_classes=encroachment_classes,
        normal_classes=normal_classes,
    )

    print("\n" + "=" * 64)
    print(f"URBANEYE PIPELINE COMPLETED: {aoi}")
    print("=" * 64)
    print(f"Change polygons: {change_gpkg}")
    print(f"Spatial analysis: {spatial_analysis_gpkg}")
    print(f"Spatial CSV: {spatial_analysis_csv}")
    print(f"Evidence reports: {reports_dir}")
    print("\nNote: cadastral layers are synthetic. Results are not legal findings.")

    return PipelineResult(
        aoi=aoi,
        candidate_count=len(polygons),
        raw_changed_pixels=int(np.count_nonzero(prediction)),
        postprocessed_changed_pixels=int(np.count_nonzero(cleaned)),
        change_polygons=change_gpkg,
        change_geojson=geojson_path,
        spatial_analysis_gpkg=spatial_analysis_gpkg,
        spatial_analysis_csv=spatial_analysis_csv,
        evidence_csv=evidence_csv,
        evidence_json=evidence_json,
        summary_report=summary_report,
        output_dir=run_dir,
    )


def main() -> None:
    args = parse_args()
    config = _default_config(args)
    result = run_pipeline(config)
    print("\nStructured result:")
    print(result.as_dict())


if __name__ == "__main__":
    main()
