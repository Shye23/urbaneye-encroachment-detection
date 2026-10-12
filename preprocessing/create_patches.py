import os
import glob
import re
import shutil
import numpy as np
import rasterio
from rasterio.windows import Window


# ============================================================
# MAIN DATA FOLDER
# ============================================================

base_folder = r"E:/UrbanEye/processed_data"


# ============================================================
# PATCH SETTINGS
# ============================================================

PATCH_SIZE = 32
STRIDE = 16


# ============================================================
# MINIMUM CHANGED PIXELS PER SPLIT
# ============================================================
#
# TRAIN:
# Keep only patches containing at least 20 changed pixels.
#
# VAL:
# Keep ALL patches.
#
# TEST:
# Keep ALL patches.
#
# This gives us a more realistic validation/test evaluation
# containing both changed and unchanged areas.
# ============================================================

MIN_MASK_PIXELS = {
    "train": 0,
    "val": 0,
    "test": 0
}


# ============================================================
# DATA SPLITS
# ============================================================

splits = [
    "train",
    "val",
    "test"
]


# ============================================================
# GET AOI ID FROM FILENAME
# ============================================================

def get_aoi_id(filename):

    match = re.search(
        r"(AOI\d+)",
        os.path.basename(filename)
    )

    if match is None:

        raise ValueError(
            f"Could not find AOI number in filename:\n{filename}"
        )

    return match.group(1)


# ============================================================
# GET PATCH POSITIONS
# ============================================================

def get_positions(size, patch_size, stride):

    positions = list(
        range(
            0,
            size - patch_size + 1,
            stride
        )
    )

    # Include final edge position
    final_position = size - patch_size

    if final_position not in positions:

        positions.append(final_position)

    return sorted(set(positions))


# ============================================================
# PROCESS EACH SPLIT
# ============================================================

