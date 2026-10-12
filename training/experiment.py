import os
import sys
import time
import csv
import argparse

import torch
import torch.nn as nn
from torch.utils.data import DataLoader

# Add project root to Python path
sys.path.insert(0, r"E:\UrbanEye")

from preprocessing.dataset import UrbanEyeDataset

from models.unet import UNet
from models.siamese_unet import SiameseUNet
from models.unet_plus_plus import UNetPlusPlus
from models.snunet_cd import SNUNetCD


# ============================================================
# SETTINGS
# ============================================================

DATA_ROOT = r"E:\UrbanEye\processed_data\patches"
CHECKPOINT_ROOT = r"E:\UrbanEye\training\checkpoints"

BATCH_SIZE = 8
MAX_EPOCHS = 15

LEARNING_RATE = 1e-4
WEIGHT_DECAY = 1e-4

POS_WEIGHT = 3.8203

EARLY_STOPPING_PATIENCE = 8

LR_PATIENCE = 3
LR_FACTOR = 0.5
MIN_LR = 1e-6

THRESHOLD = 0.5


# ============================================================
# DEVICE
# ============================================================

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

print("=" * 60)
print("UrbanEye Multi-Model Training")
print("=" * 60)

print("Device:", device)

if torch.cuda.is_available():
    print("GPU:", torch.cuda.get_device_name(0))
    print("CUDA:", torch.version.cuda)

print()


# ============================================================
# MODEL CREATION
# ============================================================

def create_model(model_name):

    if model_name == "unet":
        model = UNet(
            in_channels=6,
            out_channels=1
        )

    elif model_name == "siamese":
        model = SiameseUNet(
            in_channels=3,
            out_channels=1
        )

    elif model_name == "unetpp":
        model = UNetPlusPlus(
            in_channels=6,
            out_channels=1
        )

    elif model_name == "snunet":
        model = SNUNetCD(
            in_channels=3,
            out_channels=1
        )

    else:
        raise ValueError(
            f"Unknown model: {model_name}"
        )

    return model


# ============================================================
# PARAMETER COUNT
# ============================================================

def count_parameters(model):

    return sum(
        p.numel()
        for p in model.parameters()
        if p.requires_grad
    )


# ============================================================
# LOSS FUNCTIONS
# ============================================================

class DiceLoss(nn.Module):

    def __init__(self, smooth=1.0):
        super().__init__()
        self.smooth = smooth

    def forward(self, logits, targets):

        probabilities = torch.sigmoid(logits)

        probabilities = probabilities.view(-1)
        targets = targets.view(-1)

        intersection = (probabilities * targets).sum()

        dice = (
            2.0 * intersection + self.smooth
        ) / (
            probabilities.sum()
            + targets.sum()
            + self.smooth
        )

        return 1.0 - dice


# ============================================================
# METRICS
# ============================================================

def calculate_metrics(logits, targets):

    probabilities = torch.sigmoid(logits)

    predictions = (
        probabilities >= THRESHOLD
    ).float()

    targets = targets.float()

    predictions = predictions.view(-1)
    targets = targets.view(-1)

    true_positive = (
        (predictions == 1)
        & (targets == 1)
    ).sum().item()

    true_negative = (
        (predictions == 0)
        & (targets == 0)
    ).sum().item()

    false_positive = (
        (predictions == 1)
        & (targets == 0)
    ).sum().item()

    false_negative = (
        (predictions == 0)
        & (targets == 1)
    ).sum().item()

    accuracy = (
        true_positive + true_negative
    ) / max(
        true_positive
        + true_negative
        + false_positive
        + false_negative,
        1
    )

    precision = true_positive / max(
        true_positive + false_positive,
        1
    )

    recall = true_positive / max(
        true_positive + false_negative,
        1
    )

    f1 = (
        2 * precision * recall
    ) / max(
        precision + recall,
        1e-8
    )

    iou = true_positive / max(
        true_positive
        + false_positive
        + false_negative,
        1
    )

    return {
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "iou": iou
    }


