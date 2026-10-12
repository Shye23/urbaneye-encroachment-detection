import os
import glob
import numpy as np
import rasterio

import torch
from torch.utils.data import Dataset


class UrbanEyeDataset(Dataset):

    def __init__(self, root_dir, split="train", augment=False):

        self.root_dir = root_dir
        self.split = split
        self.augment = augment and split == "train"

        self.dir_2020 = os.path.join(
            root_dir,
            split,
            "2020"
        )

        self.dir_2024 = os.path.join(
            root_dir,
            split,
            "2024"
        )

        self.dir_masks = os.path.join(
            root_dir,
            split,
            "masks"
        )

        self.files_2020 = sorted(
            glob.glob(
                os.path.join(
                    self.dir_2020,
                    "*.tif"
                )
            )
        )

        if len(self.files_2020) == 0:
            raise ValueError(
                f"No patches found in {self.dir_2020}"
            )

        # ----------------------------------------------------
        # Verify corresponding files exist
        # ----------------------------------------------------

        self.samples = []

        for path_2020 in self.files_2020:

            filename = os.path.basename(path_2020)

            path_2024 = os.path.join(
                self.dir_2024,
                filename
            )

            path_mask = os.path.join(
                self.dir_masks,
                filename
            )

            if not os.path.exists(path_2024):
                raise FileNotFoundError(
                    f"Missing 2024 patch:\n{path_2024}"
                )

            if not os.path.exists(path_mask):
                raise FileNotFoundError(
                    f"Missing mask patch:\n{path_mask}"
                )

            self.samples.append(
                (
                    path_2020,
                    path_2024,
                    path_mask
                )
            )

        print(
            f"{split.upper()} dataset: "
            f"{len(self.samples)} samples"
        )


    def __len__(self):

        return len(self.samples)


    # ========================================================
    # LOAD TIFF
    # ========================================================

    def read_tiff(self, path):

        with rasterio.open(path) as src:

            image = src.read()

        return image


    # ========================================================
    # SYNCHRONIZED AUGMENTATION
    # ========================================================

    def apply_augmentation(
        self,
        image_2020,
        image_2024,
        mask
    ):

        # ----------------------------------------------------
        # Horizontal flip
        # ----------------------------------------------------

        if np.random.rand() < 0.5:

            image_2020 = np.flip(
                image_2020,
                axis=2
            )

            image_2024 = np.flip(
                image_2024,
                axis=2
            )

            mask = np.flip(
                mask,
                axis=1
            )


        # ----------------------------------------------------
        # Vertical flip
        # ----------------------------------------------------

        if np.random.rand() < 0.5:

            image_2020 = np.flip(
                image_2020,
                axis=1
            )

            image_2024 = np.flip(
                image_2024,
                axis=1
            )

            mask = np.flip(
                mask,
                axis=0
            )


        # ----------------------------------------------------
        # Random 90 degree rotation
        # ----------------------------------------------------

        k = np.random.randint(
            0,
            4
        )

        if k > 0:

            image_2020 = np.rot90(
                image_2020,
                k=k,
                axes=(1, 2)
            )

            image_2024 = np.rot90(
                image_2024,
                k=k,
                axes=(1, 2)
            )

            mask = np.rot90(
                mask,
                k=k,
                axes=(0, 1)
            )


        # ----------------------------------------------------
        # np.flip / rot90 can create negative strides.
        # Convert back to contiguous arrays.
        # ----------------------------------------------------

        image_2020 = np.ascontiguousarray(
            image_2020
        )

        image_2024 = np.ascontiguousarray(
            image_2024
        )

        mask = np.ascontiguousarray(
            mask
        )

        return (
            image_2020,
            image_2024,
            mask
        )


    # ========================================================
    # GET SAMPLE
    # ========================================================

    def __getitem__(self, index):

        path_2020, path_2024, path_mask = (
            self.samples[index]
        )

        # ----------------------------------------------------
        # Read data
        # ----------------------------------------------------

        image_2020 = self.read_tiff(
            path_2020
        )

        image_2024 = self.read_tiff(
            path_2024
        )

        mask = self.read_tiff(
            path_mask
        )[0]


        # ----------------------------------------------------
        # Convert images to float32
        # ----------------------------------------------------

        image_2020 = image_2020.astype(
            np.float32
        )

        image_2024 = image_2024.astype(
            np.float32
        )


        # ----------------------------------------------------
        # Normalize images
        #
        # IMPORTANT:
        # This assumes your preprocessing already produced
        # normalized values.
        # ----------------------------------------------------

        image_2020 = np.nan_to_num(
            image_2020
        )

        image_2024 = np.nan_to_num(
            image_2024
        )


        # ----------------------------------------------------
        # Mask
        # ----------------------------------------------------

        mask = (
            mask > 0
        ).astype(
            np.float32
        )


        # ----------------------------------------------------
        # Augmentation
        # ----------------------------------------------------

        if self.augment:

            (
                image_2020,
                image_2024,
                mask
            ) = self.apply_augmentation(
                image_2020,
                image_2024,
                mask
            )


        # ----------------------------------------------------
        # Convert to PyTorch tensors
        # ----------------------------------------------------

        image_2020 = torch.from_numpy(
            image_2020.copy()
        )

        image_2024 = torch.from_numpy(
            image_2024.copy()
        )

        mask = torch.from_numpy(
            mask.copy()
        )


        # ----------------------------------------------------
        # Mask shape:
        #
        # [H, W]
        #
        # Change to:
        #
        # [1, H, W]
        # ----------------------------------------------------

        mask = mask.unsqueeze(
            0
        )


        return (
            image_2020,
            image_2024,
            mask
        )