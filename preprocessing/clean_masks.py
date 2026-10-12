import os
import glob
import numpy as np
import rasterio
import cv2

# ============================================
# FOLDERS
# ============================================

input_folder = r"E:/UrbanEye/processed_data/masks"
output_folder = r"E:/UrbanEye/processed_data/clean_masks"

os.makedirs(output_folder, exist_ok=True)

mask_files = sorted(glob.glob(os.path.join(input_folder, "*.tif")))

print(f"\nFound {len(mask_files)} masks.\n")

# ============================================
# MORPHOLOGY KERNEL
# ============================================

kernel = np.ones((3,3), np.uint8)

# ============================================
# PROCESS
# ============================================

for mask_path in mask_files:

    name = os.path.basename(mask_path)

    print(f"Cleaning {name}")

    with rasterio.open(mask_path) as src:

        mask = src.read(1)

        profile = src.profile.copy()

    # Convert to uint8
    mask = (mask > 0).astype(np.uint8) * 255

    # Remove isolated pixels
    mask = cv2.morphologyEx(
        mask,
        cv2.MORPH_OPEN,
        kernel,
        iterations=1
    )

    # Fill small holes
    mask = cv2.morphologyEx(
        mask,
        cv2.MORPH_CLOSE,
        kernel,
        iterations=1
    )

    profile.update(
        dtype=rasterio.uint8,
        count=1,
        compress="lzw"
    )

    output_path = os.path.join(output_folder, name)

    with rasterio.open(output_path, "w", **profile) as dst:
        dst.write(mask, 1)

print("\nMasks cleaned successfully.")