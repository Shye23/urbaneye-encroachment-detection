import os
import re
import torch
import numpy as np
import rasterio
import matplotlib.pyplot as plt
import sys

sys.path.insert(0, r"E:\UrbanEye")
from models.snunet_cd import SNUNetCD


# ============================================================
# CONFIGURATION
# ============================================================

TEST_2020 = r"E:\UrbanEye\processed_data\patches\test\2020"
TEST_2024 = r"E:\UrbanEye\processed_data\patches\test\2024"

CHECKPOINT = (
    r"E:\UrbanEye\training\checkpoints\snunet"
    r"\baseline\best_model.pth"
)

OUTPUT_DIR = r"E:\UrbanEye\outputs\stitched"

PATCH_SIZE = 32
THRESHOLD = 0.60

DEVICE = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)


# ============================================================
# HELPERS
# ============================================================

def read_tif(path):
    """
    Read TIFF and return float32 CHW array.
    """

    with rasterio.open(path) as src:
        image = src.read().astype(np.float32)

    image = np.nan_to_num(image)

    return image


def normalize_image_for_model(image):
    """
    Match the basic preprocessing used by the project.
    """

    return np.nan_to_num(
        image.astype(np.float32)
    )


def parse_patch_name(filename):
    """
    Extract AOI, y and x from names such as:

    AOI10_y000_x000.tif
    AOI10_y000_x016.tif
    """

    pattern = r"(.+)_y(\d+)_x(\d+)\.tif"

    match = re.match(
        pattern,
        filename
    )

    if match is None:
        raise ValueError(
            f"Could not parse patch filename: {filename}"
        )

    aoi = match.group(1)
    y = int(match.group(2))
    x = int(match.group(3))

    return aoi, y, x


def normalize_for_display(image):
    """
    Convert first three channels to RGB display.
    """

    image = image[:3].transpose(1, 2, 0)

    image = np.nan_to_num(image)

    min_val = image.min()
    max_val = image.max()

    if max_val > min_val:
        image = (
            image - min_val
        ) / (
            max_val - min_val
        )

    return np.clip(image, 0, 1)


# ============================================================
# LOAD MODEL
# ============================================================

def load_model():

    print("=" * 70)
    print("UrbanEye - STITCHED TEST PREDICTIONS")
    print("=" * 70)

    print(f"Device: {DEVICE}")

    if torch.cuda.is_available():
        print(
            f"GPU: {torch.cuda.get_device_name(0)}"
        )

    checkpoint = torch.load(
        CHECKPOINT,
        map_location=DEVICE
    )

    model = SNUNetCD(
        in_channels=3,
        out_channels=1
    ).to(DEVICE)

    model.load_state_dict(
        checkpoint["model_state_dict"]
    )

    model.eval()

    print("SNUNet-CD loaded successfully.")

    return model


# ============================================================
# MAIN
# ============================================================

