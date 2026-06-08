"""
CropMD – ResNet-50 Transfer Learning Model
38-class PlantVillage disease classifier
"""

import tensorflow as tf
from tensorflow.keras import layers, models, regularizers
from tensorflow.keras.applications import ResNet50
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import (
    EarlyStopping, ReduceLROnPlateau, ModelCheckpoint, TensorBoard
)
import numpy as np
import logging

logger = logging.getLogger(__name__)

# ─── Class Labels ────────────────────────────────────────────────────────────

CLASS_NAMES = [
    "Apple___Apple_scab",
    "Apple___Black_rot",
    "Apple___Cedar_apple_rust",
    "Apple___healthy",
    "Blueberry___healthy",
    "Cherry_(including_sour)___Powdery_mildew",
    "Cherry_(including_sour)___healthy",
    "Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot",
    "Corn_(maize)___Common_rust_",
    "Corn_(maize)___Northern_Leaf_Blight",
    "Corn_(maize)___healthy",
    "Grape___Black_rot",
    "Grape___Esca_(Black_Measles)",
    "Grape___Leaf_blight_(Isariopsis_Leaf_Spot)",
    "Grape___healthy",
    "Orange___Haunglongbing_(Citrus_greening)",
    "Peach___Bacterial_spot",
    "Peach___healthy",
    "Pepper,_bell___Bacterial_spot",
    "Pepper,_bell___healthy",
    "Potato___Early_blight",
    "Potato___Late_blight",
    "Potato___healthy",
    "Raspberry___healthy",
    "Soybean___healthy",
    "Squash___Powdery_mildew",
    "Strawberry___Leaf_scorch",
    "Strawberry___healthy",
    "Tomato___Bacterial_spot",
    "Tomato___Early_blight",
    "Tomato___Late_blight",
    "Tomato___Leaf_Mold",
    "Tomato___Septoria_leaf_spot",
    "Tomato___Spider_mites Two-spotted_spider_mite",
    "Tomato___Target_Spot",
    "Tomato___Tomato_Yellow_Leaf_Curl_Virus",
    "Tomato___Tomato_mosaic_virus",
    "Tomato___healthy",
]

NUM_CLASSES = len(CLASS_NAMES)  # 38
IMAGE_SIZE = (224, 224)
INPUT_SHAPE = (224, 224, 3)


# ─── Model Builder ───────────────────────────────────────────────────────────

def build_resnet50_model(
    num_classes: int = NUM_CLASSES,
    freeze_base: bool = True,
    dropout_rate: float = 0.4,
    l2_lambda: float = 1e-4,
) -> tf.keras.Model:
    """
    Build ResNet-50 transfer-learning model.
    Phase 1 – freeze base, train custom head.
    Phase 2 – unfreeze top layers for fine-tuning.
    """
    base_model = ResNet50(
        weights="imagenet",
        include_top=False,
        input_shape=INPUT_SHAPE,
    )
    base_model.trainable = not freeze_base

    inputs = tf.keras.Input(shape=INPUT_SHAPE, name="input_image")

    # Preprocessing (built-in ResNet50 preprocessing)
    x = tf.keras.applications.resnet50.preprocess_input(inputs)

    # Base model
    x = base_model(x, training=False)

    # Custom classification head
    x = layers.GlobalAveragePooling2D(name="gap")(x)
    x = layers.BatchNormalization(name="bn_head")(x)
    x = layers.Dense(
        512,
        activation="relu",
        kernel_regularizer=regularizers.l2(l2_lambda),
        name="dense_512",
    )(x)
    x = layers.Dropout(dropout_rate, name="dropout_1")(x)
    x = layers.Dense(
        256,
        activation="relu",
        kernel_regularizer=regularizers.l2(l2_lambda),
        name="dense_256",
    )(x)
    x = layers.Dropout(dropout_rate / 2, name="dropout_2")(x)
    outputs = layers.Dense(num_classes, activation="softmax", name="output")(x)

    model = models.Model(inputs, outputs, name="CropMD_ResNet50")
    return model


def unfreeze_top_layers(model: tf.keras.Model, num_layers: int = 30) -> tf.keras.Model:
    """Unfreeze the top N layers of the ResNet50 base for fine-tuning."""
    base = model.get_layer("resnet50")
    base.trainable = True
    for layer in base.layers[:-num_layers]:
        layer.trainable = False
    logger.info(f"Unfroze top {num_layers} layers of ResNet50")
    return model


def compile_model(
    model: tf.keras.Model,
    learning_rate: float = 1e-3,
    fine_tune: bool = False,
) -> tf.keras.Model:
    lr = learning_rate if not fine_tune else learning_rate / 10
    model.compile(
        optimizer=Adam(learning_rate=lr, clipnorm=1.0),
        loss=tf.keras.losses.CategoricalCrossentropy(label_smoothing=0.1),
        metrics=[
            "accuracy",
            tf.keras.metrics.TopKCategoricalAccuracy(k=3, name="top3_accuracy"),
            tf.keras.metrics.AUC(name="auc"),
        ],
    )
    return model


def get_callbacks(
    checkpoint_path: str = "checkpoints/cropmd_best.keras",
    log_dir: str = "logs/fit",
    patience: int = 7,
) -> list:
    return [
        EarlyStopping(
            monitor="val_accuracy",
            patience=patience,
            restore_best_weights=True,
            verbose=1,
        ),
        ReduceLROnPlateau(
            monitor="val_loss",
            factor=0.3,
            patience=3,
            min_lr=1e-7,
            verbose=1,
        ),
        ModelCheckpoint(
            filepath=checkpoint_path,
            monitor="val_accuracy",
            save_best_only=True,
            verbose=1,
        ),
        TensorBoard(log_dir=log_dir, histogram_freq=1),
    ]


def get_severity_from_confidence(confidence: float) -> str:
    """Map model confidence to a human-readable severity label."""
    if confidence >= 0.85:
        return "High"
    elif confidence >= 0.60:
        return "Medium"
    else:
        return "Low"


def format_class_name(raw: str) -> tuple[str, str]:
    """Return (crop_name, disease_name) from PlantVillage class label."""
    parts = raw.split("___")
    crop = parts[0].replace("_", " ").replace(",", "").strip()
    disease = parts[1].replace("_", " ").strip() if len(parts) > 1 else "Unknown"
    return crop, disease
