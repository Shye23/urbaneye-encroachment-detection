import os
import sys
import argparse

import torch
import numpy as np
from torch.utils.data import DataLoader

# ============================================================
# PROJECT PATH
# ============================================================

sys.path.insert(0, r"E:\UrbanEye")

from preprocessing.dataset import UrbanEyeDataset
from models.snunet_cd import SNUNetCD


# ============================================================
# SETTINGS
# ============================================================

DATA_ROOT = r"E:\UrbanEye\processed_data\patches"

DEFAULT_THRESHOLD = 0.60
BATCH_SIZE = 8


# ============================================================
# DEVICE
# ============================================================

device = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)

print("=" * 70)
print("UrbanEye - FINAL TEST SET EVALUATION")
print("=" * 70)

print("Device:", device)

if torch.cuda.is_available():
    print("GPU:", torch.cuda.get_device_name(0))
    print("CUDA:", torch.version.cuda)

print()


# ============================================================
# METRICS
# ============================================================

def calculate_metrics(tp, tn, fp, fn):

    accuracy = (
        tp + tn
    ) / max(
        tp + tn + fp + fn,
        1
    )

    precision = tp / max(
        tp + fp,
        1
    )

    recall = tp / max(
        tp + fn,
        1
    )

    f1 = (
        2 * precision * recall
    ) / max(
        precision + recall,
        1e-8
    )

    iou = tp / max(
        tp + fp + fn,
        1
    )

    dice = (
        2 * tp
    ) / max(
        2 * tp + fp + fn,
        1
    )

    return {
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "iou": iou,
        "dice": dice
    }


# ============================================================
# MAIN
# ============================================================

