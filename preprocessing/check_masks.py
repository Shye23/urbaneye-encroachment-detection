import rasterio
import numpy as np

mask_path = r"E:/UrbanEye/processed_data/patches/train/masks/AOI01_y000_x000.tif"

with rasterio.open(mask_path) as src:
    mask = src.read(1)

print("Shape:", mask.shape)
print("Data type:", mask.dtype)
print("Minimum:", mask.min())
print("Maximum:", mask.max())
print("Unique values:", np.unique(mask))
print("Changed pixels:", np.count_nonzero(mask))
print("Total pixels:", mask.size)