import os
import glob
import numpy as np
import rasterio

# =====================================================
# INPUT FOLDERS
# =====================================================

folder2020 = r"E:/UrbanEye/processed_data/normalized/2020_Norm"
folder2024 = r"E:/UrbanEye/processed_data/normalized/2024_Norm"

output_folder = r"E:/UrbanEye/processed_data/differences"

os.makedirs(output_folder, exist_ok=True)

# =====================================================
# FIND IMAGE PAIRS
# =====================================================

images2020 = sorted(glob.glob(os.path.join(folder2020, "*.tif")))
images2024 = sorted(glob.glob(os.path.join(folder2024, "*.tif")))

assert len(images2020) == len(images2024), \
    "Different number of images found!"

print(f"\nFound {len(images2020)} image pairs.\n")

# =====================================================
# PROCESS EACH PAIR
# =====================================================

for img20, img24 in zip(images2020, images2024):

    name = os.path.basename(img20)

    print(f"Processing {name}")

    with rasterio.open(img20) as src20, rasterio.open(img24) as src24:

        image20 = src20.read().astype(np.float32)
        image24 = src24.read().astype(np.float32)

        # -----------------------------------------------
        # Verify alignment
        # -----------------------------------------------

        assert image20.shape == image24.shape, \
            f"Shape mismatch in {name}"

        assert src20.crs == src24.crs, \
            f"CRS mismatch in {name}"

        assert src20.transform == src24.transform, \
            f"Transform mismatch in {name}"

        # -----------------------------------------------
        # Mean Absolute Difference
        # Produces one grayscale change image
        # -----------------------------------------------

        difference = np.mean(
            np.abs(image24 - image20),
            axis=0
        )

        # -----------------------------------------------
        # Save output
        # -----------------------------------------------

        profile = src20.profile.copy()

        profile.update(
            driver="GTiff",
            dtype=rasterio.float32,
            count=1,
            compress="lzw"
        )

        output_path = os.path.join(output_folder, name)

        with rasterio.open(output_path, "w", **profile) as dst:
            dst.write(difference.astype(np.float32), 1)

print("\n====================================")
print(" Difference images created!")
print(f" Saved in: {output_folder}")
print("====================================")