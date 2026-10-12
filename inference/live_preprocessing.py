"""Prepare downloaded satellite scenes for UrbanEye inference.

This module deliberately stops before model inference. It converts two
provider scenes into a common, clipped, three-band GeoTIFF pair that satisfies
the input contract enforced by :class:`UrbanEyeInference`.
"""

from dataclasses import dataclass
import json
from math import ceil
from pathlib import Path
from typing import Any, Mapping, Sequence

import geopandas as gpd
import numpy as np
import rasterio
from rasterio.features import geometry_mask
from rasterio.mask import mask as mask_raster
from rasterio.transform import from_origin
from rasterio.warp import (
    Resampling,
    calculate_default_transform,
    reproject,
    transform_bounds,
)
from shapely.geometry import box, shape
from shapely.ops import transform as transform_geometry
from pyproj import CRS, Transformer


SceneInput = str | Path | Sequence[str | Path]


@dataclass(frozen=True)
class PreparedScenePair:
    """Aligned files and metadata produced for one detection job."""

    baseline_path: Path
    comparison_path: Path
    crs: CRS
    transform: Any
    width: int
    height: int
    band_indexes: tuple[int, ...]
    resolution: tuple[float, float]

    def as_dict(self) -> dict[str, Any]:
        """Return metadata suitable for a job record or API response."""
        return {
            "baseline_path": str(self.baseline_path),
            "comparison_path": str(self.comparison_path),
            "crs": self.crs.to_string(),
            "width": self.width,
            "height": self.height,
            "band_indexes": list(self.band_indexes),
            "resolution": list(self.resolution),
        }


def _load_aoi(
    aoi: Any,
    aoi_crs: str | CRS | None,
) -> tuple[Any, CRS]:
    """Load an AOI geometry and its CRS from common API/file inputs."""
    if isinstance(aoi, (str, Path)):
        path = Path(aoi)
        if not path.exists():
            raise FileNotFoundError(f"AOI file not found: {path}")

        if path.suffix.lower() in {".json", ".geojson"}:
            data = json.loads(path.read_text(encoding="utf-8"))
            if data["type"] == "FeatureCollection":
                if len(data["features"]) != 1:
                    raise ValueError("AOI GeoJSON must contain exactly one feature.")
                geometry = shape(data["features"][0]["geometry"])
            elif data["type"] == "Feature":
                geometry = shape(data["geometry"])
            else:
                geometry = shape(data)
            source_crs = CRS.from_user_input(aoi_crs or "EPSG:4326")
        else:
            frame = gpd.read_file(path)
            if frame.empty:
                raise ValueError(f"AOI file contains no features: {path}")
            if frame.crs is None:
                if aoi_crs is None:
                    raise ValueError("AOI file has no CRS; provide aoi_crs.")
                source_crs = CRS.from_user_input(aoi_crs)
            else:
                source_crs = CRS.from_user_input(frame.crs)
            geometry = frame.geometry.union_all()
    else:
        if not hasattr(aoi, "is_empty") and not isinstance(aoi, Mapping):
            raise TypeError("aoi must be a path, GeoJSON mapping, or Shapely geometry.")
        geometry = shape(aoi) if isinstance(aoi, Mapping) else aoi
        if aoi_crs is None:
            raise ValueError("aoi_crs is required for an in-memory AOI geometry.")
        source_crs = CRS.from_user_input(aoi_crs)

    if geometry.is_empty or not geometry.is_valid:
        raise ValueError("AOI geometry must be non-empty and valid.")
    return geometry, source_crs


def _project_geometry(geometry: Any, source_crs: CRS, target_crs: CRS) -> Any:
    transformer = Transformer.from_crs(
        source_crs,
        target_crs,
        always_xy=True,
    )
    projected = transform_geometry(transformer.transform, geometry)
    if projected.is_empty or not projected.is_valid:
        raise ValueError("AOI is invalid after reprojection.")
    return projected


def _derive_resolution(path: Path, target_crs: CRS) -> tuple[float, float]:
    with rasterio.open(path) as source:
        if source.crs is None:
            raise ValueError(f"Raster has no CRS: {path}")
        if CRS.from_user_input(source.crs) == target_crs:
            resolution = (abs(source.transform.a), abs(source.transform.e))
        else:
            transform, _, _ = calculate_default_transform(
                source.crs,
                target_crs,
                source.width,
                source.height,
                *source.bounds,
            )
            resolution = (abs(transform.a), abs(transform.e))

    if not all(np.isfinite(value) and value > 0 for value in resolution):
        raise ValueError(f"Could not derive a positive raster resolution from {path}.")
    return resolution


