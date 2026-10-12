import os
import glob
import numpy as np
import rasterio


MASK_FOLDER = r"E:/UrbanEye/processed_data/patches/train/masks"


files = sorted(glob.glob(os.path.join(MASK_FOLDER, "*.tif")))

if len(files) == 0:
    raise ValueError(f"No mask files found in:\n{MASK_FOLDER}")


total_pixels = 0
positive_pixels = 0
negative_pixels = 0

patches_with_change = 0
patches_without_change = 0

positive_percentages = []


print("=" * 70)
print("TRAINING MASK CLASS BALANCE")
print("=" * 70)

print(f"Mask folder: {MASK_FOLDER}")
print(f"Number of masks: {len(files)}")

for path in files:

    with rasterio.open(path) as src:
        mask = src.read(1)

    mask = mask > 0

    positives = np.count_nonzero(mask)
    pixels = mask.size
    negatives = pixels - positives

    total_pixels += pixels
    positive_pixels += positives
    negative_pixels += negatives

    percentage = (positives / pixels) * 100
    positive_percentages.append(percentage)

    if positives > 0:
        patches_with_change += 1
    else:
        patches_without_change += 1


positive_ratio = positive_pixels / total_pixels
negative_ratio = negative_pixels / total_pixels

pos_weight = negative_pixels / positive_pixels


print()
print("-" * 70)
print("PIXEL COUNTS")
print("-" * 70)

print(f"Total pixels:      {total_pixels:,}")
print(f"Changed pixels:    {positive_pixels:,}")
print(f"Unchanged pixels:  {negative_pixels:,}")

print()
print("-" * 70)
print("PIXEL PERCENTAGES")
print("-" * 70)

print(f"Changed:           {positive_ratio * 100:.4f}%")
print(f"Unchanged:         {negative_ratio * 100:.4f}%")

print()
print("-" * 70)
print("PATCH STATISTICS")
print("-" * 70)

print(f"Patches with change:    {patches_with_change}")
print(f"Patches without change: {patches_without_change}")

print()
print("-" * 70)
print("CHANGED PIXELS PER PATCH")
print("-" * 70)

print(f"Minimum: {min(positive_percentages):.2f}%")
print(f"Maximum: {max(positive_percentages):.2f}%")
print(f"Mean:    {np.mean(positive_percentages):.2f}%")
print(f"Median:  {np.median(positive_percentages):.2f}%")

print()
print("-" * 70)
print("BCE POSITIVE WEIGHT")
print("-" * 70)

print(f"Recommended pos_weight: {pos_weight:.4f}")

print()
print("=" * 70)
print("CLASS BALANCE CHECK COMPLETE")
print("=" * 70)

