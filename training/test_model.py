import sys
sys.path.insert(0, r"E:/UrbanEye")

import torch
from torch.utils.data import DataLoader

from models.siamese_unet import SiameseUNet
from preprocessing.dataset import UrbanEyeDataset

# --------------------------------------------------
# Device
# --------------------------------------------------

device = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)

print("Device:", device)

if torch.cuda.is_available():
    print("GPU:", torch.cuda.get_device_name(0))


# --------------------------------------------------
# Dataset
# --------------------------------------------------

dataset = UrbanEyeDataset(
    root_dir=r"E:\UrbanEye\processed_data\patches",
    split="train",
    augment=False
)

loader = DataLoader(
    dataset,
    batch_size=8,
    shuffle=True,
    num_workers=0
)


# --------------------------------------------------
# Get one batch
# --------------------------------------------------

image_2020, image_2024, mask = next(iter(loader))

print("\nInput shapes:")
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
# Create model
# --------------------------------------------------

model = SiameseUNet(
    in_channels=3,
    out_channels=1
)

model = model.to(device)

print("\nModel created.")
print("Model device:", next(model.parameters()).device)


# --------------------------------------------------
# Forward pass
# --------------------------------------------------

model.eval()

with torch.no_grad():
    prediction = model(image_2020, image_2024)


# --------------------------------------------------
# Results
# --------------------------------------------------

print("\nOutput:")
print("Prediction shape:", prediction.shape)
print("Prediction device:", prediction.device)
print("Prediction dtype:", prediction.dtype)

print("\nExpected:")
print("Prediction shape: torch.Size([8, 1, 32, 32])")
print("Prediction device: cuda:0")

print("\nForward pass successful!")