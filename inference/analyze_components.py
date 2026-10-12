import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from scipy import ndimage


# ============================================================
# CONFIGURATION
# ============================================================

POSTPROCESSED_MASK = (
    r"E:\UrbanEye\outputs\postprocessed"
    r"\AOI10_postprocessed.npy"
)

PROBABILITY_MAP = (
    r"E:\UrbanEye\outputs\stitched"
    r"\AOI10_probability.npy"
)

OUTPUT_DIR = (
    r"E:\UrbanEye\outputs\components"
)

MIN_COMPONENT_SIZE = 4


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print("UrbanEye - CONNECTED COMPONENT ANALYSIS")
    print("=" * 70)

    os.makedirs(
        OUTPUT_DIR,
        exist_ok=True
    )

    # --------------------------------------------------------
    # Load masks
    # --------------------------------------------------------

    mask = np.load(
        POSTPROCESSED_MASK
    ).astype(np.uint8)

    probability = np.load(
        PROBABILITY_MAP
    ).astype(np.float32)

    print(
        f"Mask shape: {mask.shape}"
    )

    # --------------------------------------------------------
    # Label connected regions
    # --------------------------------------------------------

    structure = np.ones(
        (3, 3),
        dtype=np.uint8
    )

    labeled, num_components = ndimage.label(
        mask,
        structure=structure
    )

    print(
        f"Connected components: {num_components}"
    )

    # --------------------------------------------------------
    # Analyze each component
    # --------------------------------------------------------

    regions = []

    for region_id in range(
        1,
        num_components + 1
    ):

        component = (
            labeled == region_id
        )

        pixel_count = int(
            component.sum()
        )

        if pixel_count < MIN_COMPONENT_SIZE:
            continue

        # --------------------------------------------
        # Coordinates
        # --------------------------------------------

        y_coords, x_coords = np.where(
            component
        )

        min_y = int(y_coords.min())
        max_y = int(y_coords.max())

        min_x = int(x_coords.min())
        max_x = int(x_coords.max())

        # --------------------------------------------
        # Centroid
        # --------------------------------------------

        centroid_y = float(
            y_coords.mean()
        )

        centroid_x = float(
            x_coords.mean()
        )

        # --------------------------------------------
        # Mean / maximum confidence
        # --------------------------------------------

        region_probabilities = probability[
            component
        ]

        mean_probability = float(
            region_probabilities.mean()
        )

        max_probability = float(
            region_probabilities.max()
        )

        # --------------------------------------------
        # Probability-weighted confidence
        # --------------------------------------------

        # Number of pixels above threshold
        high_confidence_pixels = int(
            (
                region_probabilities >= 0.80
            ).sum()
        )

        regions.append(
            {
                "region_id": region_id,
                "pixel_count": pixel_count,
                "mean_probability": mean_probability,
                "max_probability": max_probability,
                "pixels_probability_ge_0.80":
                    high_confidence_pixels,
                "centroid_x": centroid_x,
                "centroid_y": centroid_y,
                "min_x": min_x,
                "min_y": min_y,
                "max_x": max_x,
                "max_y": max_y,
                "width_pixels":
                    max_x - min_x + 1,
                "height_pixels":
                    max_y - min_y + 1,
            }
        )

    # --------------------------------------------------------
    # Create dataframe
    # --------------------------------------------------------

    df = pd.DataFrame(
        regions
    )

    if len(df) == 0:

        print(
            "No connected components found."
        )

        return

    # --------------------------------------------------------
    # Sort by size
    # --------------------------------------------------------

    df = df.sort_values(
        by="pixel_count",
        ascending=False
    ).reset_index(
        drop=True
    )

    # Reassign ranking
    df.insert(
        0,
        "rank",
        np.arange(
            1,
            len(df) + 1
        )
    )

    # --------------------------------------------------------
    # Save CSV
    # --------------------------------------------------------

    csv_path = os.path.join(
        OUTPUT_DIR,
        "AOI10_components.csv"
    )

    df.to_csv(
        csv_path,
        index=False
    )

    # --------------------------------------------------------
    # Print summary
    # --------------------------------------------------------

    print("\n" + "-" * 70)
    print("COMPONENT SUMMARY")
    print("-" * 70)

    print(
        f"Regions analyzed : {len(df)}"
    )

    print(
        f"Total change pixels : "
        f"{df['pixel_count'].sum()}"
    )

    print(
        f"Largest region : "
        f"{df['pixel_count'].max()} pixels"
    )

    print(
        f"Smallest region : "
        f"{df['pixel_count'].min()} pixels"
    )

    print(
        f"Mean region size : "
        f"{df['pixel_count'].mean():.2f} pixels"
    )

    print(
        f"Mean confidence : "
        f"{df['mean_probability'].mean():.4f}"
    )

    # --------------------------------------------------------
    # Print top 10 regions
    # --------------------------------------------------------

    print("\nTop 10 detected regions:")
    print()

    display_columns = [
        "rank",
        "region_id",
        "pixel_count",
        "mean_probability",
        "max_probability",
        "centroid_x",
        "centroid_y"
    ]

    print(
        df[
            display_columns
        ].head(10).to_string(
            index=False
        )
    )

    # --------------------------------------------------------
    # Save labeled map
    # --------------------------------------------------------

    labeled_path = os.path.join(
        OUTPUT_DIR,
        "AOI10_labeled.npy"
    )

    np.save(
        labeled_path,
        labeled
    )

    # --------------------------------------------------------
    # Visualization
    # --------------------------------------------------------

    fig, ax = plt.subplots(
        figsize=(10, 10)
    )

    ax.imshow(
        mask,
        cmap="gray"
    )

    # Add region numbers
    for _, row in df.iterrows():

        ax.text(
            row["centroid_x"],
            row["centroid_y"],
            str(int(row["rank"])),
            fontsize=8,
            ha="center",
            va="center"
        )

    ax.set_title(
        "UrbanEye - Detected Change Regions"
    )

    ax.axis("off")

    plt.tight_layout()

    figure_path = os.path.join(
        OUTPUT_DIR,
        "AOI10_components.png"
    )

    plt.savefig(
        figure_path,
        dpi=200,
        bbox_inches="tight"
    )

    plt.close()

    # --------------------------------------------------------
    # Final output
    # --------------------------------------------------------

    print("\n" + "-" * 70)

    print(
        f"CSV saved:"
    )

    print(csv_path)

    print(
        f"\nLabeled map saved:"
    )

    print(labeled_path)

    print(
        f"\nVisualization saved:"
    )

    print(figure_path)

    print("\n" + "=" * 70)
    print("CONNECTED COMPONENT ANALYSIS COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()