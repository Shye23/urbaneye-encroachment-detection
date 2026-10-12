import os
import glob
import numpy as np
import rasterio
import cv2

# =====================================================
# FOLDERS
# =====================================================

difference_folder = r"E:/UrbanEye/processed_data/differences"
output_folder = r"E:/UrbanEye/processed_data/masks"

os.makedirs(output_folder, exist_ok=True)

difference_images = sorted(glob.glob(os.path.join(difference_folder, "*.tif")))

print(f"\nFound {len(difference_images)} difference images.\n")

# =====================================================
# PARAMETERS
# =====================================================

GAUSSIAN_KERNEL = (5, 5)
MIN_AREA = 30          # Try 20–40 depending on results
MAX_AREA = 100000      # Keep all realistic buildings

kernel = np.ones((3, 3), np.uint8)

# =====================================================
# PROCESS
# =====================================================

for diff_path in difference_images:

    filename = os.path.basename(diff_path)
    print(f"Processing {filename}")

    with rasterio.open(diff_path) as src:

        diff = src.read(1).astype(np.float32)
        profile = src.profile.copy()

    # -------------------------------------------------
    # Gaussian smoothing
    # -------------------------------------------------

    diff = cv2.GaussianBlur(diff, GAUSSIAN_KERNEL, 0)

    # -------------------------------------------------
    # Normalize to 8-bit
    # -------------------------------------------------

    diff = diff - diff.min()

    if diff.max() > 0:
        diff = diff / diff.max()

    diff = (diff * 255).astype(np.uint8)

    # -------------------------------------------------
    # Otsu threshold
    # -------------------------------------------------

    _, mask = cv2.threshold(
        diff,
        0,
        255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )

    # -------------------------------------------------
    # Connected components
    # -------------------------------------------------

    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(
        mask,
        connectivity=8
    )

    clean = np.zeros_like(mask)

    for i in range(1, num_labels):

        area = stats[i, cv2.CC_STAT_AREA]

        if MIN_AREA <= area <= MAX_AREA:
            clean[labels == i] = 255

    mask = clean

    # -------------------------------------------------
    # Fill tiny holes
    # -------------------------------------------------

    mask = cv2.morphologyEx(
        mask,
        cv2.MORPH_CLOSE,
        kernel,
        iterations=1
    )

    # -------------------------------------------------
    # Save
    # -------------------------------------------------

    profile.update(
        dtype=rasterio.uint8,
        count=1,
        compress="lzw"
    )

    output_path = os.path.join(output_folder, filename)

    with rasterio.open(output_path, "w", **profile) as dst:
        dst.write(mask, 1)

print("\n===================================")
print("Masks created successfully!")
print("===================================")