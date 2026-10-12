from pathlib import Path

import numpy as np
import rasterio
from tqdm import tqdm


# -----------------------------
# Folder paths
# -----------------------------
BASE_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = BASE_DIR / "output" / "2024"  
print(RAW_DIR.resolve())
print(RAW_DIR.exists())
if RAW_DIR.exists():
    print(list(RAW_DIR.iterdir()))
OUTPUT_DIR = BASE_DIR / "processed_data" / "normalized" / "2024_Norm"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def normalize_band(band):
    """
    Normalize one band using 2nd and 98th percentiles.
    Output values are in [0,1].
    """

    band = band.astype(np.float32)

    p2 = np.percentile(band, 2)
    p98 = np.percentile(band, 98)

    band = np.clip(band, p2, p98)
    band = (band - p2) / (p98 - p2 + 1e-8)

    return band


def normalize_image(input_path, output_path):

    with rasterio.open(input_path) as src:

        image = src.read()

        profile = src.profile.copy()

    normalized = np.zeros_like(image, dtype=np.float32)

    for i in range(image.shape[0]):
        normalized[i] = normalize_band(image[i])

    profile.update(dtype=rasterio.float32)

    with rasterio.open(output_path, "w", **profile) as dst:
        dst.write(normalized)

    print(f"Saved: {output_path}")


def main():

    images = sorted(RAW_DIR.glob("*.tif"))

    print(f"Found {len(images)} images.\n")

    for img in tqdm(images):

        output = OUTPUT_DIR / f"{img.stem}_norm.tif"

        normalize_image(img, output)


if __name__ == "__main__":
    main()