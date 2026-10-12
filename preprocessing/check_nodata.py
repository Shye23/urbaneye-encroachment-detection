from pathlib import Path
import rasterio
import numpy as np

INPUT_DIR = Path("./processed_data/normalized")

for image_path in INPUT_DIR.glob("*.tif"):
    print(f"\nChecking: {image_path.name}")

    with rasterio.open(image_path) as src:
        image = src.read()

        print("NoData value :", src.nodata)
        print("Shape        :", image.shape)
        print("Min          :", image.min())
        print("Max          :", image.max())

        if src.nodata is not None:
            nodata_pixels = np.sum(image == src.nodata)
            print("NoData pixels:", nodata_pixels)
        else:
            print("NoData pixels: None defined")