def _stack_and_normalize_scene(
    band_paths: Sequence[Path],
    output_path: Path,
    clip_geometry: Any,
    clip_crs: CRS,
) -> Path:
    """Stack Bhoonidhi BAND2/3/4 files and reproduce training normalization."""
    if len(band_paths) != 3:
        raise ValueError("A Bhoonidhi scene must contain exactly three band files.")
    if len(set(band_paths)) != len(band_paths):
        raise ValueError("A Bhoonidhi scene cannot repeat a band file.")

    profile: dict[str, Any] | None = None
    reference: tuple[Any, Any, int, int] | None = None
    percentiles: list[tuple[float, float]] = []
    source_geometries: list[Any] = []
    for path in band_paths:
        if not path.exists():
            raise FileNotFoundError(f"Scene band not found: {path}")
        with rasterio.open(path) as source:
            if source.count != 1:
                raise ValueError(f"Scene band must be single-band: {path}")
            current = (source.crs, source.transform, source.width, source.height)
            if reference is None:
                reference = current
                profile = source.profile.copy()
            elif current != reference:
                raise ValueError(
                    "Bhoonidhi band files must share CRS, transform, and dimensions."
                )
            sample_height = min(source.height, 2048)
            sample_width = min(source.width, 2048)
            sample = source.read(
                1,
                out_shape=(1, sample_height, sample_width),
                resampling=Resampling.nearest,
            )
            values = sample.astype(np.float32, copy=False)
            percentiles.append(
                (float(np.percentile(values, 2)), float(np.percentile(values, 98)))
            )
            if source.crs is None:
                raise ValueError(f"Scene band has no CRS: {path}")
            source_crs = CRS.from_user_input(source.crs)
            source_geometries.append(
                _project_geometry(clip_geometry, clip_crs, source_crs)
            )

    if profile is None:
        raise ValueError("No scene bands were provided.")
    profile.update(
        count=3,
        dtype="float32",
        nodata=None,
        compress="lzw",
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cropped_bands: list[np.ndarray] = []
    cropped_transform: Any | None = None
    for path, geometry, (p2, p98) in zip(
        band_paths,
        source_geometries,
        percentiles,
    ):
        with rasterio.open(path) as source:
            cropped, transform = mask_raster(
                source,
                [geometry],
                crop=True,
                indexes=1,
                filled=True,
                nodata=0,
            )
        if cropped_transform is None:
            cropped_transform = transform
        elif cropped.shape != cropped_bands[0].shape or transform != cropped_transform:
            raise ValueError("Bhoonidhi band crops do not share an identical grid.")
        values = np.clip(cropped.astype(np.float32, copy=False), p2, p98)
        cropped_bands.append((values - p2) / (p98 - p2 + 1e-8))

    if cropped_transform is None or not cropped_bands:
        raise ValueError("Could not crop the Bhoonidhi scene to the AOI.")
    profile.update(
        height=cropped_bands[0].shape[0],
        width=cropped_bands[0].shape[1],
        transform=cropped_transform,
    )
    with rasterio.open(output_path, "w", **profile) as destination:
        destination.write(np.stack(cropped_bands).astype(np.float32))
    return output_path


def _prepare_scene_input(
    scene: SceneInput,
    output_dir: Path,
    label: str,
    clip_geometry: Any,
    clip_crs: CRS,
) -> Path:
    if isinstance(scene, (str, Path)):
        path = Path(scene)
        if not path.exists():
            raise FileNotFoundError(f"{label} not found: {path}")
        return path
    paths = tuple(Path(path) for path in scene)
    return _stack_and_normalize_scene(
        paths,
        output_dir / "_normalized_sources" / f"{label.lower()}_normalized.tif",
        clip_geometry,
        clip_crs,
    )


def _scene_intersects_aoi(
    source: rasterio.io.DatasetReader,
    aoi_geometry: Any,
    target_crs: CRS,
) -> bool:
    source_bounds = transform_bounds(
        source.crs,
        target_crs,
        *source.bounds,
        densify_pts=21,
    )
    return box(*source_bounds).intersects(aoi_geometry)


def _write_aligned_scene(
    source_path: Path,
    output_path: Path,
    band_indexes: tuple[int, ...],
    aoi_geometry: Any,
    target_crs: CRS,
    target_transform: Any,
    width: int,
    height: int,
    resampling: Resampling,
) -> None:
    with rasterio.open(source_path) as source:
        if source.crs is None:
            raise ValueError(f"Raster has no CRS: {source_path}")
        if max(band_indexes) > source.count:
            raise ValueError(
                f"{source_path} has {source.count} bands, but "
                f"{band_indexes} were requested."
            )
        if not _scene_intersects_aoi(source, aoi_geometry, target_crs):
            raise ValueError(f"Raster does not intersect the selected AOI: {source_path}")

        output = np.zeros((len(band_indexes), height, width), dtype=np.float32)
        for output_index, source_index in enumerate(band_indexes):
            reproject(
                source=rasterio.band(source, source_index),
                destination=output[output_index],
                src_transform=source.transform,
                src_crs=source.crs,
                src_nodata=source.nodata,
                dst_transform=target_transform,
                dst_crs=target_crs,
                dst_nodata=0,
                resampling=resampling,
            )

    inside_aoi = geometry_mask(
        [aoi_geometry],
        out_shape=(height, width),
        transform=target_transform,
        invert=True,
    )
    output[:, ~inside_aoi] = 0

    if not np.isfinite(output).all():
        raise ValueError(f"Prepared raster contains non-finite values: {source_path}")
    if not np.any(output):
        raise ValueError(f"Prepared raster contains no valid pixels: {source_path}")

    profile = {
        "driver": "GTiff",
        "height": height,
        "width": width,
        "count": len(band_indexes),
        "dtype": "float32",
        "crs": target_crs,
        "transform": target_transform,
        "nodata": 0,
        "compress": "lzw",
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(output_path, "w", **profile) as destination:
        destination.write(output)


def validate_prepared_pair(
    baseline_path: Path,
    comparison_path: Path,
    expected_band_count: int = 3,
) -> None:
    """Validate the exact spatial input contract required by inference."""
    with rasterio.open(baseline_path) as baseline, rasterio.open(comparison_path) as comparison:
        if baseline.count != expected_band_count or comparison.count != expected_band_count:
            raise ValueError("Prepared scenes must contain exactly three bands.")
        if baseline.shape != comparison.shape:
            raise ValueError("Prepared scenes have different dimensions.")
        if baseline.crs != comparison.crs:
            raise ValueError("Prepared scenes have different CRS values.")
        if baseline.transform != comparison.transform:
            raise ValueError("Prepared scenes do not share an identical transform.")
        if not np.any(baseline.read(1)) or not np.any(comparison.read(1)):
            raise ValueError("Prepared scenes contain no valid data.")


def prepare_scene_pair(
    baseline_path: SceneInput,
    comparison_path: SceneInput,
    aoi: Any,
    output_dir: str | Path,
    *,
    aoi_crs: str | CRS | None = "EPSG:4326",
    target_crs: str | CRS = "EPSG:32643",
    target_resolution: tuple[float, float] | None = None,
    band_indexes: Sequence[int] = (1, 2, 3),
    resampling: Resampling = Resampling.bilinear,
) -> PreparedScenePair:
    """Clip, reproject, resample, and align a downloaded scene pair.

    A source scene may be one already-stacked raster or three single-band
    Bhoonidhi files in physical-band order (BAND2, BAND3, BAND4). A sequence
    is stacked and normalized using the training-time preprocessing first.
    The returned files always share one CRS, transform, shape, and
    three-band float32 layout.
    """
    output_dir = Path(output_dir)
    target_crs = CRS.from_user_input(target_crs)
    geometry, source_aoi_crs = _load_aoi(aoi, aoi_crs)
    projected_aoi = _project_geometry(geometry, source_aoi_crs, target_crs)
    baseline_path = _prepare_scene_input(
        baseline_path,
        output_dir,
        "baseline",
        projected_aoi,
        target_crs,
    )
    comparison_path = _prepare_scene_input(
        comparison_path,
        output_dir,
        "comparison",
        projected_aoi,
        target_crs,
    )

    bands = tuple(int(index) for index in band_indexes)
    if len(bands) != 3 or len(set(bands)) != 3 or min(bands) < 1:
        raise ValueError("band_indexes must contain three distinct positive indexes.")

    resolution = target_resolution or _derive_resolution(baseline_path, target_crs)
    if len(resolution) != 2 or not all(
        np.isfinite(value) and value > 0 for value in resolution
    ):
        raise ValueError("target_resolution must contain two positive values.")
    resolution = (float(resolution[0]), float(resolution[1]))

    min_x, min_y, max_x, max_y = projected_aoi.bounds
    width = max(1, int(ceil((max_x - min_x) / resolution[0])))
    height = max(1, int(ceil((max_y - min_y) / resolution[1])))
    target_transform = from_origin(
        min_x,
        max_y,
        resolution[0],
        resolution[1],
    )

    baseline_output = output_dir / "baseline_aligned.tif"
    comparison_output = output_dir / "comparison_aligned.tif"
    _write_aligned_scene(
        baseline_path,
        baseline_output,
        bands,
        projected_aoi,
        target_crs,
        target_transform,
        width,
        height,
        resampling,
    )
    _write_aligned_scene(
        comparison_path,
        comparison_output,
        bands,
        projected_aoi,
        target_crs,
        target_transform,
        width,
        height,
        resampling,
    )
    validate_prepared_pair(baseline_output, comparison_output)

    return PreparedScenePair(
        baseline_path=baseline_output,
        comparison_path=comparison_output,
        crs=target_crs,
        transform=target_transform,
        width=width,
        height=height,
        band_indexes=bands,
        resolution=resolution,
    )
