import os
import numpy as np
import geopandas as gpd
import rasterio
from rasterio.mask import mask
from tqdm import tqdm

# =====================================================
# CHANGE THESE PATHS
# =====================================================

RASTER_2020 = r"E:/UrbanEye/raw data/resourcesat/2020/BH_R2F02DEC2020049934009400058SSANSTUC00GTDD/LISS4_2020.vrt"
RASTER_2024 = r"E:/UrbanEye/raw data/resourcesat/2024/R2F10DEC2024070801009500058SSANSTUC00GTDC/LISS4_2024.vrt"

AOI_FOLDER = r"E:/UrbanEye/raw data/cropped/AOIs"

OUTPUT_2020 = r"E:/UrbanEye/output/2020"
OUTPUT_2024 = r"E:/UrbanEye/output/2024"

os.makedirs(OUTPUT_2020, exist_ok=True)
os.makedirs(OUTPUT_2024, exist_ok=True)

# =====================================================
# CROP FUNCTION
# =====================================================

def crop_raster(input_raster, output_folder, year):

    print(f"\nCropping {year} images...")

    with rasterio.open(input_raster) as src:

        aoi_files = sorted(
            [f for f in os.listdir(AOI_FOLDER) if f.endswith(".gpkg")]
        )

        for idx, aoi in enumerate(tqdm(aoi_files), start=1):

            aoi_path = os.path.join(AOI_FOLDER, aoi)

            gdf = gpd.read_file(aoi_path)

            if gdf.crs != src.crs:
                gdf = gdf.to_crs(src.crs)

            geometries = [geom for geom in gdf.geometry]

            cropped_image, cropped_transform = mask(
                src,
                geometries,
                crop=True
            )

            metadata = src.meta.copy()

            metadata.update({
                "driver": "GTiff",
                "height": cropped_image.shape[1],
                "width": cropped_image.shape[2],
                "transform": cropped_transform
            })

            output_name = f"AOI{idx:02d}_{year}.tif"

            output_path = os.path.join(output_folder, output_name)

            with rasterio.open(output_path, "w", **metadata) as dest:
                dest.write(cropped_image)

    print(f"Finished {year}.\n")


# =====================================================
# VERIFY OUTPUTS
# =====================================================

def verify_alignment():

    print("\n==============================")
    print("VERIFYING CROPPED AOIs")
    print("==============================\n")

    files2020 = sorted(os.listdir(OUTPUT_2020))
    files2024 = sorted(os.listdir(OUTPUT_2024))

    print(f"{'AOI':<10}{'Shape':<20}{'Aligned'}")

    print("-"*45)

    all_ok = True

    for f20, f24 in zip(files2020, files2024):

        path20 = os.path.join(OUTPUT_2020, f20)
        path24 = os.path.join(OUTPUT_2024, f24)

        with rasterio.open(path20) as img20, rasterio.open(path24) as img24:

            shape_match = (
                img20.width == img24.width and
                img20.height == img24.height
            )

            transform_match = (
                img20.transform == img24.transform
            )

            crs_match = (
                img20.crs == img24.crs
            )

            aligned = (
                shape_match and
                transform_match and
                crs_match
            )

            if aligned:
                status = "✓"
            else:
                status = "✗"
                all_ok = False

            print(
                f"{f20:<10}"
                f"{img20.width}x{img20.height:<12}"
                f"{status}"
            )

    print("\n==============================")

    if all_ok:
        print("SUCCESS")
        print("All AOIs have identical dimensions, CRS and alignment.")
    else:
        print("WARNING")
        print("Some AOIs are not perfectly aligned.")

    print("==============================\n")


# =====================================================
# MAIN
# =====================================================

if __name__ == "__main__":

    crop_raster(RASTER_2020, OUTPUT_2020, "2020")

    crop_raster(RASTER_2024, OUTPUT_2024, "2024")

    verify_alignment()

    print("Cropping completed successfully.")