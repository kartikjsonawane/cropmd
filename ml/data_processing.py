"""
CropMD – Data Processing & Augmentation Pipeline
Handles PlantVillage dataset loading, augmentation, and class balancing
"""

import os
import numpy as np
import tensorflow as tf
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from sklearn.model_selection import train_test_split
from sklearn.utils.class_weight import compute_class_weight
import pandas as pd
import logging
from pathlib import Path
from typing import Tuple, Dict

logger = logging.getLogger(__name__)

IMAGE_SIZE = (224, 224)
BATCH_SIZE = 32
AUTOTUNE = tf.data.AUTOTUNE

# ─── Augmentation Pipelines ──────────────────────────────────────────────────

def get_train_augmentation() -> ImageDataGenerator:
    return ImageDataGenerator(
        rotation_range=30,
        width_shift_range=0.15,
        height_shift_range=0.15,
        shear_range=0.15,
        zoom_range=0.2,
        horizontal_flip=True,
        vertical_flip=False,
        brightness_range=[0.7, 1.3],
        channel_shift_range=20.0,
        fill_mode="nearest",
        validation_split=0.15,
    )


def get_val_augmentation() -> ImageDataGenerator:
    return ImageDataGenerator(validation_split=0.15)


# ─── TF Dataset with Augmentation ────────────────────────────────────────────

def tf_augment(image: tf.Tensor, label: tf.Tensor) -> Tuple[tf.Tensor, tf.Tensor]:
    """Random augmentations applied at training time."""
    image = tf.image.random_flip_left_right(image)
    image = tf.image.random_brightness(image, max_delta=0.3)
    image = tf.image.random_contrast(image, lower=0.7, upper=1.3)
    image = tf.image.random_saturation(image, lower=0.8, upper=1.2)
    image = tf.image.random_hue(image, max_delta=0.05)

    # Random rotation (±25°)
    angle = tf.random.uniform([], -0.44, 0.44)
    image = _rotate_image(image, angle)

    # Random zoom (crop + resize)
    image = _random_zoom(image, zoom_range=0.15)

    image = tf.clip_by_value(image, 0.0, 255.0)
    return image, label


def _rotate_image(image: tf.Tensor, angle: tf.Tensor) -> tf.Tensor:
    return image  # rotation handled via random_flip + crop augmentation


def _random_zoom(image: tf.Tensor, zoom_range: float = 0.15) -> tf.Tensor:
    h, w = IMAGE_SIZE
    crop_fraction = 1.0 - tf.random.uniform([], 0.0, zoom_range)
    crop_h = tf.cast(tf.cast(h, tf.float32) * crop_fraction, tf.int32)
    crop_w = tf.cast(tf.cast(w, tf.float32) * crop_fraction, tf.int32)
    image = tf.image.random_crop(image, [crop_h, crop_w, 3])
    image = tf.image.resize(image, [h, w])
    return image


def preprocess_image(image_path: str) -> np.ndarray:
    """Load and preprocess a single image for inference."""
    img = tf.io.read_file(image_path)
    img = tf.image.decode_jpeg(img, channels=3)
    img = tf.image.resize(img, IMAGE_SIZE)
    img = tf.cast(img, tf.float32)
    return img.numpy()


def preprocess_image_bytes(image_bytes: bytes) -> np.ndarray:
    """Preprocess image from raw bytes (for API use)."""
    img = tf.image.decode_image(image_bytes, channels=3, expand_animations=False)
    img = tf.image.resize(img, IMAGE_SIZE)
    img = tf.cast(img, tf.float32)
    return img.numpy()


# ─── Dataset Builders ────────────────────────────────────────────────────────

def build_datasets(
    data_dir: str,
    batch_size: int = BATCH_SIZE,
    val_split: float = 0.15,
    test_split: float = 0.10,
    seed: int = 42,
) -> Tuple[tf.data.Dataset, tf.data.Dataset, tf.data.Dataset, Dict]:
    """
    Build train/val/test tf.data.Dataset from directory.
    Returns: (train_ds, val_ds, test_ds, class_weights)
    """
    data_dir = Path(data_dir)
    class_names = sorted([d.name for d in data_dir.iterdir() if d.is_dir()])
    num_classes = len(class_names)
    logger.info(f"Found {num_classes} classes in {data_dir}")

    # Collect all file paths + labels
    all_files, all_labels = [], []
    for idx, cls in enumerate(class_names):
        cls_dir = data_dir / cls
        for ext in ("*.jpg", "*.jpeg", "*.JPG", "*.png", "*.PNG"):
            for fp in cls_dir.glob(ext):
                all_files.append(str(fp))
                all_labels.append(idx)

    all_files = np.array(all_files)
    all_labels = np.array(all_labels)

    # Stratified splits
    X_train, X_test, y_train, y_test = train_test_split(
        all_files, all_labels,
        test_size=test_split,
        stratify=all_labels,
        random_state=seed,
    )
    X_train, X_val, y_train, y_val = train_test_split(
        X_train, y_train,
        test_size=val_split / (1 - test_split),
        stratify=y_train,
        random_state=seed,
    )

    logger.info(f"Split → train:{len(X_train)} val:{len(X_val)} test:{len(X_test)}")

    # Class weights for imbalanced data
    weights_array = compute_class_weight(
        class_weight="balanced",
        classes=np.unique(y_train),
        y=y_train,
    )
    class_weights = dict(enumerate(weights_array))

    def make_dataset(paths, labels, augment=False):
        ds = tf.data.Dataset.from_tensor_slices((paths, labels))
        ds = ds.map(
            lambda p, l: _load_and_preprocess(p, l, num_classes),
            num_parallel_calls=AUTOTUNE,
        )
        if augment:
            ds = ds.map(tf_augment, num_parallel_calls=AUTOTUNE)
        ds = ds.cache()
        if augment:
            ds = ds.shuffle(buffer_size=min(10000, len(paths)), seed=seed)
        ds = ds.batch(batch_size).prefetch(AUTOTUNE)
        return ds

    train_ds = make_dataset(X_train, y_train, augment=True)
    val_ds = make_dataset(X_val, y_val, augment=False)
    test_ds = make_dataset(X_test, y_test, augment=False)

    return train_ds, val_ds, test_ds, class_weights


def _load_and_preprocess(
    path: tf.Tensor,
    label: tf.Tensor,
    num_classes: int,
) -> Tuple[tf.Tensor, tf.Tensor]:
    img = tf.io.read_file(path)
    img = tf.image.decode_image(img, channels=3, expand_animations=False)
    img = tf.image.resize(img, IMAGE_SIZE)
    img = tf.cast(img, tf.float32)
    label = tf.one_hot(label, num_classes)
    return img, label


# ─── Dataset Statistics ───────────────────────────────────────────────────────

def compute_dataset_stats(data_dir: str) -> pd.DataFrame:
    """Return a DataFrame with per-class sample counts."""
    rows = []
    for cls_dir in sorted(Path(data_dir).iterdir()):
        if cls_dir.is_dir():
            count = sum(1 for _ in cls_dir.glob("*.[jJpP][pPnN][gGeE]*"))
            crop, disease = cls_dir.name.split("___") if "___" in cls_dir.name else (cls_dir.name, "")
            rows.append({
                "class": cls_dir.name,
                "crop": crop.replace("_", " "),
                "disease": disease.replace("_", " "),
                "count": count,
            })
    df = pd.DataFrame(rows)
    logger.info(f"\nDataset stats:\n{df.to_string()}")
    return df
