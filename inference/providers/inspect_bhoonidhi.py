"""Inspect Bhoonidhi catalogue metadata without exposing credentials or tokens.

Set credentials only in the local environment:

    BHOONIDHI_USER_ID=...
    BHOONIDHI_PASSWORD=...

Example (PowerShell):

    python -m inference.providers.inspect_bhoonidhi `
        --aoi processed_data\aoi\aoi10.geojson `
        --start-date 2020-01-01 --end-date 2024-12-31 `
        --collection ResourceSat-2_LISS4-MX70_L2 `
        --output bhoonidhi-inspection.json

The output is a redacted catalogue snapshot. It does not download products.
"""

from __future__ import annotations

import argparse
from datetime import date, timedelta
import json
import os
from pathlib import Path
from typing import Any

import geopandas as gpd
from shapely.geometry import mapping

from .bhoonidhi import BhoonidhiClient, BhoonidhiConfig, BhoonidhiCredentials


def _load_geometry(path: Path) -> dict[str, Any]:
    if path.suffix.lower() in {".shp", ".gpkg", ".geojson", ".json"}:
        try:
            layer = gpd.read_file(path)
        except (OSError, ValueError) as exc:
            raise ValueError(f"Could not read AOI vector file {path}: {exc}") from exc
        if layer.empty:
            raise ValueError(f"AOI vector file {path} contains no features.")
        if layer.crs is None:
            raise ValueError(f"AOI vector file {path} has no CRS.")
        geometry = layer.to_crs("EPSG:4326").geometry.union_all()
        if geometry.is_empty:
            raise ValueError(f"AOI vector file {path} contains empty geometry.")
        return mapping(geometry)

    document = json.loads(path.read_text(encoding="utf-8"))
    if document.get("type") == "FeatureCollection":
        features = document.get("features", [])
        if len(features) != 1:
            raise ValueError("AOI GeoJSON must contain exactly one feature.")
        geometry = features[0].get("geometry")
    elif document.get("type") == "Feature":
        geometry = document.get("geometry")
    else:
        geometry = document
    if not isinstance(geometry, dict) or "type" not in geometry:
        raise ValueError("AOI GeoJSON does not contain a valid geometry.")
    return geometry


def _redact(value: Any) -> Any:
    if isinstance(value, dict):
        secret_keys = {
            "password",
            "access_token",
            "refresh_token",
            "authorization",
        }
        return {
            key: _redact(item)
            for key, item in value.items()
            if key.lower() not in secret_keys
        }
    if isinstance(value, list):
        return [_redact(item) for item in value]
    return value


def _date_windows(
    start_date: date,
    end_date: date,
    *,
    max_days: int = 366,
) -> list[tuple[date, date]]:
    if start_date > end_date:
        raise ValueError("start_date must not be after end_date.")
    windows = []
    window_start = start_date
    while window_start <= end_date:
        calendar_year_end = date(window_start.year, 12, 31)
        window_end = min(calendar_year_end, end_date)
        if (window_end - window_start).days + 1 > max_days:
            window_end = window_start + timedelta(days=max_days - 1)
        windows.append((window_start, window_end))
        window_start = window_end + timedelta(days=1)
    return windows


def inspect_bhoonidhi(
    *,
    aoi_path: Path,
    start_date: date,
    end_date: date,
    output_path: Path,
    collection: str | None = None,
) -> None:
    user_id = os.environ.get("BHOONIDHI_USER_ID")
    password = os.environ.get("BHOONIDHI_PASSWORD")
    if not user_id or not password:
        raise RuntimeError(
            "Set BHOONIDHI_USER_ID and BHOONIDHI_PASSWORD locally; "
            "do not put credentials in source code or chat."
        )

    extra_filters: dict[str, Any] = {
        "filter": {
            "args": [{"property": "Online"}, "Y"],
            "op": "eq",
        },
        "filter-lang": "cql2-json",
    }
    if collection:
        extra_filters["collections"] = [collection]

    client = BhoonidhiClient(
        credentials=BhoonidhiCredentials(user_id=user_id, password=password),
        config=BhoonidhiConfig(
            base_url=os.environ.get(
                "BHOONIDHI_BASE_URL",
                "https://bhoonidhi-api.nrsc.gov.in",
            )
        ),
    )
    geometry = _load_geometry(aoi_path)
    scenes_by_id = {}
    for window_start, window_end in _date_windows(start_date, end_date):
        for scene in client.search(
            geometry,
            window_start,
            window_end,
            extra_filters=extra_filters,
        ):
            scenes_by_id[scene.product_id] = scene
    scenes = sorted(
        scenes_by_id.values(),
        key=lambda scene: (
            scene.acquisition_date is None,
            scene.acquisition_date,
            scene.product_id,
        ),
    )
    payload = {
        "query": {
            "aoi": str(aoi_path),
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "collection": collection,
        },
        "scene_count": len(scenes),
        "scenes": [
            {
                "product_id": scene.product_id,
                "acquisition_date": (
                    scene.acquisition_date.isoformat()
                    if scene.acquisition_date
                    else None
                ),
                "download_reference": scene.download_reference,
                "metadata": _redact(scene.metadata),
            }
            for scene in scenes
        ],
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=True),
        encoding="utf-8",
    )
    print(f"Saved {len(scenes)} redacted scenes to {output_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--aoi", type=Path, required=True)
    parser.add_argument("--start-date", type=date.fromisoformat, required=True)
    parser.add_argument("--end-date", type=date.fromisoformat, required=True)
    parser.add_argument("--collection")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    inspect_bhoonidhi(
        aoi_path=args.aoi,
        start_date=args.start_date,
        end_date=args.end_date,
        output_path=args.output,
        collection=args.collection,
    )


if __name__ == "__main__":
    main()
