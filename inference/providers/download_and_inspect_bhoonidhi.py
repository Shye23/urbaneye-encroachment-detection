"""Download one inspected Bhoonidhi scene and report its raster metadata.

Credentials are read from BHOONIDHI_USER_ID and BHOONIDHI_PASSWORD.
This command does not run the ML pipeline.

Example (PowerShell):

    python -m inference.providers.download_and_inspect_bhoonidhi `
        --inspection bhoonidhi-inspection.json `
        --product-id R2F01JAN2020045155009400058SSANSTUC00GTDD `
        --output-dir downloaded_scenes
"""

from __future__ import annotations

import argparse
from datetime import date
import json
import os
from pathlib import Path
from typing import Any
import zipfile

import rasterio

from .bhoonidhi import (
    BhoonidhiClient,
    BhoonidhiConfig,
    BhoonidhiCredentials,
    BhoonidhiError,
    BhoonidhiScene,
)


def _load_scene(inspection_path: Path, product_id: str) -> BhoonidhiScene:
    document = json.loads(inspection_path.read_text(encoding="utf-8"))
    for item in document.get("scenes", []):
        if item.get("product_id") != product_id:
            continue
        acquisition_date = item.get("acquisition_date")
        return BhoonidhiScene(
            product_id=product_id,
            acquisition_date=(
                date.fromisoformat(acquisition_date)
                if isinstance(acquisition_date, str)
                else None
            ),
            metadata=item.get("metadata", {}),
            download_reference=item.get("download_reference"),
        )
    raise ValueError(
        f"Product {product_id!r} was not found in {inspection_path}."
    )


def _single_raster_summary(path: Path) -> dict[str, Any]:
    with rasterio.open(path) as dataset:
        band_ranges = []
        for band_index in range(1, dataset.count + 1):
            values = dataset.read(band_index, masked=True)
            if values.count() == 0:
                minimum = maximum = None
            else:
                minimum = float(values.min())
                maximum = float(values.max())
            band_ranges.append(
                {
                    "raster_band": band_index,
                    "min": minimum,
                    "max": maximum,
                }
            )
        return {
            "path": str(path),
            "driver": dataset.driver,
            "width": dataset.width,
            "height": dataset.height,
            "count": dataset.count,
            "dtypes": list(dataset.dtypes),
            "nodata": dataset.nodata,
            "crs": dataset.crs.to_string() if dataset.crs else None,
            "transform": list(dataset.transform),
            "pixel_size": {
                "x": dataset.transform.a,
                "y": dataset.transform.e,
            },
            "band_ranges": band_ranges,
            "descriptions": list(dataset.descriptions),
        }


def _raster_summary(path: Path) -> dict[str, Any]:
    sibling_bands = sorted(path.parent.glob("BAND*.tif"))
    if len(sibling_bands) <= 1:
        return _single_raster_summary(path)

    summaries = [_single_raster_summary(band_path) for band_path in sibling_bands]
    first = summaries[0]
    return {
        **first,
        "path": str(path.parent),
        "files": summaries,
    }


def _resolve_downloaded_raster(downloaded_path: Path, output_dir: Path) -> Path:
    if not zipfile.is_zipfile(downloaded_path):
        return downloaded_path

    extract_dir = output_dir / downloaded_path.stem
    extract_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(downloaded_path) as archive:
        root = extract_dir.resolve()
        for member in archive.infolist():
            target = (extract_dir / member.filename).resolve()
            if root not in target.parents and target != root:
                raise BhoonidhiError(
                    f"Unsafe path in Bhoonidhi archive: {member.filename}"
                )
        archive.extractall(extract_dir)

    rasters = sorted(extract_dir.rglob("*.tif")) + sorted(
        extract_dir.rglob("*.tiff")
    )
    if not rasters:
        raise BhoonidhiError(
            f"Bhoonidhi archive {downloaded_path} contained no GeoTIFF."
        )
    return rasters[0]


def download_and_inspect(
    *,
    inspection_path: Path,
    product_id: str,
    output_dir: Path,
) -> dict[str, Any]:
    user_id = os.environ.get("BHOONIDHI_USER_ID")
    password = os.environ.get("BHOONIDHI_PASSWORD")
    if not user_id or not password:
        raise RuntimeError(
            "Set BHOONIDHI_USER_ID and BHOONIDHI_PASSWORD in the local "
            "PowerShell session before running this command."
        )

    scene = _load_scene(inspection_path, product_id)
    client = BhoonidhiClient(
        credentials=BhoonidhiCredentials(user_id=user_id, password=password),
        config=BhoonidhiConfig(
            base_url=os.environ.get(
                "BHOONIDHI_BASE_URL",
                "https://bhoonidhi-api.nrsc.gov.in",
            )
        ),
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    destination = output_dir / f"{product_id}.download"
    downloaded_path = client.download(scene, destination)
    raster_path = _resolve_downloaded_raster(downloaded_path, output_dir)
    try:
        summary = _raster_summary(raster_path)
    except rasterio.errors.RasterioIOError as exc:
        raise BhoonidhiError(
            f"Downloaded product is not readable as a GeoTIFF: {downloaded_path}"
        ) from exc

    summary_path = output_dir / f"{product_id}.raster.json"
    summary_path.write_text(
        json.dumps(summary, indent=2, ensure_ascii=True),
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2, ensure_ascii=True))
    print(f"Saved raster summary to {summary_path}")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inspection", type=Path, required=True)
    parser.add_argument("--product-id", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    download_and_inspect(
        inspection_path=args.inspection,
        product_id=args.product_id,
        output_dir=args.output_dir,
    )


if __name__ == "__main__":
    main()
