"""
CropMD – Admin Routes (role: admin only)
GET  /api/admin/stats         – Platform-wide statistics
GET  /api/admin/users         – List all users
PUT  /api/admin/users/<id>    – Update user (activate/deactivate, change role)
GET  /api/admin/scans         – All scans with filters
POST /api/admin/seed-diseases – Seed disease knowledge base
GET  /api/admin/disease-db    – View disease KB
"""

import functools
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson import ObjectId
from datetime import datetime, timedelta

from models.user import USERS_COLLECTION, serialize_user
from models.scan import SCANS_COLLECTION, serialize_scan
from ml.disease_kb import DISEASE_KB, get_advisory

admin_bp = Blueprint("admin", __name__)


def admin_required(fn):
    @functools.wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        user_id = get_jwt_identity()
        db = current_app.db
        user = db[USERS_COLLECTION].find_one({"_id": ObjectId(user_id)})
        if not user or user.get("role") != "admin":
            return jsonify({"error": "Admin access required"}), 403
        return fn(*args, **kwargs)
    return wrapper


@admin_bp.get("/stats")
@admin_required
def platform_stats():
    db = current_app.db
    total_users = db[USERS_COLLECTION].count_documents({})
    total_scans = db[SCANS_COLLECTION].count_documents({})
    total_diseases = db[SCANS_COLLECTION].count_documents({"prediction.is_healthy": False})

    # Last 7 days signups
    week_ago = datetime.utcnow() - timedelta(days=7)
    new_users = db[USERS_COLLECTION].count_documents({"created_at": {"$gte": week_ago}})
    new_scans = db[SCANS_COLLECTION].count_documents({"created_at": {"$gte": week_ago}})

    # Top diseases globally
    pipeline = [
        {"$match": {"prediction.is_healthy": False}},
        {"$group": {"_id": "$prediction.disease_name", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10},
    ]
    top_diseases = [{"disease": r["_id"], "count": r["count"]}
                    for r in db[SCANS_COLLECTION].aggregate(pipeline)]

    return jsonify({
        "total_users": total_users,
        "total_scans": total_scans,
        "total_disease_detections": total_diseases,
        "new_users_7d": new_users,
        "new_scans_7d": new_scans,
        "health_rate": round((total_scans - total_diseases) / total_scans * 100, 1) if total_scans else 100.0,
        "top_diseases": top_diseases,
    })


@admin_bp.get("/users")
@admin_required
def list_users():
    db = current_app.db
    page = int(request.args.get("page", 1))
    limit = min(int(request.args.get("limit", 20)), 100)
    skip = (page - 1) * limit
    search = request.args.get("search", "")
    role = request.args.get("role", "")

    query = {}
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"email": {"$regex": search, "$options": "i"}},
        ]
    if role:
        query["role"] = role

    total = db[USERS_COLLECTION].count_documents(query)
    users = list(db[USERS_COLLECTION].find(query).sort("created_at", -1).skip(skip).limit(limit))
    return jsonify({
        "users": [serialize_user(u) for u in users],
        "total": total,
        "page": page,
        "pages": -(-total // limit),
    })


@admin_bp.put("/users/<user_id>")
@admin_required
def update_user(user_id: str):
    data = request.get_json(silent=True) or {}
    allowed = {"role", "is_active", "is_verified"}
    updates = {k: v for k, v in data.items() if k in allowed}
    if not updates:
        return jsonify({"error": "No valid fields"}), 400

    updates["updated_at"] = datetime.utcnow()
    db = current_app.db
    db[USERS_COLLECTION].update_one({"_id": ObjectId(user_id)}, {"$set": updates})
    user = db[USERS_COLLECTION].find_one({"_id": ObjectId(user_id)})
    return jsonify({"message": "User updated", "user": serialize_user(user)})


@admin_bp.get("/scans")
@admin_required
def all_scans():
    db = current_app.db
    page = int(request.args.get("page", 1))
    limit = min(int(request.args.get("limit", 20)), 100)
    skip = (page - 1) * limit
    total = db[SCANS_COLLECTION].count_documents({})
    scans = list(db[SCANS_COLLECTION].find().sort("created_at", -1).skip(skip).limit(limit))
    return jsonify({
        "scans": [serialize_scan(s) for s in scans],
        "total": total,
        "page": page,
        "pages": -(-total // limit),
    })


@admin_bp.post("/seed-diseases")
@admin_required
def seed_diseases():
    """Seed the disease knowledge base into MongoDB."""
    db = current_app.db
    seeded = 0
    for class_name, data in DISEASE_KB.items():
        db["diseases"].update_one(
            {"class_name": class_name},
            {"$set": {
                "class_name": class_name,
                **data,
                "updated_at": datetime.utcnow(),
            }},
            upsert=True,
        )
        seeded += 1
    return jsonify({"message": f"Seeded {seeded} disease records"})


@admin_bp.get("/disease-db")
@admin_required
def list_diseases():
    db = current_app.db
    diseases = list(db["diseases"].find({}, {"_id": 0}))
    return jsonify({"diseases": diseases, "total": len(diseases)})
