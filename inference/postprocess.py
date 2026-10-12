import os
import numpy as np
import matplotlib.pyplot as plt

from scipy import ndimage


# ============================================================
# CONFIGURATION
# ============================================================

INPUT_PATH = (
    r"E:\UrbanEye\outputs\stitched\AOI10_prediction.npy"
)

OUTPUT_DIR = r"E:\UrbanEye\outputs\postprocessed"

# Morphological kernel
KERNEL_SIZE = 3

# Remove connected regions smaller than this many pixels
MIN_COMPONENT_SIZE = 4


# ============================================================
# LOAD RAW PREDICTION
# ============================================================

def main():

    print("=" * 70)
    print("UrbanEye - POST-PROCESSING")
    print("=" * 70)

    os.makedirs(
        OUTPUT_DIR,
        exist_ok=True
    )

    prediction = np.load(
        INPUT_PATH
    )

    prediction = (
        prediction > 0
    ).astype(np.uint8)

    print(
        f"Input shape: {prediction.shape}"
    )

    print(
        f"Raw changed pixels: "
        f"{prediction.sum()}"
    )


    # ========================================================
    # MORPHOLOGICAL OPERATIONS
    # ========================================================

    structure = np.ones(
        (KERNEL_SIZE, KERNEL_SIZE),
        dtype=bool
    )

    # --------------------------------------------------------
    # Opening
    # Removes very small isolated noise
    # --------------------------------------------------------

    opened = ndimage.binary_opening(
        prediction,
        structure=structure
    )


    # --------------------------------------------------------
    # Closing
    # Fills small gaps and connects nearby pixels
    # --------------------------------------------------------

    closed = ndimage.binary_closing(
        opened,
        structure=structure
    )


    # ========================================================
    # CONNECTED COMPONENT ANALYSIS
    # ========================================================

    labeled, num_components = ndimage.label(
        closed,
        structure=structure
    )

    print(
        f"Connected components before filtering: "
        f"{num_components}"
    )


    component_sizes = np.bincount(
        labeled.ravel()
    )

    cleaned = np.zeros_like(
        closed,
        dtype=np.uint8
    )


    for component_id in range(
        1,
        len(component_sizes)
    ):

        size = component_sizes[
            component_id
        ]

        if size >= MIN_COMPONENT_SIZE:

            cleaned[
                labeled == component_id
            ] = 1


    # ========================================================
    # FINAL STATISTICS
    # ========================================================

    labeled_final, final_components = ndimage.label(
        cleaned,
        structure=structure
    )

    raw_pixels = int(
        prediction.sum()
    )

    opened_pixels = int(
        opened.sum()
    )

    closed_pixels = int(
        closed.sum()
    )

    final_pixels = int(
        cleaned.sum()
    )


    print("\n" + "-" * 70)
    print("POST-PROCESSING RESULTS")
    print("-" * 70)

    print(
        f"Raw change pixels       : {raw_pixels}"
    )

    print(
        f"After opening           : {opened_pixels}"
    )

    print(
        f"After closing           : {closed_pixels}"
    )

    print(
        f"After component filter  : {final_pixels}"
    )

    print(
        f"Final connected regions : {final_components}"
    )


    # ========================================================
    # SAVE RESULTS
    # ========================================================

    output_path = os.path.join(
        OUTPUT_DIR,
        "AOI10_postprocessed.npy"
    )

    np.save(
        output_path,
        cleaned
    )

    print(
        f"\nSaved cleaned mask:"
    )

    print(output_path)


    # ========================================================
    # VISUALIZATION
    # ========================================================

    fig, axes = plt.subplots(
        1,
        3,
        figsize=(15, 5)
    )


    axes[0].imshow(
        prediction,
        cmap="gray"
    )

    axes[0].set_title(
        "Raw Prediction"
    )

    axes[0].axis("off")


    axes[1].imshow(
        closed,
        cmap="gray"
    )

    axes[1].set_title(
        "After Morphology"
    )

    axes[1].axis("off")


    axes[2].imshow(
        cleaned,
        cmap="gray"
    )

    axes[2].set_title(
        "Final Cleaned Mask"
    )

    axes[2].axis("off")


    plt.tight_layout()


    figure_path = os.path.join(
        OUTPUT_DIR,
        "AOI10_postprocessing.png"
    )

    plt.savefig(
        figure_path,
        dpi=200,
        bbox_inches="tight"
    )

    plt.close()


    print(
        f"Saved visualization:"
    )

    print(figure_path)


    print("\n" + "=" * 70)
    print("POST-PROCESSING COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()