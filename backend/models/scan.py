"""
CropMD – Scan & Disease MongoDB Schemas
"""

from datetime import datetime
from bson import ObjectId
from typing import Dict, Any, Optional, List


SCANS_COLLECTION = "scans"
DISEASES_COLLECTION = "diseases"


# ── Scan Document ─────────────────────────────────────────────────────────────

def create_scan_document(
    user_id: str,
    farm_id: Optional[str],
    image_url: str,
    image_key: str,
    prediction: Dict,
    location: Optional[Dict] = None,
    notes: Optional[str] = None,
) -> Dict[str, Any]:
    """
    prediction = {
        disease_name, crop_name, confidence, severity,
        top_predictions: [{class_name, confidence}],
        is_healthy: bool
    }
    """
    return {
        "user_id": ObjectId(user_id),
        "farm_id": ObjectId(farm_id) if farm_id else None,
        "image_url": image_url,
        "image_key": image_key,             # Cloud storage key for deletion
        "prediction": {
            "disease_name": prediction.get("disease_name"),
            "crop_name": prediction.get("crop_name"),
            "confidence": prediction.get("confidence"),
            "severity": prediction.get("severity"),          # High / Medium / Low
            "is_healthy": prediction.get("is_healthy", False),
            "top_predictions": prediction.get("top_predictions", []),
        },
        "advisory": prediction.get("advisory", {}),          # AI-generated advice
        "location": location or {},                           # GPS if available
        "notes": notes,
        "status": "active",                                  # active | resolved | archived
        "viewed": False,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }


def serialize_scan(scan: Dict) -> Dict:
    return {
        "id": str(scan["_id"]),
        "user_id": str(scan["user_id"]),
        "farm_id": str(scan["farm_id"]) if scan.get("farm_id") else None,
        "image_url": scan["image_url"],
        "prediction": scan.get("prediction", {}),
        "advisory": scan.get("advisory", {}),
        "location": scan.get("location", {}),
        "notes": scan.get("notes"),
        "status": scan.get("status", "active"),
        "created_at": scan["created_at"].isoformat(),
    }


# ── Disease Knowledge Base Document ──────────────────────────────────────────

def create_disease_document(
    class_name: str,
    crop: str,
    disease: str,
    description: str,
    symptoms: List[str],
    causes: List[str],
    treatments: List[Dict],        # [{name, dosage, frequency, notes}]
    pesticides: List[Dict],        # [{name, type, active_ingredient, dosage}]
    prevention: List[str],
    fertilizer_tips: List[str],
    irrigation_tips: str,
    severity_default: str = "Medium",
) -> Dict[str, Any]:
    return {
        "class_name": class_name,
        "crop": crop,
        "disease": disease,
        "description": description,
        "symptoms": symptoms,
        "causes": causes,
        "treatments": treatments,
        "pesticides": pesticides,
        "prevention": prevention,
        "fertilizer_tips": fertilizer_tips,
        "irrigation_tips": irrigation_tips,
        "severity_default": severity_default,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }
