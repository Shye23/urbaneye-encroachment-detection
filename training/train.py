import os
import sys
import time
import csv
import argparse

import torch
import torch.nn as nn
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
CHECKPOINT_ROOT = r"E:\UrbanEye\training\checkpoints\snunet"

BATCH_SIZE = 8

MAX_EPOCHS = 40
EARLY_STOPPING_PATIENCE = 8

LEARNING_RATE = 5e-4
WEIGHT_DECAY = 1e-4

POS_WEIGHT = 3.8203

LR_PATIENCE = 3
LR_FACTOR = 0.5
MIN_LR = 1e-6

THRESHOLD = 0.6


# ============================================================
# DEVICE
# ============================================================

device = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)

print("=" * 65)
print("UrbanEye - SNUNet-CD Training")
print("=" * 65)

print("Device:", device)

if torch.cuda.is_available():
    print("GPU:", torch.cuda.get_device_name(0))
    print("CUDA:", torch.version.cuda)

print()


# ============================================================
# DICE LOSS
# ============================================================

class DiceLoss(nn.Module):

    def __init__(self, smooth=1.0):
        super().__init__()
        self.smooth = smooth

    def forward(self, logits, targets):

        probabilities = torch.sigmoid(logits)

        probabilities = probabilities.view(-1)
        targets = targets.view(-1)

        intersection = (
            probabilities * targets
        ).sum()

        dice = (
            2.0 * intersection + self.smooth
        ) / (
            probabilities.sum()
            + targets.sum()
            + self.smooth
        )

        return 1.0 - dice


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

        loss = (
            0.25 * bce
            + 0.75 * dice
        )

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

            loss = (
                0.5 * bce
                + 0.5 * dice
            )

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
# TRAINING
# ============================================================

