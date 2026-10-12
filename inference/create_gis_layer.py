import os

import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio

from shapely.geometry import shape
from rasterio.features import shapes


# ============================================================
# CONFIGURATION
# ============================================================

LABELED_MASK = (
    r"E:\UrbanEye\outputs\components"
    r"\AOI10_labeled.npy"
)

PROBABILITY_MAP = (
    r"E:\UrbanEye\outputs\stitched"
    r"\AOI10_probability.npy"
)

REFERENCE_TIF = (
    r"E:\UrbanEye\processed_data\patches\test\2024"
    r"\AOI10_y000_x000.tif"
)

OUTPUT_DIR = (
    r"E:\UrbanEye\outputs\gis"
)

OUTPUT_GPKG = (
    r"E:\UrbanEye\outputs\gis"
    r"\AOI10_detected_change.gpkg"
)

OUTPUT_CSV = (
    r"E:\UrbanEye\outputs\gis"
    r"\AOI10_regions.csv"
)


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print("UrbanEye - FINAL GIS CHANGE REGION GENERATION")
    print("=" * 70)

    os.makedirs(
        OUTPUT_DIR,
        exist_ok=True
    )

    # --------------------------------------------------------
    # Load component labels and probability map
    # --------------------------------------------------------

    labeled = np.load(
        LABELED_MASK
    ).astype(np.int32)

    probability = np.load(
        PROBABILITY_MAP
    ).astype(np.float32)

    print(
        f"Raster shape: {labeled.shape}"
    )

    print(
        f"Components: {labeled.max()}"
    )

    # --------------------------------------------------------
    # Read actual geospatial metadata
    # --------------------------------------------------------

    with rasterio.open(
        REFERENCE_TIF
    ) as src:

        transform = src.transform
        crs = src.crs
        resolution_x = src.res[0]
        resolution_y = src.res[1]

    print(
        f"CRS: {crs}"
    )

    print(
        f"Resolution: "
        f"{resolution_x} m x {resolution_y} m"
    )

    # --------------------------------------------------------
    # Polygonize labeled components
    #
    # Each component ID becomes its own polygon.
    # --------------------------------------------------------

    records = []

    polygon_generator = shapes(
        labeled,
        mask=(labeled > 0),
        transform=transform,
        connectivity=8
    )

    for geometry, value in polygon_generator:

        region_id = int(value)

        if region_id == 0:
            continue

        polygon = shape(
            geometry
        )

        # ----------------------------------------------------
        # Exact pixels belonging to this component
        # ----------------------------------------------------

        component_mask = (
            labeled == region_id
        )

        pixel_count = int(
            component_mask.sum()
        )

        if pixel_count == 0:
            continue

        # ----------------------------------------------------
        # Exact probability values for this component
        # ----------------------------------------------------

        component_probabilities = (
            probability[component_mask]
        )

        mean_probability = float(
            component_probabilities.mean()
        )

        max_probability = float(
            component_probabilities.max()
        )

        # ----------------------------------------------------
        # Coordinates
        # ----------------------------------------------------

        y_coords, x_coords = np.where(
            component_mask
        )

        centroid_x_pixel = float(
            x_coords.mean()
        )

        centroid_y_pixel = float(
            y_coords.mean()
        )

        # ----------------------------------------------------
        # Geographic centroid
        # ----------------------------------------------------

        centroid = polygon.centroid

        # ----------------------------------------------------
        # Area
        # ----------------------------------------------------

        area_m2 = float(
            pixel_count
            * resolution_x
            * resolution_y
        )

        area_hectares = (
            area_m2 / 10000.0
        )

        # ----------------------------------------------------
        # Bounding box
        # ----------------------------------------------------

        minx, miny, maxx, maxy = (
            polygon.bounds
        )

        records.append(
            {
                "region_id": region_id,
                "pixel_count": pixel_count,
                "area_m2": area_m2,
                "area_hectares": area_hectares,
                "mean_probability": mean_probability,
                "max_probability": max_probability,
                "centroid_easting": centroid.x,
                "centroid_northing": centroid.y,
                "centroid_pixel_x":
                    centroid_x_pixel,
                "centroid_pixel_y":
                    centroid_y_pixel,
                "min_easting": minx,
                "min_northing": miny,
                "max_easting": maxx,
                "max_northing": maxy,
                "geometry": polygon
            }
        )

    # --------------------------------------------------------
    # Create GeoDataFrame
    # --------------------------------------------------------

    gdf = gpd.GeoDataFrame(
        records,
        crs=crs
    )

    # --------------------------------------------------------
    # Sort by area
    # --------------------------------------------------------

    gdf = gdf.sort_values(
        by="area_m2",
        ascending=False
    ).reset_index(
        drop=True
    )

    gdf.insert(
        0,
        "rank",
        np.arange(
            1,
            len(gdf) + 1
        )
    )

    # --------------------------------------------------------
    # Save GeoPackage
    # --------------------------------------------------------

    gdf.to_file(
        OUTPUT_GPKG,
        layer="detected_change",
        driver="GPKG"
    )

    # --------------------------------------------------------
    # Save CSV
    # --------------------------------------------------------

    csv_df = gdf.drop(
        columns="geometry"
    )

    csv_df.to_csv(
        OUTPUT_CSV,
        index=False
    )

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    print("\n" + "-" * 70)
    print("GIS REGION SUMMARY")
    print("-" * 70)

    print(
        f"Detected regions : {len(gdf)}"
    )

    print(
        f"Total pixels     : "
        f"{gdf['pixel_count'].sum()}"
    )

    print(
        f"Total area       : "
        f"{gdf['area_m2'].sum():.2f} m²"
    )

    print(
        f"Total area       : "
        f"{gdf['area_hectares'].sum():.4f} ha"
    )

    print(
        f"Largest region   : "
        f"{gdf['area_m2'].max():.2f} m²"
    )

    print(
        f"Mean region area : "
        f"{gdf['area_m2'].mean():.2f} m²"
    )

    print(
        f"Mean confidence  : "
        f"{gdf['mean_probability'].mean():.4f}"
    )

    print("\nTop 10 regions:")

    print(
        gdf[
            [
                "rank",
                "region_id",
                "pixel_count",
                "area_m2",
                "area_hectares",
                "mean_probability",
                "max_probability"
            ]
        ].head(10).to_string(
            index=False
        )
    )

    print("\n" + "-" * 70)

    print(
        "GeoPackage:"
    )

    print(
        OUTPUT_GPKG
    )

    print(
        "\nCSV:"
    )

    print(
        OUTPUT_CSV
    )

    print("\n" + "=" * 70)
    print("FINAL GIS LAYER GENERATED")
    print("=" * 70)


if __name__ == "__main__":
    main()