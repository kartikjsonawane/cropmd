"""
CropMD – Full Training Script
Two-phase training: frozen base → fine-tuned top layers
Run: python train.py --data_dir /path/to/PlantVillage --epochs 30
"""

import os
import sys
import argparse
import logging
import json
from datetime import datetime
from pathlib import Path

import tensorflow as tf
import numpy as np

# Local imports
sys.path.insert(0, str(Path(__file__).parent))
from model import (
    build_resnet50_model, compile_model, get_callbacks,
    unfreeze_top_layers, NUM_CLASSES, CLASS_NAMES
)
from data_processing import build_datasets, compute_dataset_stats
from evaluate import evaluate_model, save_evaluation_report

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("CropMD.train")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="CropMD Training Script")
    p.add_argument("--data_dir", required=True, help="Path to PlantVillage dataset root")
    p.add_argument("--output_dir", default="outputs", help="Where to save model + reports")
    p.add_argument("--epochs_phase1", type=int, default=20, help="Epochs with frozen base")
    p.add_argument("--epochs_phase2", type=int, default=15, help="Epochs for fine-tuning")
    p.add_argument("--batch_size", type=int, default=32)
    p.add_argument("--lr_phase1", type=float, default=1e-3)
    p.add_argument("--lr_phase2", type=float, default=1e-4)
    p.add_argument("--unfreeze_layers", type=int, default=30, help="Top N ResNet layers to unfreeze")
    p.add_argument("--dropout", type=float, default=0.4)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--mixed_precision", action="store_true", help="Use fp16 mixed precision")
    p.add_argument("--export_tflite", action="store_true", help="Export TFLite model")
    return p.parse_args()


def setup_gpu(mixed_precision: bool) -> None:
    gpus = tf.config.list_physical_devices("GPU")
    if gpus:
        for gpu in gpus:
            tf.config.experimental.set_memory_growth(gpu, True)
        logger.info(f"Using {len(gpus)} GPU(s)")
    else:
        logger.warning("No GPU found – training on CPU (slow)")

    if mixed_precision:
        tf.keras.mixed_precision.set_global_policy("mixed_float16")
        logger.info("Mixed precision (fp16) enabled")


def train(args: argparse.Namespace) -> None:
    tf.random.set_seed(args.seed)
    np.random.seed(args.seed)

    setup_gpu(args.mixed_precision)

    output_dir = Path(args.output_dir)
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = output_dir / run_id
    checkpoint_dir = run_dir / "checkpoints"
    log_dir = run_dir / "logs"
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)

    # ── Dataset Stats ────────────────────────────────────────────────────────
    logger.info("Computing dataset statistics …")
    stats_df = compute_dataset_stats(args.data_dir)
    stats_df.to_csv(run_dir / "dataset_stats.csv", index=False)

    # ── Build Datasets ───────────────────────────────────────────────────────
    logger.info("Building tf.data pipelines …")
    train_ds, val_ds, test_ds, class_weights = build_datasets(
        data_dir=args.data_dir,
        batch_size=args.batch_size,
        seed=args.seed,
    )

    # ── Phase 1: Train Head Only ─────────────────────────────────────────────
    logger.info("=== Phase 1: Training classification head (frozen ResNet50) ===")
    model = build_resnet50_model(
        num_classes=NUM_CLASSES,
        freeze_base=True,
        dropout_rate=args.dropout,
    )
    model = compile_model(model, learning_rate=args.lr_phase1, fine_tune=False)
    model.summary(print_fn=logger.info)

    callbacks_p1 = get_callbacks(
        checkpoint_path=str(checkpoint_dir / "phase1_best.weights.h5"),
        log_dir=str(log_dir / "phase1"),
        patience=8,
    )

    history_p1 = model.fit(
        train_ds,
        epochs=args.epochs_phase1,
        validation_data=val_ds,
        class_weight=class_weights,
        callbacks=callbacks_p1,
    )

    p1_val_acc = max(history_p1.history["val_accuracy"])
    logger.info(f"Phase 1 best val accuracy: {p1_val_acc:.4f}")

    # ── Phase 2: Fine-Tune Top Layers ────────────────────────────────────────
    logger.info(f"=== Phase 2: Fine-tuning top {args.unfreeze_layers} ResNet50 layers ===")
    model = unfreeze_top_layers(model, num_layers=args.unfreeze_layers)
    model = compile_model(model, learning_rate=args.lr_phase2, fine_tune=True)

    callbacks_p2 = get_callbacks(
        checkpoint_path=str(checkpoint_dir / "phase2_best.weights.h5"),
        log_dir=str(log_dir / "phase2"),
        patience=7,
    )

    history_p2 = model.fit(
        train_ds,
        epochs=args.epochs_phase2,
        validation_data=val_ds,
        class_weight=class_weights,
        callbacks=callbacks_p2,
        initial_epoch=len(history_p1.history["val_accuracy"]),
    )

    p2_val_acc = max(history_p2.history["val_accuracy"])
    logger.info(f"Phase 2 best val accuracy: {p2_val_acc:.4f}")

    # ── Evaluation ───────────────────────────────────────────────────────────
    logger.info("Running final evaluation on test set …")
    eval_results = evaluate_model(model, test_ds, CLASS_NAMES, run_dir)
    logger.info(f"Test accuracy: {eval_results['accuracy']:.4f}")
    logger.info(f"Macro F1:      {eval_results['macro_f1']:.4f}")

    # ── Save Final Model ─────────────────────────────────────────────────────
    final_model_path = run_dir / "cropmd_model.keras"
    model.save(str(final_model_path), save_format="keras")
    logger.info(f"Model saved → {final_model_path}")

    # Save class names alongside model
    with open(run_dir / "class_names.json", "w") as f:
        json.dump(CLASS_NAMES, f, indent=2)

    # Save training config
    config = {
        "run_id": run_id,
        "num_classes": NUM_CLASSES,
        "image_size": [224, 224],
        "batch_size": args.batch_size,
        "epochs_phase1": args.epochs_phase1,
        "epochs_phase2": args.epochs_phase2,
        "lr_phase1": args.lr_phase1,
        "lr_phase2": args.lr_phase2,
        "phase1_best_val_acc": float(p1_val_acc),
        "phase2_best_val_acc": float(p2_val_acc),
        "test_accuracy": float(eval_results["accuracy"]),
        "macro_f1": float(eval_results["macro_f1"]),
    }
    with open(run_dir / "training_config.json", "w") as f:
        json.dump(config, f, indent=2)

    # ── Optional TFLite Export ────────────────────────────────────────────────
    if args.export_tflite:
        logger.info("Exporting TFLite model for edge deployment …")
        export_tflite(model, run_dir / "cropmd_model.tflite")

    logger.info(f"\n✅ Training complete. Artifacts saved to: {run_dir}")
    logger.info(f"   Final test accuracy: {eval_results['accuracy']:.4f}")


def export_tflite(model: tf.keras.Model, output_path: Path) -> None:
    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    converter.target_spec.supported_types = [tf.float16]
    tflite_model = converter.convert()
    with open(output_path, "wb") as f:
        f.write(tflite_model)
    logger.info(f"TFLite model saved → {output_path} ({len(tflite_model) / 1e6:.1f} MB)")


if __name__ == "__main__":
    args = parse_args()
    train(args)
