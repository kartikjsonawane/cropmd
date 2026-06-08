"""
CropMD – Inference Engine
Loads trained ResNet-50 model and runs predictions on uploaded images.
"""

import json
import logging
import io
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import tensorflow as tf
from PIL import Image

logger = logging.getLogger(__name__)

IMAGE_SIZE = (224, 224)

HEALTHY_KEYWORDS = {"healthy"}


class CropMDPredictor:
    """Thread-safe inference wrapper around the saved Keras model."""

    def __init__(self, model_path: str, class_names_path: str):
        self.model: Optional[tf.keras.Model] = None
        self.class_names: List[str] = []
        self._load(model_path, class_names_path)

    def _load(self, model_path: str, class_names_path: str) -> None:
        mp = Path(model_path)
        cp = Path(class_names_path)

        if not mp.exists():
            logger.warning(
                f"Model not found at {mp}. "
                "Predictions will return mock data until the model is trained."
            )
            self._load_class_names(cp)
            return

        logger.info(f"Loading model from {mp} …")
        self.model = tf.keras.models.load_model(str(mp))
        self._load_class_names(cp)
        logger.info("Model loaded successfully")

    def _load_class_names(self, class_names_path: Path) -> None:
        if class_names_path.exists():
            with open(class_names_path) as f:
                self.class_names = json.load(f)
        else:
            # Fallback to built-in list
            from sys import path as syspath
            import os
            syspath.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "ml"))
            try:
                from model import CLASS_NAMES
                self.class_names = CLASS_NAMES
            except ImportError:
                self.class_names = []

    def _preprocess(self, image_bytes: bytes) -> np.ndarray:
        """Convert raw bytes → (1, 224, 224, 3) float32 numpy array."""
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        img = img.resize(IMAGE_SIZE, Image.LANCZOS)
        arr = np.array(img, dtype=np.float32)
        # Apply ResNet50 preprocessing (same as training)
        arr = tf.keras.applications.resnet50.preprocess_input(arr)
        return np.expand_dims(arr, axis=0)

    def predict(self, image_bytes: bytes, top_k: int = 5) -> Dict:
        """
        Returns:
        {
            class_name, crop_name, disease_name, confidence,
            severity, is_healthy, top_predictions
        }
        """
        if self.model is None:
            return self._mock_prediction()

        input_arr = self._preprocess(image_bytes)
        probs = self.model.predict(input_arr, verbose=0)[0]  # shape (38,)

        top_indices = np.argsort(probs)[::-1][:top_k]
        top_predictions = [
            {
                "class_name": self.class_names[i],
                "confidence": float(probs[i]),
                **self._parse_class(self.class_names[i]),
            }
            for i in top_indices
        ]

        best_idx = top_indices[0]
        best_class = self.class_names[best_idx]
        best_conf = float(probs[best_idx])

        parsed = self._parse_class(best_class)
        is_healthy = "healthy" in parsed["disease_name"].lower()

        return {
            "class_name": best_class,
            "crop_name": parsed["crop_name"],
            "disease_name": parsed["disease_name"],
            "confidence": best_conf,
            "confidence_pct": round(best_conf * 100, 2),
            "severity": self._get_severity(best_conf, is_healthy),
            "is_healthy": is_healthy,
            "top_predictions": top_predictions,
        }

    def _parse_class(self, class_name: str) -> Dict[str, str]:
        parts = class_name.split("___")
        crop = parts[0].replace("_", " ").replace(",", "").strip()
        disease = parts[1].replace("_", " ").strip() if len(parts) > 1 else "Unknown"
        return {"crop_name": crop, "disease_name": disease}

    def _get_severity(self, confidence: float, is_healthy: bool) -> str:
        if is_healthy:
            return "None"
        if confidence >= 0.85:
            return "High"
        elif confidence >= 0.60:
            return "Medium"
        return "Low"

    def _mock_prediction(self) -> Dict:
        """Return realistic mock data when model file is missing (dev mode)."""
        return {
            "class_name": "Tomato___Early_blight",
            "crop_name": "Tomato",
            "disease_name": "Early blight",
            "confidence": 0.912,
            "confidence_pct": 91.2,
            "severity": "High",
            "is_healthy": False,
            "top_predictions": [
                {"class_name": "Tomato___Early_blight", "crop_name": "Tomato",
                 "disease_name": "Early blight", "confidence": 0.912},
                {"class_name": "Tomato___Late_blight", "crop_name": "Tomato",
                 "disease_name": "Late blight", "confidence": 0.054},
                {"class_name": "Tomato___healthy", "crop_name": "Tomato",
                 "disease_name": "healthy", "confidence": 0.018},
            ],
        }
