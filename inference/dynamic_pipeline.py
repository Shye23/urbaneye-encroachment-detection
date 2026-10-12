from pathlib import Path

import numpy as np
import rasterio
from rasterio.features import shapes

from shapely.geometry import shape
import geopandas as gpd

from inference.inference_engine import UrbanEyeInference


def polygonize_prediction(
    prediction,
    transform,
    crs
):

    polygons = []

    for geom, value in shapes(
        prediction.astype(np.uint8),
        mask=prediction.astype(bool),
        transform=transform
    ):

        if value == 1:

            polygons.append(
                shape(geom)
            )

    if not polygons:

        return gpd.GeoDataFrame(
            {
                "change_id": [],
                "area_m2": [],
                "geometry": []
            },
            geometry="geometry",
            crs=crs
        )

    gdf = gpd.GeoDataFrame(
        {
            "geometry": polygons
        },
        geometry="geometry",
        crs=crs
    )

    gdf["area_m2"] = (
        gdf.geometry.area
    )

    gdf["change_id"] = [
        f"CHG-{i:03d}"
        for i in range(
            1,
            len(gdf) + 1
        )
    ]

    return gdf[
        [
            "change_id",
            "area_m2",
            "geometry"
        ]
    ]


def run_detection(
    image_2020,
    image_2024,
    checkpoint,
    output_dir,
    threshold=0.60
):

    output_dir = Path(
        output_dir
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    print("\n")
    print("=" * 60)
    print("URBANEYE DYNAMIC DETECTION")
    print("=" * 60)

    engine = UrbanEyeInference(
        checkpoint_path=checkpoint,
        threshold=threshold
    )

    result = engine.predict(
        image_2020,
        image_2024
    )

    probability = result[
        "probability"
    ]

    prediction = result[
        "prediction"
    ]

    transform = result[
        "transform"
    ]

    crs = result[
        "crs"
    ]

    np.save(
        output_dir /
        "probability.npy",
        probability
    )

    np.save(
        output_dir /
        "prediction.npy",
        prediction
    )

    polygons = polygonize_prediction(
        prediction,
        transform,
        crs
    )

    gpkg_path = (
        output_dir /
        "change_polygons.gpkg"
    )

    geojson_path = (
        output_dir /
        "change_polygons.geojson"
    )

    polygons.to_file(
        gpkg_path,
        layer="change_polygons",
        driver="GPKG"
    )

    polygons.to_file(
        geojson_path,
        driver="GeoJSON"
    )

    print(
        f"\nDetected regions: "
        f"{len(polygons)}"
    )

    print(
        f"Total change area: "
        f"{polygons['area_m2'].sum():,.2f} m²"
    )

    print(
        f"\nSaved:"
    )

    print(
        f"  {gpkg_path}"
    )

    print(
        f"  {geojson_path}"
    )

    return {
        "probability": probability,
        "prediction": prediction,
        "polygons": polygons
    }