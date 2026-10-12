import json

import geopandas as gpd
import rasterio
from rasterio.mask import mask
from shapely.geometry import shape


def load_aoi_geojson(path):

    with open(path, "r") as f:
        data = json.load(f)

    if data["type"] == "FeatureCollection":

        if len(data["features"]) != 1:
            raise ValueError(
                "AOI GeoJSON must contain "
                "exactly one feature."
            )

        geometry = shape(
            data["features"][0]["geometry"]
        )

    elif data["type"] == "Feature":

        geometry = shape(
            data["geometry"]
        )

    else:

        geometry = shape(data)

    return geometry


def clip_raster_to_aoi(
    raster_path,
    aoi_geometry,
    aoi_crs="EPSG:4326"
):

    with rasterio.open(raster_path) as src:

        aoi = gpd.GeoDataFrame(
            geometry=[aoi_geometry],
            crs=aoi_crs
        )

        aoi = aoi.to_crs(
            src.crs
        )

        geometries = [
            aoi.geometry.iloc[0]
        ]

        clipped, transform = mask(
            src,
            geometries,
            crop=True
        )

        profile = src.profile.copy()

        profile.update(
            {
                "height": clipped.shape[1],
                "width": clipped.shape[2],
                "transform": transform
            }
        )

    return (
        clipped,
        profile,
        transform
    )