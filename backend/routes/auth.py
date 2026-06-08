"""
CropMD – Authentication Routes
POST /api/auth/register
POST /api/auth/login
POST /api/auth/refresh
POST /api/auth/logout
GET  /api/auth/me
PUT  /api/auth/me
"""

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import (
    create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity, get_jwt
)
from bson import ObjectId
from datetime import datetime

from models.user import (
    create_user_document, verify_password, serialize_user,
    USERS_COLLECTION
)

auth_bp = Blueprint("auth", __name__)

# ── Register ──────────────────────────────────────────────────────────────────

@auth_bp.post("/register")
def register():
    data = request.get_json(silent=True) or {}
    required = ["email", "password", "name"]
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    db = current_app.db
    if db[USERS_COLLECTION].find_one({"email": data["email"].lower().strip()}):
        return jsonify({"error": "Email already registered"}), 409

    try:
        user_doc = create_user_document(
            email=data["email"],
            password=data["password"],
            name=data["name"],
            role=data.get("role", "farmer"),
            phone=data.get("phone"),
            location=data.get("location"),
        )
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    result = db[USERS_COLLECTION].insert_one(user_doc)
    user_doc["_id"] = result.inserted_id

    access_token = create_access_token(identity=str(result.inserted_id))
    refresh_token = create_refresh_token(identity=str(result.inserted_id))

    return jsonify({
        "message": "Registration successful",
        "user": serialize_user(user_doc),
        "access_token": access_token,
        "refresh_token": refresh_token,
    }), 201


# ── Login ─────────────────────────────────────────────────────────────────────

@auth_bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    email = data.get("email", "").lower().strip()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({"error": "Email and password required"}), 400

    db = current_app.db
    user = db[USERS_COLLECTION].find_one({"email": email})

    if not user or not verify_password(user["password_hash"], password):
        return jsonify({"error": "Invalid email or password"}), 401

    if not user.get("is_active", True):
        return jsonify({"error": "Account is deactivated"}), 403

    # Update last_login
    db[USERS_COLLECTION].update_one(
        {"_id": user["_id"]},
        {"$set": {"last_login": datetime.utcnow()}},
    )

    access_token = create_access_token(identity=str(user["_id"]))
    refresh_token = create_refresh_token(identity=str(user["_id"]))

    return jsonify({
        "message": "Login successful",
        "user": serialize_user(user),
        "access_token": access_token,
        "refresh_token": refresh_token,
    })


# ── Refresh ───────────────────────────────────────────────────────────────────

@auth_bp.post("/refresh")
@jwt_required(refresh=True)
def refresh():
    identity = get_jwt_identity()
    access_token = create_access_token(identity=identity)
    return jsonify({"access_token": access_token})


# ── Me (GET) ──────────────────────────────────────────────────────────────────

@auth_bp.get("/me")
@jwt_required()
def get_me():
    user_id = get_jwt_identity()
    db = current_app.db
    user = db[USERS_COLLECTION].find_one({"_id": ObjectId(user_id)})
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify({"user": serialize_user(user)})


# ── Me (PUT) ──────────────────────────────────────────────────────────────────

@auth_bp.put("/me")
@jwt_required()
def update_me():
    user_id = get_jwt_identity()
    data = request.get_json(silent=True) or {}

    allowed_fields = {"name", "phone", "location", "language", "profile_image"}
    updates = {k: v for k, v in data.items() if k in allowed_fields}

    if not updates:
        return jsonify({"error": "No valid fields to update"}), 400

    updates["updated_at"] = datetime.utcnow()
    db = current_app.db
    db[USERS_COLLECTION].update_one(
        {"_id": ObjectId(user_id)},
        {"$set": updates},
    )
    user = db[USERS_COLLECTION].find_one({"_id": ObjectId(user_id)})
    return jsonify({"message": "Profile updated", "user": serialize_user(user)})
