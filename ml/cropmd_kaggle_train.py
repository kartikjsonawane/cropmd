# ============================================================
# CropMD – Kaggle Training Script
# Run this in a Kaggle Notebook with:
#   Dataset: abdallahalidev/plantvillage-dataset
#   Accelerator: GPU T4 x2 (free)
# ============================================================

# CELL 1 – Imports
import os, json, logging, numpy as np, tensorflow as tf
from pathlib import Path
from datetime import datetime
from tensorflow.keras.applications import ResNet50
from tensorflow.keras import layers, models, regularizers
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau, ModelCheckpoint
from sklearn.model_selection import train_test_split
from sklearn.utils.class_weight import compute_class_weight

print("TF version:", tf.__version__)
print("GPU:", tf.config.list_physical_devices('GPU'))

# CELL 2 – Config
DATA_DIR    = "/kaggle/input/plantvillage-dataset/color"
OUTPUT_DIR  = "/kaggle/working/outputs"
IMAGE_SIZE  = (224, 224)
BATCH_SIZE  = 32
EPOCHS_P1   = 20
EPOCHS_P2   = 15
AUTOTUNE    = tf.data.AUTOTUNE
Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

# CELL 3 – Collect files
class_names = sorted([d for d in os.listdir(DATA_DIR) if os.path.isdir(os.path.join(DATA_DIR, d))])
NUM_CLASSES = len(class_names)
print(f"Found {NUM_CLASSES} classes")

all_files, all_labels = [], []
for idx, cls in enumerate(class_names):
    cls_dir = os.path.join(DATA_DIR, cls)
    for fname in os.listdir(cls_dir):
        if fname.lower().endswith(('.jpg', '.jpeg', '.png')):
            all_files.append(os.path.join(cls_dir, fname))
            all_labels.append(idx)

all_files  = np.array(all_files)
all_labels = np.array(all_labels)
print(f"Total images: {len(all_files)}")

# CELL 4 – Splits
X_train, X_test, y_train, y_test = train_test_split(
    all_files, all_labels, test_size=0.10, stratify=all_labels, random_state=42)
X_train, X_val, y_train, y_val = train_test_split(
    X_train, y_train, test_size=0.15/0.90, stratify=y_train, random_state=42)
print(f"Train: {len(X_train)} | Val: {len(X_val)} | Test: {len(X_test)}")

weights_array = compute_class_weight('balanced', classes=np.unique(y_train), y=y_train)
class_weights = dict(enumerate(weights_array))

# CELL 5 – tf.data pipeline
def load_and_preprocess(path, label):
    img = tf.io.read_file(path)
    img = tf.image.decode_image(img, channels=3, expand_animations=False)
    img = tf.image.resize(img, IMAGE_SIZE)
    img = tf.cast(img, tf.float32)
    label = tf.one_hot(label, NUM_CLASSES)
    return img, label

def augment(img, label):
    img = tf.image.random_flip_left_right(img)
    img = tf.image.random_brightness(img, 0.3)
    img = tf.image.random_contrast(img, 0.7, 1.3)
    img = tf.image.random_saturation(img, 0.8, 1.2)
    img = tf.clip_by_value(img, 0, 255)
    return img, label

def make_ds(paths, labels, augment_flag=False):
    ds = tf.data.Dataset.from_tensor_slices((paths, labels))
    ds = ds.map(load_and_preprocess, num_parallel_calls=AUTOTUNE)
    if augment_flag:
        ds = ds.map(augment, num_parallel_calls=AUTOTUNE)
    ds = ds.cache()
    if augment_flag:
        ds = ds.shuffle(5000, seed=42)
    return ds.batch(BATCH_SIZE).prefetch(AUTOTUNE)

train_ds = make_ds(X_train, y_train, augment_flag=True)
val_ds   = make_ds(X_val,   y_val)
test_ds  = make_ds(X_test,  y_test)

