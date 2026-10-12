from pathlib import Path

from inference.dynamic_pipeline import run_detection


ROOT = Path(
    r"E:\UrbanEye"
)

IMAGE_2020 = (
    ROOT /
    "output" /
    "2020" /
    "AOI10_2020.tif"
)

IMAGE_2024 = (
    ROOT /
    "output" /
    "2024" /
    "AOI10_2024.tif"
)

CHECKPOINT = (
    ROOT /
    "training" /
    "checkpoints" /
    "snunet" /
    "baseline" /
    "best_model.pth"
)

OUTPUT = (
    ROOT /
    "outputs" /
    "dynamic"
)


if __name__ == "__main__":

    run_detection(
        image_2020=IMAGE_2020,
        image_2024=IMAGE_2024,
        checkpoint=CHECKPOINT,
        output_dir=OUTPUT,
        threshold=0.60
    )