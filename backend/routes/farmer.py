"""
CropMD – Farmer Profile & Farm Management Routes
GET  /api/farmer/profile
PUT  /api/farmer/profile
GET  /api/farmer/farms
POST /api/farmer/farms
GET  /api/farmer/farms/<farm_id>
PUT  /api/farmer/farms/<farm_id>
DELETE /api/farmer/farms/<farm_id>
"""

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson import ObjectId
from datetime import datetime

from models.user import USERS_COLLECTION, serialize_user
from models.user import create_farm_document, serialize_farm, FARMS_COLLECTION

farmer_bp = Blueprint("farmer", __name__)


@farmer_bp.get("/profile")
@jwt_required()
def get_profile():
    user_id = get_jwt_identity()
    db = current_app.db
    user = db[USERS_COLLECTION].find_one({"_id": ObjectId(user_id)})
    if not user:
        return jsonify({"error": "User not found"}), 404

    farms = list(db[FARMS_COLLECTION].find({"owner_id": ObjectId(user_id)}))
    return jsonify({
        "user": serialize_user(user),
        "farms": [serialize_farm(f) for f in farms],
        "farm_count": len(farms),
    })


@farmer_bp.get("/farms")
@jwt_required()
def list_farms():
    user_id = get_jwt_identity()
    db = current_app.db
    farms = list(db[FARMS_COLLECTION].find({"owner_id": ObjectId(user_id)}))
    return jsonify({"farms": [serialize_farm(f) for f in farms]})


@farmer_bp.post("/farms")
@jwt_required()
def create_farm():
    user_id = get_jwt_identity()
    data = request.get_json(silent=True) or {}
    required = ["name", "location", "area_acres", "crops"]
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    doc = create_farm_document(
        owner_id=user_id,
        name=data["name"],
        location=data["location"],
        area_acres=float(data["area_acres"]),
        crops=data["crops"],
        soil_type=data.get("soil_type"),
        irrigation_type=data.get("irrigation_type"),
    )
    db = current_app.db
    result = db[FARMS_COLLECTION].insert_one(doc)
    doc["_id"] = result.inserted_id
    return jsonify({"message": "Farm created", "farm": serialize_farm(doc)}), 201


@farmer_bp.get("/farms/<farm_id>")
@jwt_required()
def get_farm(farm_id: str):
    user_id = get_jwt_identity()
    db = current_app.db
    farm = db[FARMS_COLLECTION].find_one({
        "_id": ObjectId(farm_id),
        "owner_id": ObjectId(user_id),
    })
    if not farm:
        return jsonify({"error": "Farm not found"}), 404

    # Latest 5 scans for this farm
    from models.scan import SCANS_COLLECTION, serialize_scan
    scans = list(
        db[SCANS_COLLECTION]
        .find({"farm_id": ObjectId(farm_id)})
        .sort("created_at", -1)
        .limit(5)
    )
    return jsonify({
        "farm": serialize_farm(farm),
        "recent_scans": [serialize_scan(s) for s in scans],
    })


@farmer_bp.put("/farms/<farm_id>")
@jwt_required()
def update_farm(farm_id: str):
    user_id = get_jwt_identity()
    data = request.get_json(silent=True) or {}
    allowed = {"name", "location", "area_acres", "crops", "soil_type", "irrigation_type"}
    updates = {k: v for k, v in data.items() if k in allowed}
    if not updates:
        return jsonify({"error": "No valid fields to update"}), 400

    updates["updated_at"] = datetime.utcnow()
    db = current_app.db
    result = db[FARMS_COLLECTION].update_one(
        {"_id": ObjectId(farm_id), "owner_id": ObjectId(user_id)},
        {"$set": updates},
    )
    if result.matched_count == 0:
        return jsonify({"error": "Farm not found"}), 404

    farm = db[FARMS_COLLECTION].find_one({"_id": ObjectId(farm_id)})
    return jsonify({"message": "Farm updated", "farm": serialize_farm(farm)})


@farmer_bp.delete("/farms/<farm_id>")
@jwt_required()
def delete_farm(farm_id: str):
    user_id = get_jwt_identity()
    db = current_app.db
    result = db[FARMS_COLLECTION].delete_one({
        "_id": ObjectId(farm_id),
        "owner_id": ObjectId(user_id),
    })
    if result.deleted_count == 0:
        return jsonify({"error": "Farm not found"}), 404
    return jsonify({"message": "Farm deleted"})
