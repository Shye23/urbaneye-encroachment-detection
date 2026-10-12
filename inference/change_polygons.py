import os
import sys
import numpy as np
import geopandas as gpd
import rasterio

from rasterio.features import shapes
from shapely.geometry import shape

sys.path.insert(0,r"E:\UrbanEye")
# ============================================================
# CONFIG
# ============================================================

PROJECT_ROOT = r"E:\UrbanEye"

MASK_PATH = os.path.join(
    PROJECT_ROOT,
    "outputs",
    "postprocessed",
    "AOI10_postprocessed.npy"
)

REFERENCE_TIF = os.path.join(
    PROJECT_ROOT,
    "processed_data",
    "patches",
    "test",
    "2024",
    "AOI10_y000_x000.tif"
)

OUTPUT_DIR = os.path.join(
    PROJECT_ROOT,
    "outputs",
    "gis"
)

os.makedirs(OUTPUT_DIR, exist_ok=True)

OUTPUT_PATH = os.path.join(
    OUTPUT_DIR,
    "AOI10_change_polygons.gpkg"
)


# ============================================================
# LOAD DATA
# ============================================================

print("Loading postprocessed change mask...")

mask = np.load(MASK_PATH)

print(f"Mask shape: {mask.shape}")
print(f"Changed pixels: {int(mask.sum())}")


# ============================================================
# GET GEOSPATIAL REFERENCE
# ============================================================

with rasterio.open(REFERENCE_TIF) as src:

    transform = src.transform
    crs = src.crs

    pixel_width = abs(transform.a)
    pixel_height = abs(transform.e)

    origin_x = transform.c
    origin_y = transform.f


print(f"CRS: {crs}")
print(f"Pixel size: {pixel_width} x {pixel_height} m")


# ============================================================
# POLYGONIZE
# ============================================================

print("\nPolygonizing change mask...")

mask_uint8 = mask.astype(np.uint8)

polygon_records = []

region_id = 1

for geom, value in shapes(
    mask_uint8,
    mask=mask_uint8 == 1,
    transform=transform,
    connectivity=8
):

    if value != 1:
        continue

    polygon = shape(geom)

    if polygon.is_empty:
        continue

    if not polygon.is_valid:
        polygon = polygon.buffer(0)

    area = polygon.area

    polygon_records.append({
        "candidate_id": f"C{region_id:03d}",
        "change_area_m2": area,
        "change_pixels": area / (pixel_width * pixel_height),
        "source": "URBANEYE",
        "geometry": polygon
    })

    region_id += 1


# ============================================================
# SAVE
# ============================================================

gdf = gpd.GeoDataFrame(
    polygon_records,
    crs=crs
)

gdf.to_file(
    OUTPUT_PATH,
    layer="change_polygons",
    driver="GPKG"
)


# ============================================================
# SUMMARY
# ============================================================

print("\n" + "=" * 60)
print("CHANGE POLYGONIZATION COMPLETE")
print("=" * 60)

print(f"Regions: {len(gdf)}")
print(f"Total change area: {gdf['change_area_m2'].sum():.2f} m²")
print(f"Output: {OUTPUT_PATH}")

print("\nLargest regions:")

print(
    gdf[
        ["candidate_id", "change_area_m2"]
    ]
    .sort_values(
        "change_area_m2",
        ascending=False
    )
    .head(10)
    .to_string(index=False)
)