# ============================================================
# TRAIN ONE EPOCH
# ============================================================

def train_one_epoch(
    model,
    loader,
    optimizer,
    bce_loss,
    dice_loss
):

    model.train()

    total_loss = 0.0
    total_bce = 0.0
    total_dice = 0.0

    for image_2020, image_2024, masks in loader:

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

        optimizer.zero_grad()

        outputs = model(
            image_2020,
            image_2024
        )

        bce = bce_loss(
            outputs,
            masks
        )

        dice = dice_loss(
            outputs,
            masks
        )

        loss = 0.5 * bce + 0.5 * dice

        loss.backward()

        optimizer.step()

        total_loss += loss.item()
        total_bce += bce.item()
        total_dice += dice.item()

    num_batches = len(loader)

    return (
        total_loss / num_batches,
        total_bce / num_batches,
        total_dice / num_batches
    )


# ============================================================
# VALIDATION
# ============================================================

def validate(
    model,
    loader,
    bce_loss,
    dice_loss
):

    model.eval()

    total_loss = 0.0
    total_bce = 0.0
    total_dice = 0.0

    total_tp = 0
    total_tn = 0
    total_fp = 0
    total_fn = 0

    with torch.no_grad():

        for image_2020, image_2024, masks in loader:

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

            outputs = model(
                image_2020,
                image_2024
            )

            bce = bce_loss(
                outputs,
                masks
            )

            dice = dice_loss(
                outputs,
                masks
            )

            loss = 0.5 * bce + 0.5 * dice

            total_loss += loss.item()
            total_bce += bce.item()
            total_dice += dice.item()

            probabilities = torch.sigmoid(outputs)

            predictions = (
                probabilities >= THRESHOLD
            ).float()

            predictions = predictions.view(-1)
            targets = masks.view(-1)

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

    accuracy = (
        total_tp + total_tn
    ) / max(
        total_tp
        + total_tn
        + total_fp
        + total_fn,
        1
    )

    precision = total_tp / max(
        total_tp + total_fp,
        1
    )

    recall = total_tp / max(
        total_tp + total_fn,
        1
    )

    f1 = (
        2 * precision * recall
    ) / max(
        precision + recall,
        1e-8
    )

    iou = total_tp / max(
        total_tp
        + total_fp
        + total_fn,
        1
    )

    num_batches = len(loader)

    return {
        "loss": total_loss / num_batches,
        "bce": total_bce / num_batches,
        "dice": total_dice / num_batches,
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "iou": iou
    }


# ============================================================
# MAIN TRAINING FUNCTION
# ============================================================

