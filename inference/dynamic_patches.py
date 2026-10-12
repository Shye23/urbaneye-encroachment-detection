from pathlib import Path
import numpy as np
import rasterio


def create_patches(
    image_2020,
    image_2024,
    patch_size=32,
    stride=16
):
    """
    Create paired patches from two already aligned image arrays.

    Input:
        image_2020: [C, H, W]
        image_2024: [C, H, W]

    Returns:
        list of tuples:
        (patch_2020, patch_2024, y, x)
    """

    if image_2020.shape != image_2024.shape:
        raise ValueError(
            f"Image shapes do not match: "
            f"{image_2020.shape} vs {image_2024.shape}"
        )

    _, height, width = image_2020.shape

    patches = []

    for y in range(0, height - patch_size + 1, stride):
        for x in range(0, width - patch_size + 1, stride):

            patch_2020 = image_2020[
                :,
                y:y + patch_size,
                x:x + patch_size
            ]

            patch_2024 = image_2024[
                :,
                y:y + patch_size,
                x:x + patch_size
            ]

            patches.append(
                (
                    patch_2020,
                    patch_2024,
                    y,
                    x
                )
            )

    return patches


def normalize_image(image):
    """
    Normalize each band independently using the same
    2nd/98th percentile normalization used during training.

    Output range: [0, 1]
    Input shape: [C, H, W]
    """

    image = image.astype(np.float32)

    normalized = np.zeros_like(
        image,
        dtype=np.float32
    )

    for i in range(image.shape[0]):

        band = image[i]

        band = np.nan_to_num(
            band,
            nan=0.0,
            posinf=0.0,
            neginf=0.0
        )

        p2 = np.percentile(
            band,
            2
        )

        p98 = np.percentile(
            band,
            98
        )

        band = np.clip(
            band,
            p2,
            p98
        )

        band = (
            band - p2
        ) / (
            p98 - p2 + 1e-8
        )

        normalized[i] = band

    return normalized


def pad_to_patch_size(
    image_2020,
    image_2024,
    patch_size=32,
    stride=16
):
    """
    Pad images so that patch extraction with the given
    patch size and stride covers the entire image.

    Returns:
        padded_2020
        padded_2024
        original_height
        original_width
    """

    _, height, width = image_2020.shape

    # Find the minimum padded dimensions that allow
    # the final patch to cover the image completely.
    if height <= patch_size:
        new_height = patch_size
    else:
        new_height = (
            ((height - patch_size + stride - 1) // stride)
            * stride
            + patch_size
        )

    if width <= patch_size:
        new_width = patch_size
    else:
        new_width = (
            ((width - patch_size + stride - 1) // stride)
            * stride
            + patch_size
        )

    padded_2020 = np.zeros(
        (
            image_2020.shape[0],
            new_height,
            new_width
        ),
        dtype=np.float32
    )

    padded_2024 = np.zeros(
        (
            image_2024.shape[0],
            new_height,
            new_width
        ),
        dtype=np.float32
    )

    # Copy original images into padded arrays.
    padded_2020[
        :,
        :height,
        :width
    ] = image_2020

    padded_2024[
        :,
        :height,
        :width
    ] = image_2024

    print(
        f"Original size: "
        f"{height} x {width}"
    )

    print(
        f"Padded size: "
        f"{new_height} x {new_width}"
    )

    return (
        padded_2020,
        padded_2024,
        height,
        width
    )