for split in splits:

    print("\n")
    print("=" * 70)
    print(f"PROCESSING: {split.upper()}")
    print("=" * 70)


    # --------------------------------------------------------
    # MINIMUM MASK PIXELS FOR THIS SPLIT
    # --------------------------------------------------------

    min_mask_pixels = MIN_MASK_PIXELS[split]

    print(
        f"Minimum changed pixels: {min_mask_pixels}"
    )


    # --------------------------------------------------------
    # INPUT FOLDERS
    # --------------------------------------------------------

    folder_2020 = os.path.join(
        base_folder,
        split,
        "2020"
    )

    folder_2024 = os.path.join(
        base_folder,
        split,
        "2024"
    )

    folder_masks = os.path.join(
        base_folder,
        split,
        "masks"
    )


    # --------------------------------------------------------
    # OUTPUT FOLDER
    # --------------------------------------------------------

    output_root = os.path.join(
        base_folder,
        "patches",
        split
    )

    output_2020 = os.path.join(
        output_root,
        "2020"
    )

    output_2024 = os.path.join(
        output_root,
        "2024"
    )

    output_masks = os.path.join(
        output_root,
        "masks"
    )


    # --------------------------------------------------------
    # CREATE OUTPUT DIRECTORIES
    # --------------------------------------------------------

    os.makedirs(
        output_2020,
        exist_ok=True
    )

    os.makedirs(
        output_2024,
        exist_ok=True
    )

    os.makedirs(
        output_masks,
        exist_ok=True
    )


    # --------------------------------------------------------
    # FIND FILES
    # --------------------------------------------------------

    files_2020 = sorted(
        glob.glob(
            os.path.join(
                folder_2020,
                "*.tif"
            )
        )
    )

    files_2024 = sorted(
        glob.glob(
            os.path.join(
                folder_2024,
                "*.tif"
            )
        )
    )

    files_masks = sorted(
        glob.glob(
            os.path.join(
                folder_masks,
                "*.tif"
            )
        )
    )


    print()
    print(f"2020 images : {len(files_2020)}")
    print(f"2024 images : {len(files_2024)}")
    print(f"Masks       : {len(files_masks)}")


    # ========================================================
    # BASIC COUNT CHECK
    # ========================================================

    if len(files_2020) != len(files_2024):

        raise ValueError(
            f"{split}: Number of 2020 and 2024 images "
            "does not match!"
        )


    if len(files_2020) != len(files_masks):

        raise ValueError(
            f"{split}: Number of images and masks "
            "does not match!"
        )


    # ========================================================
    # CREATE AOI LOOKUPS
    # ========================================================

    lookup_2020 = {
        get_aoi_id(path): path
        for path in files_2020
    }

    lookup_2024 = {
        get_aoi_id(path): path
        for path in files_2024
    }

    lookup_masks = {
        get_aoi_id(path): path
        for path in files_masks
    }


    # ========================================================
    # CHECK AOI MATCHING
    # ========================================================

    if set(lookup_2020.keys()) != set(lookup_2024.keys()):

        raise ValueError(
            f"{split}: AOI IDs between 2020 and 2024 "
            "do not match!"
        )


    if set(lookup_2020.keys()) != set(lookup_masks.keys()):

        raise ValueError(
            f"{split}: AOI IDs between images and masks "
            "do not match!"
        )


    aoi_ids = sorted(
        lookup_2020.keys()
    )


    # ========================================================
    # SPLIT STATISTICS
    # ========================================================

    split_generated = 0
    split_skipped = 0
    split_changed_pixels = 0


    # ========================================================
    # PROCESS EACH AOI
    # ========================================================

    for aoi in aoi_ids:

        path_2020 = lookup_2020[aoi]
        path_2024 = lookup_2024[aoi]
        path_mask = lookup_masks[aoi]


        print("\n--------------------------------------------")
        print(f"AOI: {aoi}")
        print("--------------------------------------------")

        print(
            "2020:",
            os.path.basename(path_2020)
        )

        print(
            "2024:",
            os.path.basename(path_2024)
        )

        print(
            "Mask:",
            os.path.basename(path_mask)
        )


        # ====================================================
        # OPEN DATASETS
        # ====================================================

        with rasterio.open(path_2020) as src20, \
             rasterio.open(path_2024) as src24, \
             rasterio.open(path_mask) as srcmask:


            # ------------------------------------------------
            # DIMENSION CHECK
            # ------------------------------------------------

            if (
                src20.width != src24.width
                or src20.height != src24.height
            ):

                raise ValueError(
                    f"{aoi}: 2020 and 2024 dimensions "
                    "do not match!"
                )


            if (
                src20.width != srcmask.width
                or src20.height != srcmask.height
            ):

                raise ValueError(
                    f"{aoi}: Image and mask dimensions "
                    "do not match!"
                )


            # ------------------------------------------------
            # CRS CHECK
            # ------------------------------------------------

            if src20.crs != src24.crs:

                raise ValueError(
                    f"{aoi}: 2020 and 2024 CRS "
                    "do not match!"
                )


            if src20.crs != srcmask.crs:

                raise ValueError(
                    f"{aoi}: Image and mask CRS "
                    "do not match!"
                )


            # ------------------------------------------------
            # SPATIAL ALIGNMENT CHECK
            # ------------------------------------------------

            if src20.transform != src24.transform:

                raise ValueError(
                    f"{aoi}: 2020 and 2024 transforms "
                    "do not match!"
                )


            if src20.transform != srcmask.transform:

                raise ValueError(
                    f"{aoi}: Image and mask transforms "
                    "do not match!"
                )


            width = src20.width
            height = src20.height


            print(
                f"Dimensions: {width} × {height}"
            )

            print(
                f"2020 bands: {src20.count}"
            )

            print(
                f"2024 bands: {src24.count}"
            )


            # ------------------------------------------------
            # MAKE SURE AOI IS LARGE ENOUGH
            # ------------------------------------------------

            if (
                width < PATCH_SIZE
                or height < PATCH_SIZE
            ):

                raise ValueError(
                    f"{aoi}: AOI smaller than patch size!"
                )


            # ------------------------------------------------
            # PATCH POSITIONS
            # ------------------------------------------------

            x_positions = get_positions(
                width,
                PATCH_SIZE,
                STRIDE
            )

            y_positions = get_positions(
                height,
                PATCH_SIZE,
                STRIDE
            )


            total_possible = (
                len(x_positions)
                * len(y_positions)
            )


            print(
                f"Patch grid: "
                f"{len(x_positions)} × "
                f"{len(y_positions)}"
            )

            print(
                f"Possible patches: "
                f"{total_possible}"
            )


            aoi_generated = 0
            aoi_skipped = 0
            aoi_changed_pixels = 0


            # =================================================
            # CREATE PATCHES
            # =================================================

            for y in y_positions:

                for x in x_positions:


                    # -----------------------------------------
                    # WINDOW
                    # -----------------------------------------

                    window = Window(
                        x,
                        y,
                        PATCH_SIZE,
                        PATCH_SIZE
                    )


                    # -----------------------------------------
                    # READ DATA
                    # -----------------------------------------

                    patch20 = src20.read(
                        window=window
                    )

                    patch24 = src24.read(
                        window=window
                    )

                    patch_mask = srcmask.read(
                        1,
                        window=window
                    )


                    # -----------------------------------------
                    # SIZE CHECK
                    # -----------------------------------------

                    if (
                        patch20.shape[1] != PATCH_SIZE
                        or patch20.shape[2] != PATCH_SIZE
                    ):
                        continue


                    if (
                        patch24.shape[1] != PATCH_SIZE
                        or patch24.shape[2] != PATCH_SIZE
                    ):
                        continue


                    if patch_mask.shape != (
                        PATCH_SIZE,
                        PATCH_SIZE
                    ):
                        continue


                    # -----------------------------------------
                    # BINARY MASK
                    # -----------------------------------------

                    mask_binary = (
                        patch_mask > 0
                    )


                    # -----------------------------------------
                    # COUNT CHANGED PIXELS
                    # -----------------------------------------

                    changed_pixels = np.count_nonzero(
                        mask_binary
                    )


                    aoi_changed_pixels += (
                        changed_pixels
                    )

                    split_changed_pixels += (
                        changed_pixels
                    )


                    # -----------------------------------------
                    # SKIP BASED ON SPLIT THRESHOLD
                    # -----------------------------------------

                    if (
                        changed_pixels
                        < min_mask_pixels
                    ):

                        aoi_skipped += 1
                        split_skipped += 1

                        continue


                    # -----------------------------------------
                    # PATCH NAME
                    # -----------------------------------------

                    patch_name = (
                        f"{aoi}"
                        f"_y{y:03d}"
                        f"_x{x:03d}"
                        f".tif"
                    )


                    # -----------------------------------------
                    # PATCH TRANSFORM
                    # -----------------------------------------

                    patch_transform = (
                        src20.window_transform(
                            window
                        )
                    )


                    # =================================================
                    # 2020 PROFILE
                    # =================================================

                    profile20 = src20.profile.copy()

                    profile20.update(
                        height=PATCH_SIZE,
                        width=PATCH_SIZE,
                        transform=patch_transform,
                        compress="lzw"
                    )


                    # =================================================
                    # 2024 PROFILE
                    # =================================================

                    profile24 = src24.profile.copy()

                    profile24.update(
                        height=PATCH_SIZE,
                        width=PATCH_SIZE,
                        transform=patch_transform,
                        compress="lzw"
                    )


                    # =================================================
                    # MASK PROFILE
                    # =================================================

                    mask_profile = srcmask.profile.copy()

                    mask_profile.update(
                        height=PATCH_SIZE,
                        width=PATCH_SIZE,
                        count=1,
                        dtype=rasterio.uint8,
                        transform=patch_transform,
                        compress="lzw"
                    )


                    # =================================================
                    # SAVE 2020 PATCH
                    # =================================================

                    output_path_2020 = os.path.join(
                        output_2020,
                        patch_name
                    )


                    with rasterio.open(
                        output_path_2020,
                        "w",
                        **profile20
                    ) as dst:

                        dst.write(patch20)


                    # =================================================
                    # SAVE 2024 PATCH
                    # =================================================

                    output_path_2024 = os.path.join(
                        output_2024,
                        patch_name
                    )


                    with rasterio.open(
                        output_path_2024,
                        "w",
                        **profile24
                    ) as dst:

                        dst.write(patch24)


                    # =================================================
                    # SAVE MASK PATCH
                    # =================================================

                    output_path_mask = os.path.join(
                        output_masks,
                        patch_name
                    )


                    with rasterio.open(
                        output_path_mask,
                        "w",
                        **mask_profile
                    ) as dst:

                        dst.write(
                            mask_binary.astype(
                                np.uint8
                            ),
                            1
                        )


                    # -----------------------------------------
                    # UPDATE COUNTERS
                    # -----------------------------------------

                    aoi_generated += 1
                    split_generated += 1


            # =================================================
            # AOI SUMMARY
            # =================================================

            print()
            print(
                f"Generated: {aoi_generated}"
            )

            print(
                f"Skipped:   {aoi_skipped}"
            )

            print(
                f"Changed pixels across generated patches: "
                f"{aoi_changed_pixels}"
            )


    # ========================================================
    # SPLIT SUMMARY
    # ========================================================

    print("\n")
    print("=" * 60)
    print(f"{split.upper()} COMPLETE")
    print("=" * 60)

    print(
        f"Generated patches: {split_generated}"
    )

    print(
        f"Skipped patches:   {split_skipped}"
    )

    print(
        f"Total changed pixels: "
        f"{split_changed_pixels}"
    )


# ============================================================
# FINAL SUMMARY
# ============================================================

print("\n")
print("=" * 70)
print("ALL PATCH GENERATION COMPLETE")
print("=" * 70)

print()
print("Patch size        :", PATCH_SIZE)
print("Stride            :", STRIDE)
print(
    "Train min pixels  :",
    MIN_MASK_PIXELS["train"]
)
print(
    "Val min pixels    :",
    MIN_MASK_PIXELS["val"]
)
print(
    "Test min pixels   :",
    MIN_MASK_PIXELS["test"]
)

print("\nOutput structure:")

print(
    os.path.join(
        base_folder,
        "patches",
        "train"
    )
)

print(
    os.path.join(
        base_folder,
        "patches",
        "val"
    )
)

print(
    os.path.join(
        base_folder,
        "patches",
        "test"
    )
)

print("\nDone.")