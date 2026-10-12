from pathlib import Path

import numpy as np
import torch
import rasterio

from models.snunet_cd import SNUNetCD

from inference.dynamic_patches import (
    create_patches,
    normalize_image,
    pad_to_patch_size
)


class UrbanEyeInference:

    def __init__(
        self,
        checkpoint_path,
        device=None,
        threshold=0.60
    ):

        self.checkpoint_path = Path(checkpoint_path)
        self.threshold = threshold

        if device is None:
            device = (
                "cuda"
                if torch.cuda.is_available()
                else "cpu"
            )

        self.device = torch.device(device)

        print(f"Device: {self.device}")

        if self.device.type == "cuda":
            print(
                f"GPU: "
                f"{torch.cuda.get_device_name(0)}"
            )

        self.model = SNUNetCD(
            in_channels=3,
            out_channels=1
        )

        checkpoint = torch.load(
            self.checkpoint_path,
            map_location=self.device
        )

        if "model_state_dict" in checkpoint:
            state_dict = checkpoint[
                "model_state_dict"
            ]
        elif "state_dict" in checkpoint:
            state_dict = checkpoint[
                "state_dict"
            ]
        else:
            state_dict = checkpoint

        self.model.load_state_dict(
            state_dict
        )

        self.model.to(self.device)
        self.model.eval()

        print(
            f"Loaded checkpoint: "
            f"{self.checkpoint_path}"
        )

    def read_image(self, path):

        with rasterio.open(path) as src:

            image = src.read()

            profile = src.profile.copy()

            transform = src.transform

            crs = src.crs

        return (
            image,
            profile,
            transform,
            crs
        )

    def validate_images(
        self,
        image_2020,
        image_2024,
        crs_2020,
        crs_2024,
        transform_2020,
        transform_2024
    ):

        if image_2020.shape != image_2024.shape:
            raise ValueError(
                "2020 and 2024 image dimensions "
                "do not match."
            )

        if crs_2020 != crs_2024:
            raise ValueError(
                f"CRS mismatch: "
                f"{crs_2020} vs {crs_2024}"
            )

        if transform_2020 != transform_2024:
            raise ValueError(
                "Image transforms are not identical. "
                "Images must be spatially aligned "
                "before SNUNet inference."
            )

        if image_2020.shape[0] != 3:
            raise ValueError(
                f"Expected 3 channels, "
                f"got {image_2020.shape[0]}"
            )

    @torch.no_grad()
    def predict(
        self,
        image_2020_path,
        image_2024_path
    ):

        (
            image_2020,
            profile,
            transform,
            crs
        ) = self.read_image(
            image_2020_path
        )

        (
            image_2024,
            profile_2024,
            transform_2024,
            crs_2024
        ) = self.read_image(
            image_2024_path
        )

        self.validate_images(
            image_2020,
            image_2024,
            crs,
            crs_2024,
            transform,
            transform_2024
        )

        print(
            f"Input shape: "
            f"{image_2020.shape}"
        )

        image_2020 = normalize_image(
            image_2020
        )

        image_2024 = normalize_image(
            image_2024
        )

        (
            padded_2020,
            padded_2024,
            original_height,
            original_width
        ) = pad_to_patch_size(
            image_2020,
            image_2024,
            patch_size=32
        )

        patches = create_patches(
            padded_2020,
            padded_2024,
            patch_size=32,
            stride=16
        )

        print(
            f"Generated patches: "
            f"{len(patches)}"
        )

        height = padded_2020.shape[1]
        width = padded_2020.shape[2]

        probability_sum = np.zeros(
            (height, width),
            dtype=np.float32
        )

        probability_count = np.zeros(
            (height, width),
            dtype=np.float32
        )

        batch_size = 8

        for start in range(
            0,
            len(patches),
            batch_size
        ):

            batch = patches[
                start:start + batch_size
            ]

            x2020 = np.stack(
                [item[0] for item in batch]
            )

            x2024 = np.stack(
                [item[1] for item in batch]
            )

            ys = [
                item[2]
                for item in batch
            ]

            xs = [
                item[3]
                for item in batch
            ]

            x2020 = torch.from_numpy(
                x2020
            ).float().to(self.device)

            x2024 = torch.from_numpy(
                x2024
            ).float().to(self.device)

            logits = self.model(
                x2020,
                x2024
            )

            probabilities = torch.sigmoid(
                logits
            )

            probabilities = (
                probabilities
                .cpu()
                .numpy()
            )

            for i in range(
                len(batch)
            ):

                y = ys[i]
                x = xs[i]

                probability = (
                    probabilities[i, 0]
                )

                probability_sum[
                    y:y + 32,
                    x:x + 32
                ] += probability

                probability_count[
                    y:y + 32,
                    x:x + 32
                ] += 1

        probability_map = (
            probability_sum /
            np.maximum(
                probability_count,
                1
            )
        )

        probability_map = probability_map[
            :original_height,
            :original_width
        ]

        prediction = (
            probability_map >= self.threshold
        ).astype(np.uint8)

        return {
            "probability": probability_map,
            "prediction": prediction,
            "crs": crs,
            "transform": transform,
            "profile": profile
        }