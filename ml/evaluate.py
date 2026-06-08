"""
CropMD – Model Evaluation
Generates accuracy, precision, recall, F1, confusion matrix, classification report
"""

import numpy as np
import tensorflow as tf
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    accuracy_score,
    precision_recall_fscore_support,
)
from pathlib import Path
from typing import Dict, List
import pandas as pd
import json
import logging

logger = logging.getLogger(__name__)


def evaluate_model(
    model: tf.keras.Model,
    test_ds: tf.data.Dataset,
    class_names: List[str],
    output_dir: Path,
) -> Dict:
    """Full evaluation suite — returns dict with all metrics."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Collecting predictions …")
    y_true, y_pred_probs = [], []

    for images, labels in test_ds:
        probs = model.predict(images, verbose=0)
        y_pred_probs.extend(probs)
        y_true.extend(np.argmax(labels.numpy(), axis=1))

    y_true = np.array(y_true)
    y_pred_probs = np.array(y_pred_probs)
    y_pred = np.argmax(y_pred_probs, axis=1)

    # ── Core Metrics ─────────────────────────────────────────────────────────
    acc = accuracy_score(y_true, y_pred)
    precision, recall, f1, support = precision_recall_fscore_support(
        y_true, y_pred, average=None, labels=list(range(len(class_names)))
    )
    macro_p, macro_r, macro_f1, _ = precision_recall_fscore_support(
        y_true, y_pred, average="macro"
    )
    weighted_p, weighted_r, weighted_f1, _ = precision_recall_fscore_support(
        y_true, y_pred, average="weighted"
    )

    # Top-3 accuracy
    top3_acc = top_k_accuracy(y_true, y_pred_probs, k=3)

    metrics = {
        "accuracy": float(acc),
        "top3_accuracy": float(top3_acc),
        "macro_precision": float(macro_p),
        "macro_recall": float(macro_r),
        "macro_f1": float(macro_f1),
        "weighted_precision": float(weighted_p),
        "weighted_recall": float(weighted_r),
        "weighted_f1": float(weighted_f1),
    }

    logger.info(f"Accuracy:        {acc:.4f}")
    logger.info(f"Top-3 Accuracy:  {top3_acc:.4f}")
    logger.info(f"Macro F1:        {macro_f1:.4f}")
    logger.info(f"Weighted F1:     {weighted_f1:.4f}")

    # ── Classification Report ─────────────────────────────────────────────────
    report_str = classification_report(
        y_true, y_pred, target_names=class_names, digits=4
    )
    report_path = output_dir / "classification_report.txt"
    with open(report_path, "w") as f:
        f.write(report_str)
    logger.info(f"\n{report_str}")

    # Per-class DataFrame
    per_class_df = pd.DataFrame({
        "class": class_names,
        "precision": precision,
        "recall": recall,
        "f1_score": f1,
        "support": support.astype(int),
    })
    per_class_df.to_csv(output_dir / "per_class_metrics.csv", index=False)

    # ── Confusion Matrix ──────────────────────────────────────────────────────
    cm = confusion_matrix(y_true, y_pred)
    plot_confusion_matrix(cm, class_names, output_dir / "confusion_matrix.png")

    # ── Metrics JSON ─────────────────────────────────────────────────────────
    with open(output_dir / "metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)

    # ── Per-class Bar Chart ───────────────────────────────────────────────────
    plot_per_class_f1(per_class_df, output_dir / "per_class_f1.png")

    save_evaluation_report(metrics, per_class_df, output_dir / "evaluation_report.md")

    return metrics


def top_k_accuracy(y_true: np.ndarray, y_probs: np.ndarray, k: int = 3) -> float:
    top_k_preds = np.argsort(y_probs, axis=1)[:, -k:]
    correct = sum(y_true[i] in top_k_preds[i] for i in range(len(y_true)))
    return correct / len(y_true)


def plot_confusion_matrix(
    cm: np.ndarray,
    class_names: List[str],
    save_path: Path,
    figsize: tuple = (22, 20),
) -> None:
    # Normalize
    cm_norm = cm.astype(float) / cm.sum(axis=1, keepdims=True)

    fig, ax = plt.subplots(figsize=figsize)
    sns.heatmap(
        cm_norm,
        annot=True,
        fmt=".2f",
        cmap="YlOrRd",
        xticklabels=class_names,
        yticklabels=class_names,
        ax=ax,
        linewidths=0.3,
    )
    ax.set_xlabel("Predicted Label", fontsize=12)
    ax.set_ylabel("True Label", fontsize=12)
    ax.set_title("CropMD – Normalized Confusion Matrix", fontsize=14, fontweight="bold")
    plt.xticks(rotation=45, ha="right", fontsize=7)
    plt.yticks(fontsize=7)
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close()
    logger.info(f"Confusion matrix saved → {save_path}")


def plot_per_class_f1(df: pd.DataFrame, save_path: Path) -> None:
    df_sorted = df.sort_values("f1_score", ascending=True)
    fig, ax = plt.subplots(figsize=(10, 14))
    colors = ["#e74c3c" if v < 0.90 else "#2ecc71" for v in df_sorted["f1_score"]]
    ax.barh(df_sorted["class"], df_sorted["f1_score"], color=colors)
    ax.axvline(0.94, color="navy", linestyle="--", label="Target (0.94)")
    ax.set_xlabel("F1 Score", fontsize=12)
    ax.set_title("CropMD – Per-Class F1 Score", fontsize=14, fontweight="bold")
    ax.legend()
    plt.tight_layout()
    plt.savefig(save_path, dpi=120, bbox_inches="tight")
    plt.close()
    logger.info(f"Per-class F1 chart saved → {save_path}")


def save_evaluation_report(
    metrics: Dict,
    per_class_df: pd.DataFrame,
    save_path: Path,
) -> None:
    md = f"""# CropMD – Model Evaluation Report

## Summary Metrics

| Metric | Value |
|---|---|
| **Accuracy** | {metrics['accuracy']:.4f} |
| **Top-3 Accuracy** | {metrics['top3_accuracy']:.4f} |
| **Macro Precision** | {metrics['macro_precision']:.4f} |
| **Macro Recall** | {metrics['macro_recall']:.4f} |
| **Macro F1** | {metrics['macro_f1']:.4f} |
| **Weighted F1** | {metrics['weighted_f1']:.4f} |

## Per-Class Metrics (Top 10 by F1)

{per_class_df.nlargest(10, 'f1_score').to_markdown(index=False)}

## Bottom 10 Classes (Lowest F1)

{per_class_df.nsmallest(10, 'f1_score').to_markdown(index=False)}
"""
    with open(save_path, "w") as f:
        f.write(md)
    logger.info(f"Evaluation report saved → {save_path}")