# CELL 6 – Build model
def build_model(freeze_base=True):
    base = ResNet50(weights='imagenet', include_top=False, input_shape=(224,224,3))
    base.trainable = not freeze_base
    inputs = tf.keras.Input(shape=(224,224,3))
    x = tf.keras.applications.resnet50.preprocess_input(inputs)
    x = base(x, training=False)
    x = layers.GlobalAveragePooling2D()(x)
    x = layers.BatchNormalization()(x)
    x = layers.Dense(512, activation='relu', kernel_regularizer=regularizers.l2(1e-4))(x)
    x = layers.Dropout(0.4)(x)
    x = layers.Dense(256, activation='relu', kernel_regularizer=regularizers.l2(1e-4))(x)
    x = layers.Dropout(0.2)(x)
    outputs = layers.Dense(NUM_CLASSES, activation='softmax')(x)
    return tf.keras.Model(inputs, outputs), base

model, base_model = build_model(freeze_base=True)

# CELL 7 – Phase 1: Train head only
model.compile(
    optimizer=Adam(1e-3),
    loss=tf.keras.losses.CategoricalCrossentropy(label_smoothing=0.1),
    metrics=['accuracy', tf.keras.metrics.TopKCategoricalAccuracy(k=3, name='top3')]
)

callbacks_p1 = [
    EarlyStopping(monitor='val_accuracy', patience=5, restore_best_weights=True, verbose=1),
    ReduceLROnPlateau(monitor='val_loss', factor=0.3, patience=3, min_lr=1e-7, verbose=1),
    ModelCheckpoint(f"{OUTPUT_DIR}/phase1_best.weights.h5", monitor='val_accuracy',
                    save_best_only=True, save_weights_only=True, verbose=1),
]

print("\n=== Phase 1: Training head (frozen ResNet50) ===")
history1 = model.fit(
    train_ds, epochs=EPOCHS_P1, validation_data=val_ds,
    class_weight=class_weights, callbacks=callbacks_p1
)
print(f"Phase 1 best val accuracy: {max(history1.history['val_accuracy']):.4f}")

# CELL 8 – Phase 2: Fine-tune top 30 layers
base_model.trainable = True
for layer in base_model.layers[:-30]:
    layer.trainable = False

model.compile(
    optimizer=Adam(1e-4),
    loss=tf.keras.losses.CategoricalCrossentropy(label_smoothing=0.1),
    metrics=['accuracy', tf.keras.metrics.TopKCategoricalAccuracy(k=3, name='top3')]
)

callbacks_p2 = [
    EarlyStopping(monitor='val_accuracy', patience=5, restore_best_weights=True, verbose=1),
    ReduceLROnPlateau(monitor='val_loss', factor=0.3, patience=3, min_lr=1e-7, verbose=1),
    ModelCheckpoint(f"{OUTPUT_DIR}/phase2_best.weights.h5", monitor='val_accuracy',
                    save_best_only=True, save_weights_only=True, verbose=1),
]

print("\n=== Phase 2: Fine-tuning top 30 layers ===")
history2 = model.fit(
    train_ds, epochs=EPOCHS_P2, validation_data=val_ds,
    class_weight=class_weights, callbacks=callbacks_p2,
    initial_epoch=len(history1.history['val_accuracy'])
)
print(f"Phase 2 best val accuracy: {max(history2.history['val_accuracy']):.4f}")

# CELL 9 – Evaluate on test set
print("\n=== Test Set Evaluation ===")
test_loss, test_acc, test_top3 = model.evaluate(test_ds, verbose=1)
print(f"Test Accuracy : {test_acc:.4f}")
print(f"Test Top-3    : {test_top3:.4f}")

# CELL 10 – Save model + class names
model.save(f"{OUTPUT_DIR}/cropmd_model.keras", save_format="keras")
with open(f"{OUTPUT_DIR}/class_names.json", "w") as f:
    json.dump(class_names, f, indent=2)

# Save config summary
config = {
    "num_classes": NUM_CLASSES,
    "image_size": [224, 224],
    "test_accuracy": float(test_acc),
    "test_top3_accuracy": float(test_top3),
    "phase1_best_val_acc": float(max(history1.history['val_accuracy'])),
    "phase2_best_val_acc": float(max(history2.history['val_accuracy'])),
    "class_names": class_names,
}
with open(f"{OUTPUT_DIR}/training_config.json", "w") as f:
    json.dump(config, f, indent=2)

print(f"\n✅ Done! Files saved to {OUTPUT_DIR}")
print(f"   Download: cropmd_model.keras + class_names.json")
print(f"   Test accuracy: {test_acc:.4f}")
