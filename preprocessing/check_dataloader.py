import torch
from torch.utils.data import DataLoader

from dataset import UrbanEyeDataset


# ============================================================
# PATH
# ============================================================

DATA_ROOT = r"E:/UrbanEye/processed_data/patches"


# ============================================================
# DATASET
# ============================================================

train_dataset = UrbanEyeDataset(
    root_dir=DATA_ROOT,
    split="train",
    augment=True
)

val_dataset = UrbanEyeDataset(
    root_dir=DATA_ROOT,
    split="val",
    augment=False
)


# ============================================================
# DATALOADER
# ============================================================

train_loader = DataLoader(
    train_dataset,
    batch_size=8,
    shuffle=True,
    num_workers=0,
    pin_memory=True
)

val_loader = DataLoader(
    val_dataset,
    batch_size=8,
    shuffle=False,
    num_workers=0,
    pin_memory=True
)


# ============================================================
# CHECK TRAIN BATCH
# ============================================================

print("\nChecking training batch...")

image_2020, image_2024, masks = next(
    iter(train_loader)
)


print(
    "2020 shape:",
    image_2020.shape
)

print(
    "2024 shape:",
    image_2024.shape
)

print(
    "Mask shape:",
    masks.shape
)


print(
    "2020 dtype:",
    image_2020.dtype
)

print(
    "2024 dtype:",
    image_2024.dtype
)

print(
    "Mask dtype:",
    masks.dtype
)


print(
    "2020 min:",
    image_2020.min().item()
)

print(
    "2020 max:",
    image_2020.max().item()
)

print(
    "2024 min:",
    image_2024.min().item()
)

print(
    "2024 max:",
    image_2024.max().item()
)


print(
    "Mask unique values:",
    torch.unique(masks)
)


print(
    "Changed pixels in batch:",
    masks.sum().item()
)


# ============================================================
# CHECK VALIDATION BATCH
# ============================================================

print("\nChecking validation batch...")

val_2020, val_2024, val_masks = next(
    iter(val_loader)
)


print(
    "Validation 2020:",
    val_2020.shape
)

print(
    "Validation 2024:",
    val_2024.shape
)

print(
    "Validation masks:",
    val_masks.shape
)


print("\nDataLoader check complete.")