def main():

    os.makedirs(
        OUTPUT_DIR,
        exist_ok=True
    )

    model = load_model()

    # --------------------------------------------------------
    # Find test patches
    # --------------------------------------------------------

    files_2020 = sorted(
        f for f in os.listdir(TEST_2020)
        if f.lower().endswith(".tif")
    )

    print(
        f"\nTest patches found: {len(files_2020)}"
    )

    # --------------------------------------------------------
    # Group patches by AOI
    # --------------------------------------------------------

    aoi_patches = {}

    for filename in files_2020:

        aoi, y, x = parse_patch_name(filename)

        if aoi not in aoi_patches:
            aoi_patches[aoi] = []

        aoi_patches[aoi].append(
            (y, x, filename)
        )

    print(
        f"AOIs found: {len(aoi_patches)}"
    )

    # --------------------------------------------------------
    # Process each AOI
    # --------------------------------------------------------

    with torch.no_grad():

        for aoi, patches in aoi_patches.items():

            print("\n" + "-" * 70)
            print(f"Processing {aoi}")
            print("-" * 70)

            max_y = max(
                p[0] for p in patches
            )

            max_x = max(
                p[1] for p in patches
            )

            height = max_y + PATCH_SIZE
            width = max_x + PATCH_SIZE

            probability_sum = np.zeros(
                (height, width),
                dtype=np.float32
            )

            probability_count = np.zeros(
                (height, width),
                dtype=np.float32
            )

            # ------------------------------------------------
            # Stitch predictions
            # ------------------------------------------------

            for index, (y, x, filename) in enumerate(patches):

                path_2020 = os.path.join(
                    TEST_2020,
                    filename
                )

                path_2024 = os.path.join(
                    TEST_2024,
                    filename
                )

                image_2020 = read_tif(
                    path_2020
                )

                image_2024 = read_tif(
                    path_2024
                )

                image_2020 = normalize_image_for_model(
                    image_2020
                )

                image_2024 = normalize_image_for_model(
                    image_2024
                )

                tensor_2020 = torch.from_numpy(
                    image_2020
                ).unsqueeze(0).to(DEVICE)

                tensor_2024 = torch.from_numpy(
                    image_2024
                ).unsqueeze(0).to(DEVICE)

                logits = model(
                    tensor_2020,
                    tensor_2024
                )

                probability = torch.sigmoid(
                    logits
                )

                probability = (
                    probability[0, 0]
                    .cpu()
                    .numpy()
                )

                # --------------------------------------------
                # Add overlapping patch
                # --------------------------------------------

                probability_sum[
                    y:y + PATCH_SIZE,
                    x:x + PATCH_SIZE
                ] += probability

                probability_count[
                    y:y + PATCH_SIZE,
                    x:x + PATCH_SIZE
                ] += 1

                if (index + 1) % 20 == 0:
                    print(
                        f"  {index + 1}/{len(patches)} patches"
                    )

            # ------------------------------------------------
            # Average overlapping predictions
            # ------------------------------------------------

            stitched_probability = (
                probability_sum
                / np.maximum(
                    probability_count,
                    1
                )
            )

            stitched_prediction = (
                stitched_probability
                >= THRESHOLD
            ).astype(np.uint8)

            # ------------------------------------------------
            # Save NumPy arrays
            # ------------------------------------------------

            probability_path = os.path.join(
                OUTPUT_DIR,
                f"{aoi}_probability.npy"
            )

            prediction_path = os.path.join(
                OUTPUT_DIR,
                f"{aoi}_prediction.npy"
            )

            np.save(
                probability_path,
                stitched_probability
            )

            np.save(
                prediction_path,
                stitched_prediction
            )

            # ------------------------------------------------
            # Create visualization
            # ------------------------------------------------

            # Use the first patch as display background.
            first_patch = patches[0]

            first_filename = first_patch[2]

            image_2024 = read_tif(
                os.path.join(
                    TEST_2024,
                    first_filename
                )
            )

            rgb = normalize_for_display(
                image_2024
            )

            fig, axes = plt.subplots(
                1,
                3,
                figsize=(15, 5)
            )

            axes[0].imshow(
                stitched_probability,
                cmap="viridis",
                vmin=0,
                vmax=1
            )

            axes[0].set_title(
                f"{aoi} - Probability"
            )

            axes[0].axis("off")

            axes[1].imshow(
                stitched_prediction,
                cmap="gray"
            )

            axes[1].set_title(
                f"Prediction @ {THRESHOLD}"
            )

            axes[1].axis("off")

            # ------------------------------------------------
            # Overlay
            # ------------------------------------------------

            axes[2].imshow(rgb)

            overlay = np.zeros(
                (
                    stitched_prediction.shape[0],
                    stitched_prediction.shape[1],
                    4
                )
            )

            overlay[:, :, 0] = 1.0

            overlay[:, :, 3] = (
                stitched_prediction * 0.55
            )

            axes[2].imshow(
                overlay
            )

            axes[2].set_title(
                "Detected Change"
            )

            axes[2].axis("off")

            fig.suptitle(
                f"UrbanEye - {aoi}",
                fontsize=16
            )

            plt.tight_layout()

            figure_path = os.path.join(
                OUTPUT_DIR,
                f"{aoi}_stitched.png"
            )

            plt.savefig(
                figure_path,
                dpi=200,
                bbox_inches="tight"
            )

            plt.close(fig)

            print(
                f"Saved: {figure_path}"
            )

    print("\n" + "=" * 70)
    print("STITCHING COMPLETE")
    print("=" * 70)

    print(
        f"Output folder: {OUTPUT_DIR}"
    )


if __name__ == "__main__":
    main()