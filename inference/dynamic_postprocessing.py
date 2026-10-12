
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
from scipy import ndimage


def postprocess_mask(
    prediction,
    output_dir,
    prefix="AOI10",
    kernel_size=3,
    min_component_size=4
):
    """
    Postprocess a binary change mask without relying
    on hardcoded AOI10 file paths.
    """

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    prediction = (prediction > 0).astype(np.uint8)

    structure = np.ones(
        (kernel_size, kernel_size),
        dtype=bool
    )

    opened = ndimage.binary_opening(
        prediction,
        structure=structure
    )

    closed = ndimage.binary_closing(
        opened,
        structure=structure
    )

    labeled, num_components = ndimage.label(
        closed,
        structure=structure
    )

    component_sizes = np.bincount(labeled.ravel())

    cleaned = np.zeros_like(prediction, dtype=np.uint8)

    for component_id in range(1, num_components + 1):
        if component_sizes[component_id] >= min_component_size:
            cleaned[labeled == component_id] = 1

    _, final_components = ndimage.label(
        cleaned,
        structure=structure
    )

    print("\nPOSTPROCESSING")
    print(f"Raw changed pixels: {int(prediction.sum())}")
    print(f"After opening: {int(opened.sum())}")
    print(f"After closing: {int(closed.sum())}")
    print(f"Final changed pixels: {int(cleaned.sum())}")
    print(f"Final regions: {final_components}")

    mask_path = output_dir / f"{prefix}_postprocessed.npy"
    np.save(mask_path, cleaned)

    figure, axes = plt.subplots(1, 3, figsize=(15, 5))

    axes[0].imshow(prediction, cmap="gray")
    axes[0].set_title("Raw Prediction")
    axes[0].axis("off")

    axes[1].imshow(closed, cmap="gray")
    axes[1].set_title("After Morphology")
    axes[1].axis("off")

    axes[2].imshow(cleaned, cmap="gray")
    axes[2].set_title("Postprocessed Prediction")
    axes[2].axis("off")

    figure.tight_layout()
    figure.savefig(
        output_dir / f"{prefix}_postprocessing.png",
        dpi=200,
        bbox_inches="tight"
    )
    plt.close(figure)

    return {
        "mask": cleaned,
        "mask_path": str(mask_path),
        "raw_pixels": int(prediction.sum()),
        "final_pixels": int(cleaned.sum()),
        "final_regions": int(final_components)
    }
