import sys
sys.path.insert(0, r"E:\UrbanEye")

import torch
import torch.nn as nn
from torch.utils.data import DataLoader

from snunet_cd import SNUNetCD
from preprocessing.dataset import UrbanEyeDataset


# --------------------------------------------------
# Device
# --------------------------------------------------

device = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)

print("=" * 70)
print("TRAINING STEP TEST")
print("=" * 70)

print("Device:", device)

if torch.cuda.is_available():
    print("GPU:", torch.cuda.get_device_name(0))


# --------------------------------------------------
# Dice Loss
# --------------------------------------------------

def dice_loss(logits, targets, smooth=1.0):

    probabilities = torch.sigmoid(logits)

    probabilities = probabilities.contiguous().view(
        probabilities.size(0), -1
    )

    targets = targets.contiguous().view(
        targets.size(0), -1
    )

    intersection = (
        probabilities * targets
    ).sum(dim=1)

    dice = (
        (2.0 * intersection + smooth)
        /
        (
            probabilities.sum(dim=1)
            + targets.sum(dim=1)
            + smooth
        )
    )

    return 1.0 - dice.mean()


# --------------------------------------------------
# Dataset
# --------------------------------------------------

dataset = UrbanEyeDataset(
    root_dir=r"E:\UrbanEye\processed_data\patches",
    split="train",
    augment=True
)

loader = DataLoader(
    dataset,
    batch_size=8,
    shuffle=True,
    num_workers=0,
    pin_memory=torch.cuda.is_available()
)


# --------------------------------------------------
# Get batch
# --------------------------------------------------

image_2020, image_2024, mask = next(iter(loader))

print()
print("Input shapes:")
print("2020:", image_2020.shape)
print("2024:", image_2024.shape)
print("Mask:", mask.shape)


# --------------------------------------------------
# Move to GPU
# --------------------------------------------------

image_2020 = image_2020.to(device)
image_2024 = image_2024.to(device)
mask = mask.to(device)


# --------------------------------------------------
# Model
# --------------------------------------------------

model = SNUNetCD(
    in_channels=3,
    out_channels=1
).to(device)

print()
print("Model device:", next(model.parameters()).device)


# --------------------------------------------------
# Loss
# --------------------------------------------------

pos_weight = torch.tensor(
    [3.8203],
    device=device
)

bce_loss_function = nn.BCEWithLogitsLoss(
    pos_weight=pos_weight
)


# --------------------------------------------------
# Optimizer
# --------------------------------------------------

optimizer = torch.optim.AdamW(
    model.parameters(),
    lr=1e-4,
    weight_decay=1e-4
)


# --------------------------------------------------
# Forward pass
# --------------------------------------------------

model.train()

prediction = model(
    image_2020,
    image_2024
)

print()
print("Prediction shape:", prediction.shape)


# --------------------------------------------------
# Calculate losses
# --------------------------------------------------

bce = bce_loss_function(
    prediction,
    mask
)

dice = dice_loss(
    prediction,
    mask
)

total_loss = 0.5 * bce + 0.5 * dice


print()
print("Loss values:")
print(f"BCE Loss:   {bce.item():.6f}")
print(f"Dice Loss:  {dice.item():.6f}")
print(f"Total Loss: {total_loss.item():.6f}")


# --------------------------------------------------
# Backpropagation
# --------------------------------------------------

optimizer.zero_grad()

total_loss.backward()

print()
print("Backpropagation successful.")


# --------------------------------------------------
# Check gradients
# --------------------------------------------------

gradient_found = False

for name, parameter in model.named_parameters():

    if parameter.grad is not None:

        gradient_found = True

        print(
            f"Gradient found: {name} "
            f"| mean = {parameter.grad.abs().mean().item():.8f}"
        )

        break


if not gradient_found:
    raise RuntimeError(
        "No gradients were generated!"
    )


# --------------------------------------------------
# Optimizer step
# --------------------------------------------------

optimizer.step()

print()
print("Optimizer step successful.")

print()
print("=" * 70)
print("TRAINING STEP TEST PASSED")
print("=" * 70)