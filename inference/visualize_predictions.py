import os
import sys
import torch
import numpy as np
import matplotlib.pyplot as plt

from torch.utils.data import DataLoader

sys.path.insert(0, r"E:\UrbanEye")

from preprocessing.dataset import UrbanEyeDataset
from models.snunet_cd import SNUNetCD


# ============================================================
# CONFIGURATION
# ============================================================

DATA_ROOT = r"E:\UrbanEye\processed_data\patches"

CHECKPOINT = (
    r"E:\UrbanEye\training\checkpoints\snunet"
    r"\baseline\best_model.pth"
)

OUTPUT_DIR = r"E:\UrbanEye\outputs\qualitative"

THRESHOLD = 0.60
NUM_SAMPLES = 6
BATCH_SIZE = 1

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


# ============================================================
# HELPERS
# ============================================================

def normalize_for_display(image):
    """
    Convert CHW satellite image into an RGB image for display.
    Uses first three channels.
    """

    image = image[:3].transpose(1, 2, 0)

    image = np.nan_to_num(image)

    min_val = image.min()
    max_val = image.max()

    if max_val > min_val:
        image = (image - min_val) / (max_val - min_val)

    return np.clip(image, 0, 1)


def save_prediction(
    image_2020,
    image_2024,
    ground_truth,
    probability,
    prediction,
    sample_name,
    output_path
):
    """
    Save a six-panel qualitative prediction figure.
    """

    rgb_2020 = normalize_for_display(image_2020)
    rgb_2024 = normalize_for_display(image_2024)

    ground_truth = ground_truth.squeeze()
    probability = probability.squeeze()
    prediction = prediction.squeeze()

    fig, axes = plt.subplots(2, 3, figsize=(15, 9))

    # --------------------------------------------------------
    # 2020 image
    # --------------------------------------------------------

    axes[0, 0].imshow(rgb_2020)
    axes[0, 0].set_title("2020 Satellite")
    axes[0, 0].axis("off")

    # --------------------------------------------------------
    # 2024 image
    # --------------------------------------------------------

    axes[0, 1].imshow(rgb_2024)
    axes[0, 1].set_title("2024 Satellite")
    axes[0, 1].axis("off")

    # --------------------------------------------------------
    # Ground truth
    # --------------------------------------------------------

    axes[0, 2].imshow(ground_truth, cmap="gray")
    axes[0, 2].set_title("Ground Truth")
    axes[0, 2].axis("off")

    # --------------------------------------------------------
    # Probability map
    # --------------------------------------------------------

    im = axes[1, 0].imshow(probability, cmap="viridis", vmin=0, vmax=1)
    axes[1, 0].set_title("Model Probability")
    axes[1, 0].axis("off")

    fig.colorbar(im, ax=axes[1, 0], fraction=0.046, pad=0.04)

    # --------------------------------------------------------
    # Binary prediction
    # --------------------------------------------------------

    axes[1, 1].imshow(prediction, cmap="gray")
    axes[1, 1].set_title(f"Prediction (Threshold {THRESHOLD})")
    axes[1, 1].axis("off")

    # --------------------------------------------------------
    # Overlay
    # --------------------------------------------------------

    axes[1, 2].imshow(rgb_2024)

    overlay = np.zeros(
        (prediction.shape[0], prediction.shape[1], 4)
    )

    overlay[:, :, 0] = 1.0
    overlay[:, :, 3] = prediction * 0.55

    axes[1, 2].imshow(overlay)
    axes[1, 2].set_title("Detected Change Overlay")
    axes[1, 2].axis("off")

    fig.suptitle(
        f"UrbanEye - {sample_name}",
        fontsize=16
    )

    plt.tight_layout()

    plt.savefig(
        output_path,
        dpi=200,
        bbox_inches="tight"
    )

    plt.close(fig)


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print("UrbanEye - QUALITATIVE TEST PREDICTIONS")
    print("=" * 70)

    print(f"Device: {DEVICE}")

    if torch.cuda.is_available():
        print(f"GPU: {torch.cuda.get_device_name(0)}")
        print(f"CUDA: {torch.version.cuda}")

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # --------------------------------------------------------
    # Load test dataset
    # --------------------------------------------------------

    test_dataset = UrbanEyeDataset(
        DATA_ROOT,
        split="test"
    )

    print(f"\nTest samples: {len(test_dataset)}")

    test_loader = DataLoader(
        test_dataset,
        batch_size=BATCH_SIZE,
        shuffle=False
    )

    # --------------------------------------------------------
    # Load model
    # --------------------------------------------------------

    print("\nLoading checkpoint:")
    print(CHECKPOINT)

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

    # --------------------------------------------------------
    # Run inference
    # --------------------------------------------------------

    saved = 0

    with torch.no_grad():

        for batch_idx, batch in enumerate(test_loader):

            if saved >= NUM_SAMPLES:
                break

            image_2020 = batch[0].to(DEVICE)
            image_2024 = batch[1].to(DEVICE)
            mask = batch[2].to(DEVICE)

            logits = model(
                image_2020,
                image_2024
            )

            probability = torch.sigmoid(logits)

            prediction = (
                probability >= THRESHOLD
            ).float()

            # ------------------------------------------------
            # Convert to numpy
            # ------------------------------------------------

            img20_np = image_2020[0].cpu().numpy()
            img24_np = image_2024[0].cpu().numpy()

            mask_np = mask[0].cpu().numpy()

            probability_np = (
                probability[0]
                .cpu()
                .numpy()
            )

            prediction_np = (
                prediction[0]
                .cpu()
                .numpy()
            )

            # ------------------------------------------------
            # Determine sample name
            # ------------------------------------------------

            sample_name = f"test_{batch_idx + 1:03d}"

            if hasattr(test_dataset, "samples"):
                try:
                    sample_info = test_dataset.samples[batch_idx]

                    if isinstance(sample_info, (list, tuple)):
                        sample_name = os.path.splitext(
                            os.path.basename(
                                str(sample_info[0])
                            )
                        )[0]
                    else:
                        sample_name = os.path.splitext(
                            os.path.basename(
                                str(sample_info)
                            )
                        )[0]

                except Exception:
                    pass

            output_path = os.path.join(
                OUTPUT_DIR,
                f"{sample_name}.png"
            )

            save_prediction(
                img20_np,
                img24_np,
                mask_np,
                probability_np,
                prediction_np,
                sample_name,
                output_path
            )

            print(
                f"Saved {saved + 1}/{NUM_SAMPLES}: "
                f"{output_path}"
            )

            saved += 1

    print("\n" + "=" * 70)
    print("QUALITATIVE PREDICTIONS COMPLETE")
    print("=" * 70)

    print(f"Saved: {saved} images")
    print(f"Output folder: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()