def train_model(
    learning_rate=LEARNING_RATE,
    batch_size=BATCH_SIZE,
    experiment_name="baseline"
):

    print("=" * 65)
    print("EXPERIMENT:", experiment_name)
    print("=" * 65)

    print("Learning Rate:", learning_rate)
    print("Batch Size:", batch_size)
    print("Maximum Epochs:", MAX_EPOCHS)
    print("Weight Decay:", WEIGHT_DECAY)
    print("Positive Weight:", POS_WEIGHT)
    print("Threshold:", THRESHOLD)
    print()

    # --------------------------------------------------------
    # DATASETS
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
    # DATALOADERS
    # --------------------------------------------------------

    pin_memory = torch.cuda.is_available()

    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=0,
        pin_memory=pin_memory
    )

    val_loader = DataLoader(
        val_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=0,
        pin_memory=pin_memory
    )

    test_loader = DataLoader(
        test_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=0,
        pin_memory=pin_memory
    )

    print("Dataset sizes:")
    print("Train:", len(train_dataset))
    print("Validation:", len(val_dataset))
    print("Test:", len(test_dataset))
    print()

    # --------------------------------------------------------
    # MODEL
    # --------------------------------------------------------

    model = SNUNetCD(
        in_channels=3,
        out_channels=1
    )

    model = model.to(device)

    trainable_parameters = count_parameters(model)

    print(
        f"Trainable Parameters: "
        f"{trainable_parameters:,}"
    )

    print(
        f"Trainable Parameters: "
        f"{trainable_parameters / 1e6:.3f} M"
    )

    print()

    # --------------------------------------------------------
    # LOSS
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
    # OPTIMIZER
    # --------------------------------------------------------

    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=learning_rate,
        weight_decay=WEIGHT_DECAY
    )

    # --------------------------------------------------------
    # LR SCHEDULER
    # --------------------------------------------------------

    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer,
        mode="max",
        factor=LR_FACTOR,
        patience=LR_PATIENCE,
        min_lr=MIN_LR
    )

    # --------------------------------------------------------
    # EXPERIMENT DIRECTORY
    # --------------------------------------------------------

    experiment_dir = os.path.join(
        CHECKPOINT_ROOT,
        experiment_name
    )

    os.makedirs(
        experiment_dir,
        exist_ok=True
    )

    best_checkpoint = os.path.join(
        experiment_dir,
        "best_model.pth"
    )

    last_checkpoint = os.path.join(
        experiment_dir,
        "last_model.pth"
    )

    history_file = os.path.join(
        experiment_dir,
        "training_history.csv"
    )

    # --------------------------------------------------------
    # TRAINING VARIABLES
    # --------------------------------------------------------

    best_f1 = -1.0
    best_epoch = 0

    epochs_without_improvement = 0

    history = []

    training_start = time.time()

    # ========================================================
    # EPOCH LOOP
    # ========================================================

    for epoch in range(
        1,
        MAX_EPOCHS + 1
    ):

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

        epoch_time = (
            time.time()
            - epoch_start
        )

        # ----------------------------------------------------
        # PRINT
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
        # HISTORY
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
        # BEST MODEL
        # ----------------------------------------------------

        if val_metrics["f1"] > best_f1:

            best_f1 = val_metrics["f1"]
            best_epoch = epoch

            epochs_without_improvement = 0

            torch.save(
                {
                    "model_name": "SNUNet-CD",
                    "experiment": experiment_name,
                    "epoch": epoch,
                    "model_state_dict": model.state_dict(),
                    "optimizer_state_dict": optimizer.state_dict(),
                    "best_val_f1": best_f1,
                    "best_val_iou": val_metrics["iou"],
                    "best_val_precision": val_metrics["precision"],
                    "best_val_recall": val_metrics["recall"],
                    "best_val_accuracy": val_metrics["accuracy"],
                    "parameters": trainable_parameters,
                    "learning_rate": learning_rate,
                    "batch_size": batch_size,
                    "weight_decay": WEIGHT_DECAY,
                    "pos_weight": POS_WEIGHT,
                    "threshold": THRESHOLD
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
        # LR SCHEDULER
        # ----------------------------------------------------

        scheduler.step(
            val_metrics["f1"]
        )

        # ----------------------------------------------------
        # EARLY STOPPING
        # ----------------------------------------------------

        if (
            epochs_without_improvement
            >= EARLY_STOPPING_PATIENCE
        ):

            print()
            print(
                "Early stopping triggered."
            )

            break

    # ========================================================
    # TRAINING COMPLETE
    # ========================================================

    total_training_time = (
        time.time()
        - training_start
    )

    # --------------------------------------------------------
    # SAVE LAST MODEL
    # --------------------------------------------------------

    torch.save(
        {
            "model_name": "SNUNet-CD",
            "experiment": experiment_name,
            "epoch": epoch,
            "model_state_dict": model.state_dict(),
            "optimizer_state_dict": optimizer.state_dict(),
            "parameters": trainable_parameters,
            "learning_rate": learning_rate,
            "batch_size": batch_size,
            "weight_decay": WEIGHT_DECAY,
            "pos_weight": POS_WEIGHT,
            "threshold": THRESHOLD
        },
        last_checkpoint
    )

    # --------------------------------------------------------
    # SAVE HISTORY
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
    # BEST RESULT
    # --------------------------------------------------------

    best_result = max(
        history,
        key=lambda x: x["val_f1"]
    )

    # ========================================================
    # FINAL SUMMARY
    # ========================================================

    print()
    print("=" * 65)
    print("SNUNET-CD TRAINING COMPLETE")
    print("=" * 65)

    print(
        f"Experiment: {experiment_name}"
    )

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
        f"Training Time: "
        f"{total_training_time / 60:.2f} minutes"
    )

    print()
    print(
        "Best checkpoint:",
        best_checkpoint
    )

    print(
        "Training history:",
        history_file
    )

    print("=" * 65)


# ============================================================
# COMMAND LINE
# ============================================================

if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Train SNUNet-CD for UrbanEye"
    )

    parser.add_argument(
        "--lr",
        type=float,
        default=LEARNING_RATE,
        help="Learning rate"
    )

    parser.add_argument(
        "--batch-size",
        type=int,
        default=BATCH_SIZE,
        help="Training batch size"
    )

    parser.add_argument(
        "--experiment",
        type=str,
        default="baseline",
        help="Experiment name"
    )

    args = parser.parse_args()

    train_model(
        learning_rate=args.lr,
        batch_size=args.batch_size,
        experiment_name=args.experiment
    )