def train_model(model_name):

    print("=" * 60)
    print(f"MODEL: {model_name.upper()}")
    print("=" * 60)

    # --------------------------------------------------------
    # Create datasets
    # --------------------------------------------------------

    train_dataset = UrbanEyeDataset(
        DATA_ROOT,
        split="train",
        augment=True
    )

    val_dataset = UrbanEyeDataset(
        DATA_ROOT,
        split="val",
        augment=False
    )

    test_dataset = UrbanEyeDataset(
        DATA_ROOT,
        split="test",
        augment=False
    )

    # --------------------------------------------------------
    # DataLoaders
    # --------------------------------------------------------

    pin_memory = torch.cuda.is_available()

    train_loader = DataLoader(
        train_dataset,
        batch_size=BATCH_SIZE,
        shuffle=True,
        num_workers=0,
        pin_memory=pin_memory
    )

    val_loader = DataLoader(
        val_dataset,
        batch_size=BATCH_SIZE,
        shuffle=False,
        num_workers=0,
        pin_memory=pin_memory
    )

    test_loader = DataLoader(
        test_dataset,
        batch_size=BATCH_SIZE,
        shuffle=False,
        num_workers=0,
        pin_memory=pin_memory
    )

    print()
    print("Dataset sizes:")
    print("Train:", len(train_dataset))
    print("Validation:", len(val_dataset))
    print("Test:", len(test_dataset))
    print()

    # --------------------------------------------------------
    # Create model
    # --------------------------------------------------------

    model = create_model(model_name)

    model = model.to(device)

    trainable_parameters = count_parameters(model)

    print(
        f"Trainable parameters: "
        f"{trainable_parameters:,}"
    )

    print(
        f"Trainable parameters: "
        f"{trainable_parameters / 1e6:.3f} M"
    )

    print()

    # --------------------------------------------------------
    # Loss
    # --------------------------------------------------------

    pos_weight = torch.tensor(
        [POS_WEIGHT],
        device=device
    )

    bce_loss = nn.BCEWithLogitsLoss(
        pos_weight=pos_weight
    )

    dice_loss = DiceLoss()

    # --------------------------------------------------------
    # Optimizer
    # --------------------------------------------------------

    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=LEARNING_RATE,
        weight_decay=WEIGHT_DECAY
    )

    # --------------------------------------------------------
    # Learning rate scheduler
    # --------------------------------------------------------

    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer,
        mode="max",
        factor=LR_FACTOR,
        patience=LR_PATIENCE,
        min_lr=MIN_LR
    )

    # --------------------------------------------------------
    # Checkpoint directory
    # --------------------------------------------------------

    model_checkpoint_dir = os.path.join(
        CHECKPOINT_ROOT,
        model_name
    )

    os.makedirs(
        model_checkpoint_dir,
        exist_ok=True
    )

    best_checkpoint = os.path.join(
        model_checkpoint_dir,
        "best_model.pth"
    )

    last_checkpoint = os.path.join(
        model_checkpoint_dir,
        "last_model.pth"
    )

    history_file = os.path.join(
        model_checkpoint_dir,
        "training_history.csv"
    )

    # --------------------------------------------------------
    # Training variables
    # --------------------------------------------------------

    best_f1 = -1.0
    best_epoch = 0

    epochs_without_improvement = 0

    history = []

    training_start = time.time()

    # ========================================================
    # EPOCH LOOP
    # ========================================================

    for epoch in range(1, MAX_EPOCHS + 1):

        epoch_start = time.time()

        train_loss, train_bce, train_dice = train_one_epoch(
            model,
            train_loader,
            optimizer,
            bce_loss,
            dice_loss
        )

        val_metrics = validate(
            model,
            val_loader,
            bce_loss,
            dice_loss
        )

        current_lr = optimizer.param_groups[0]["lr"]

        epoch_time = time.time() - epoch_start

        # ----------------------------------------------------
        # Print results
        # ----------------------------------------------------

        print()
        print(
            f"Epoch {epoch}/{MAX_EPOCHS}"
        )

        print(
            f"Train Loss: {train_loss:.6f}"
        )

        print(
            f"Train BCE: {train_bce:.6f}"
        )

        print(
            f"Train Dice: {train_dice:.6f}"
        )

        print(
            f"Val Loss: {val_metrics['loss']:.6f}"
        )

        print(
            f"Val Accuracy: "
            f"{val_metrics['accuracy']:.4f}"
        )

        print(
            f"Val Precision: "
            f"{val_metrics['precision']:.4f}"
        )

        print(
            f"Val Recall: "
            f"{val_metrics['recall']:.4f}"
        )

        print(
            f"Val F1: "
            f"{val_metrics['f1']:.4f}"
        )

        print(
            f"Val IoU: "
            f"{val_metrics['iou']:.4f}"
        )

        print(
            f"Learning Rate: "
            f"{current_lr:.6f}"
        )

        print(
            f"Epoch Time: "
            f"{epoch_time:.2f} sec"
        )

        # ----------------------------------------------------
        # Save history
        # ----------------------------------------------------

        history.append({
            "epoch": epoch,
            "train_loss": train_loss,
            "train_bce": train_bce,
            "train_dice": train_dice,
            "val_loss": val_metrics["loss"],
            "val_accuracy": val_metrics["accuracy"],
            "val_precision": val_metrics["precision"],
            "val_recall": val_metrics["recall"],
            "val_f1": val_metrics["f1"],
            "val_iou": val_metrics["iou"],
            "learning_rate": current_lr,
            "epoch_time_sec": epoch_time
        })

        # ----------------------------------------------------
        # Best model
        # ----------------------------------------------------

        if val_metrics["f1"] > best_f1:

            best_f1 = val_metrics["f1"]
            best_epoch = epoch

            epochs_without_improvement = 0

            torch.save(
                {
                    "model_name": model_name,
                    "epoch": epoch,
                    "model_state_dict": model.state_dict(),
                    "optimizer_state_dict": optimizer.state_dict(),
                    "best_val_f1": best_f1,
                    "best_val_iou": val_metrics["iou"],
                    "parameters": trainable_parameters
                },
                best_checkpoint
            )

            print(
                f"Best model saved! "
                f"Val F1 = {best_f1:.4f}"
            )

        else:

            epochs_without_improvement += 1

        # ----------------------------------------------------
        # Learning rate scheduler
        # ----------------------------------------------------

        scheduler.step(
            val_metrics["f1"]
        )

        # ----------------------------------------------------
        # Early stopping
        # ----------------------------------------------------

        if epochs_without_improvement >= EARLY_STOPPING_PATIENCE:

            print()
            print(
                "Early stopping triggered."
            )

            break

    # ========================================================
    # TRAINING COMPLETE
    # ========================================================

    total_training_time = (
        time.time() - training_start
    )

    # --------------------------------------------------------
    # Save last model
    # --------------------------------------------------------

    torch.save(
        {
            "model_name": model_name,
            "epoch": epoch,
            "model_state_dict": model.state_dict(),
            "optimizer_state_dict": optimizer.state_dict(),
            "parameters": trainable_parameters
        },
        last_checkpoint
    )

    # --------------------------------------------------------
    # Save history CSV
    # --------------------------------------------------------

    with open(
        history_file,
        "w",
        newline=""
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=history[0].keys()
        )

        writer.writeheader()
        writer.writerows(history)

    # --------------------------------------------------------
    # Find best metrics
    # --------------------------------------------------------

    best_result = max(
        history,
        key=lambda x: x["val_f1"]
    )

    # ========================================================
    # FINAL SUMMARY
    # ========================================================

    print()
    print("=" * 60)
    print(f"{model_name.upper()} TRAINING COMPLETE")
    print("=" * 60)

    print(
        f"Best Epoch: "
        f"{best_result['epoch']}"
    )

    print(
        f"Best Val F1: "
        f"{best_result['val_f1']:.4f}"
    )

    print(
        f"Best Val IoU: "
        f"{best_result['val_iou']:.4f}"
    )

    print(
        f"Precision: "
        f"{best_result['val_precision']:.4f}"
    )

    print(
        f"Recall: "
        f"{best_result['val_recall']:.4f}"
    )

    print(
        f"Accuracy: "
        f"{best_result['val_accuracy']:.4f}"
    )

    print(
        f"Parameters: "
        f"{trainable_parameters:,}"
    )

    print(
        f"Parameters: "
        f"{trainable_parameters / 1e6:.3f} M"
    )

    print(
        f"Total Training Time: "
        f"{total_training_time / 60:.2f} minutes"
    )

    print()
    print(
        "Best checkpoint:",
        best_checkpoint
    )

    print(
        "History:",
        history_file
    )

    print("=" * 60)


# ============================================================
# COMMAND LINE
# ============================================================

if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Train UrbanEye change detection models"
    )

    parser.add_argument(
        "--model",
        type=str,
        required=True,
        choices=[
            "unet",
            "siamese",
            "unetpp",
            "snunet"
        ],
        help="Model to train"
    )

    args = parser.parse_args()

    train_model(args.model)