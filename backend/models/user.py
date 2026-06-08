"""
CropMD – User & Farm MongoDB Schemas (using pymongo + marshmallow-style helpers)
"""

from datetime import datetime
from bson import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
from typing import Optional, Dict, Any
import re


# ── MongoDB Collection Names ──────────────────────────────────────────────────
USERS_COLLECTION = "users"
FARMS_COLLECTION = "farms"


# ── User Schema ───────────────────────────────────────────────────────────────

def create_user_document(
    email: str,
    password: str,
    name: str,
    role: str = "farmer",
    phone: Optional[str] = None,
    location: Optional[Dict] = None,
) -> Dict[str, Any]:
    """Return a new user document ready for insertion."""
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        raise ValueError("Invalid email address")
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters")

    return {
        "email": email.lower().strip(),
        "password_hash": generate_password_hash(password),
        "name": name.strip(),
        "role": role,                          # "farmer" | "admin" | "agronomist"
        "phone": phone,
        "location": location or {},            # {country, state, city, lat, lng}
        "profile_image": None,
        "language": "en",
        "is_active": True,
        "is_verified": False,
        "last_login": None,
        "scan_count": 0,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }


def verify_password(password_hash: str, password: str) -> bool:
    return check_password_hash(password_hash, password)


def serialize_user(user: Dict) -> Dict:
    """Strip sensitive fields for API response."""
    return {
        "id": str(user["_id"]),
        "email": user["email"],
        "name": user["name"],
        "role": user["role"],
        "phone": user.get("phone"),
        "location": user.get("location", {}),
        "profile_image": user.get("profile_image"),
        "language": user.get("language", "en"),
        "scan_count": user.get("scan_count", 0),
        "created_at": user["created_at"].isoformat(),
    }


# ── Farm Schema ───────────────────────────────────────────────────────────────

def create_farm_document(
    owner_id: str,
    name: str,
    location: Dict,
    area_acres: float,
    crops: list,
    soil_type: Optional[str] = None,
    irrigation_type: Optional[str] = None,
) -> Dict[str, Any]:
    return {
        "owner_id": ObjectId(owner_id),
        "name": name,
        "location": location,               # {lat, lng, address, state, country}
        "area_acres": area_acres,
        "crops": crops,                     # ["Tomato", "Potato", ...]
        "soil_type": soil_type,             # "Clay" | "Sandy" | "Loam" | ...
        "irrigation_type": irrigation_type, # "Drip" | "Sprinkler" | "Flood" | ...
        "health_score": 100.0,             # 0–100, updated on each scan
        "total_scans": 0,
        "active_diseases": [],
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }


def serialize_farm(farm: Dict) -> Dict:
    return {
        "id": str(farm["_id"]),
        "owner_id": str(farm["owner_id"]),
        "name": farm["name"],
        "location": farm.get("location", {}),
        "area_acres": farm.get("area_acres"),
        "crops": farm.get("crops", []),
        "soil_type": farm.get("soil_type"),
        "irrigation_type": farm.get("irrigation_type"),
        "health_score": farm.get("health_score", 100.0),
        "total_scans": farm.get("total_scans", 0),
        "active_diseases": farm.get("active_diseases", []),
        "created_at": farm["created_at"].isoformat(),
    }