def evaluate(checkpoint_path):

    print("Checkpoint:")
    print(checkpoint_path)
    print()

    # --------------------------------------------------------
    # CHECK CHECKPOINT EXISTS
    # --------------------------------------------------------

    if not os.path.exists(checkpoint_path):

        raise FileNotFoundError(
            f"\nCheckpoint not found:\n"
            f"{checkpoint_path}"
        )

    # --------------------------------------------------------
    # LOAD CHECKPOINT
    # --------------------------------------------------------

    checkpoint = torch.load(
        checkpoint_path,
        map_location=device
    )

    print("Checkpoint information:")

    if "model_name" in checkpoint:
        print(
            "Model:",
            checkpoint["model_name"]
        )

    if "experiment" in checkpoint:
        print(
            "Experiment:",
            checkpoint["experiment"]
        )

    if "epoch" in checkpoint:
        print(
            "Best checkpoint epoch:",
            checkpoint["epoch"]
        )

    if "best_val_f1" in checkpoint:
        print(
            "Validation F1:",
            f"{checkpoint['best_val_f1']:.4f}"
        )

    if "best_val_iou" in checkpoint:
        print(
            "Validation IoU:",
            f"{checkpoint['best_val_iou']:.4f}"
        )

    if "parameters" in checkpoint:
        print(
            "Parameters:",
            f"{checkpoint['parameters']:,}"
        )

    print()

    # --------------------------------------------------------
    # THRESHOLD
    # --------------------------------------------------------

    threshold = checkpoint.get(
        "threshold",
        DEFAULT_THRESHOLD
    )

    print(
        f"Evaluation threshold: {threshold:.2f}"
    )

    print()

    # --------------------------------------------------------
    # TEST DATASET
    # --------------------------------------------------------

    test_dataset = UrbanEyeDataset(
        DATA_ROOT,
        split="test",
        augment=False
    )

    test_loader = DataLoader(
        test_dataset,
        batch_size=BATCH_SIZE,
        shuffle=False,
        num_workers=0,
        pin_memory=torch.cuda.is_available()
    )

    print(
        "Test samples:",
        len(test_dataset)
    )

    print()

    # --------------------------------------------------------
    # CREATE MODEL
    # --------------------------------------------------------

    model = SNUNetCD(
        in_channels=3,
        out_channels=1
    )

    model.load_state_dict(
        checkpoint["model_state_dict"]
    )

    model = model.to(device)

    model.eval()

    print(
        "SNUNet-CD loaded successfully."
    )

    print(
        "Model device:",
        next(model.parameters()).device
    )

    print()

    # --------------------------------------------------------
    # TEST INFERENCE
    # --------------------------------------------------------

    total_tp = 0
    total_tn = 0
    total_fp = 0
    total_fn = 0

    print(
        "Running inference on TEST SET..."
    )

    with torch.no_grad():

        for image_2020, image_2024, masks in test_loader:

            image_2020 = image_2020.to(
                device,
                non_blocking=True
            )

            image_2024 = image_2024.to(
                device,
                non_blocking=True
            )

            masks = masks.to(
                device,
                non_blocking=True
            )

            # Model prediction
            outputs = model(
                image_2020,
                image_2024
            )

            probabilities = torch.sigmoid(
                outputs
            )

            predictions = (
                probabilities >= threshold
            ).float()

            # Flatten
            predictions = predictions.view(-1)
            targets = masks.view(-1)

            # Confusion matrix components
            total_tp += (
                (predictions == 1)
                & (targets == 1)
            ).sum().item()

            total_tn += (
                (predictions == 0)
                & (targets == 0)
            ).sum().item()

            total_fp += (
                (predictions == 1)
                & (targets == 0)
            ).sum().item()

            total_fn += (
                (predictions == 0)
                & (targets == 1)
            ).sum().item()

    # --------------------------------------------------------
    # CALCULATE FINAL METRICS
    # --------------------------------------------------------

    metrics = calculate_metrics(
        total_tp,
        total_tn,
        total_fp,
        total_fn
    )

    # ========================================================
    # FINAL RESULTS
    # ========================================================

    print()
    print("=" * 70)
    print("FINAL TEST SET RESULTS")
    print("=" * 70)

    print(
        f"Accuracy  : {metrics['accuracy']:.4f}"
    )

    print(
        f"Precision : {metrics['precision']:.4f}"
    )

    print(
        f"Recall    : {metrics['recall']:.4f}"
    )

    print(
        f"F1 Score  : {metrics['f1']:.4f}"
    )

    print(
        f"IoU       : {metrics['iou']:.4f}"
    )

    print(
        f"Dice      : {metrics['dice']:.4f}"
    )

    print()

    print("Confusion Matrix:")
    print(
        f"True Positive  (TP): {total_tp:,}"
    )

    print(
        f"True Negative  (TN): {total_tn:,}"
    )

    print(
        f"False Positive (FP): {total_fp:,}"
    )

    print(
        f"False Negative (FN): {total_fn:,}"
    )

    print()

    print(
        f"Threshold: {threshold:.2f}"
    )

    print("=" * 70)

    # --------------------------------------------------------
    # SAVE RESULTS
    # --------------------------------------------------------

    results_file = os.path.join(
        os.path.dirname(checkpoint_path),
        "final_test_results.txt"
    )

    with open(
        results_file,
        "w"
    ) as f:

        f.write(
            "UrbanEye Final Test Set Results\n"
        )

        f.write(
            "====================================\n"
        )

        f.write(
            f"Model: SNUNet-CD\n"
        )

        f.write(
            f"Checkpoint: {checkpoint_path}\n"
        )

        f.write(
            f"Best Epoch: "
            f"{checkpoint.get('epoch', 'N/A')}\n"
        )

        f.write(
            f"Threshold: {threshold:.2f}\n"
        )

        f.write(
            f"Parameters: "
            f"{checkpoint.get('parameters', 'N/A')}\n"
        )

        f.write(
            f"Accuracy: "
            f"{metrics['accuracy']:.4f}\n"
        )

        f.write(
            f"Precision: "
            f"{metrics['precision']:.4f}\n"
        )

        f.write(
            f"Recall: "
            f"{metrics['recall']:.4f}\n"
        )

        f.write(
            f"F1 Score: "
            f"{metrics['f1']:.4f}\n"
        )

        f.write(
            f"IoU: "
            f"{metrics['iou']:.4f}\n"
        )

        f.write(
            f"Dice: "
            f"{metrics['dice']:.4f}\n"
        )

        f.write("\n")

        f.write(
            f"TP: {total_tp}\n"
        )

        f.write(
            f"TN: {total_tn}\n"
        )

        f.write(
            f"FP: {total_fp}\n"
        )

        f.write(
            f"FN: {total_fn}\n"
        )

    print()
    print(
        "Results saved to:"
    )

    print(
        results_file
    )

    print()


# ============================================================
# COMMAND LINE
# ============================================================

if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Final UrbanEye test-set evaluation"
    )

    parser.add_argument(
        "--checkpoint",
        type=str,
        required=True,
        help="Path to final best_model.pth"
    )

    args = parser.parse_args()

    evaluate(
        args.checkpoint
    )