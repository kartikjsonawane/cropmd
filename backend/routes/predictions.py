"""
CropMD – Prediction Routes
POST /api/predictions/analyze          – Upload image & get prediction
GET  /api/predictions/history          – Get user's scan history
GET  /api/predictions/<scan_id>        – Get single scan detail
DELETE /api/predictions/<scan_id>      – Delete a scan
GET  /api/predictions/stats            – Aggregate stats for user
"""

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson import ObjectId
from datetime import datetime, timedelta

from models.scan import create_scan_document, serialize_scan, SCANS_COLLECTION
from models.user import USERS_COLLECTION
from ml.disease_kb import get_advisory
from utils.storage import upload_image, delete_image

predictions_bp = Blueprint("predictions", __name__)

ALLOWED_TYPES = {"image/jpeg", "image/jpg", "image/png", "image/webp"}
MAX_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB


# ── Analyze (Main Prediction Endpoint) ───────────────────────────────────────

@predictions_bp.post("/analyze")
@jwt_required()
def analyze():
    user_id = get_jwt_identity()

    if "image" not in request.files:
        return jsonify({"error": "No image file provided"}), 400

    file = request.files["image"]
    if not file.filename:
        return jsonify({"error": "Empty filename"}), 400
    if file.content_type not in ALLOWED_TYPES:
        return jsonify({"error": f"Unsupported file type: {file.content_type}"}), 415

    image_bytes = file.read()
    if len(image_bytes) > MAX_SIZE_BYTES:
        return jsonify({"error": "Image exceeds 10MB limit"}), 413

    # ── Run ML Prediction ────────────────────────────────────────────────────
    predictor = current_app.predictor
    prediction = predictor.predict(image_bytes)

    # ── Attach Advisory from Knowledge Base ──────────────────────────────────
    advisory = get_advisory(prediction["class_name"])

    full_prediction = {**prediction, "advisory": advisory}

    # ── Upload Image to Cloud Storage ─────────────────────────────────────────
    farm_id = request.form.get("farm_id")
    notes = request.form.get("notes")
    lat = request.form.get("lat")
    lng = request.form.get("lng")

    try:
        image_url, image_key = upload_image(
            image_bytes=image_bytes,
            filename=file.filename,
            user_id=user_id,
        )
    except Exception as e:
        current_app.logger.error(f"Image upload failed: {e}")
        image_url = ""
        image_key = ""

    # ── Save Scan to MongoDB ──────────────────────────────────────────────────
    location = {}
    if lat and lng:
        try:
            location = {"lat": float(lat), "lng": float(lng)}
        except ValueError:
            pass

    scan_doc = create_scan_document(
        user_id=user_id,
        farm_id=farm_id,
        image_url=image_url,
        image_key=image_key,
        prediction=full_prediction,
        location=location,
        notes=notes,
    )
    db = current_app.db
    result = db[SCANS_COLLECTION].insert_one(scan_doc)
    scan_doc["_id"] = result.inserted_id

    # Increment user scan count
    db[USERS_COLLECTION].update_one(
        {"_id": ObjectId(user_id)},
        {"$inc": {"scan_count": 1}},
    )

    # Update farm health score if farm_id provided
    if farm_id:
        _update_farm_health(db, farm_id, prediction)

    return jsonify({
        "scan_id": str(result.inserted_id),
        "prediction": prediction,
        "advisory": advisory,
        "image_url": image_url,
        "message": "Analysis complete",
    }), 201


# ── Scan History ──────────────────────────────────────────────────────────────

@predictions_bp.get("/history")
@jwt_required()
def get_history():
    user_id = get_jwt_identity()
    db = current_app.db

    page = int(request.args.get("page", 1))
    limit = min(int(request.args.get("limit", 20)), 100)
    skip = (page - 1) * limit

    # Optional filters
    crop = request.args.get("crop")
    status = request.args.get("status")
    from_date = request.args.get("from")
    to_date = request.args.get("to")

    query = {"user_id": ObjectId(user_id)}
    if crop:
        query["prediction.crop_name"] = {"$regex": crop, "$options": "i"}
    if status:
        query["status"] = status
    if from_date or to_date:
        date_filter = {}
        if from_date:
            date_filter["$gte"] = datetime.fromisoformat(from_date)
        if to_date:
            date_filter["$lte"] = datetime.fromisoformat(to_date)
        query["created_at"] = date_filter

    total = db[SCANS_COLLECTION].count_documents(query)
    scans = list(
        db[SCANS_COLLECTION]
        .find(query)
        .sort("created_at", -1)
        .skip(skip)
        .limit(limit)
    )

    return jsonify({
        "scans": [serialize_scan(s) for s in scans],
        "total": total,
        "page": page,
        "pages": -(-total // limit),
        "limit": limit,
    })


# ── Single Scan ───────────────────────────────────────────────────────────────

@predictions_bp.get("/<scan_id>")
@jwt_required()
def get_scan(scan_id: str):
    user_id = get_jwt_identity()
    db = current_app.db

    try:
        scan = db[SCANS_COLLECTION].find_one({
            "_id": ObjectId(scan_id),
            "user_id": ObjectId(user_id),
        })
    except Exception:
        return jsonify({"error": "Invalid scan ID"}), 400

    if not scan:
        return jsonify({"error": "Scan not found"}), 404

    # Mark as viewed
    db[SCANS_COLLECTION].update_one(
        {"_id": ObjectId(scan_id)},
        {"$set": {"viewed": True}},
    )
    return jsonify({"scan": serialize_scan(scan)})


# ── Delete Scan ───────────────────────────────────────────────────────────────

@predictions_bp.delete("/<scan_id>")
@jwt_required()
def delete_scan(scan_id: str):
    user_id = get_jwt_identity()
    db = current_app.db

    try:
        scan = db[SCANS_COLLECTION].find_one({
            "_id": ObjectId(scan_id),
            "user_id": ObjectId(user_id),
        })
    except Exception:
        return jsonify({"error": "Invalid scan ID"}), 400

    if not scan:
        return jsonify({"error": "Scan not found"}), 404

    # Delete image from cloud
    if scan.get("image_key"):
        delete_image(scan["image_key"])

    db[SCANS_COLLECTION].delete_one({"_id": ObjectId(scan_id)})
    return jsonify({"message": "Scan deleted"})


# ── User Stats ────────────────────────────────────────────────────────────────

@predictions_bp.get("/stats/summary")
@jwt_required()
def get_stats():
    user_id = get_jwt_identity()
    db = current_app.db

    pipeline = [
        {"$match": {"user_id": ObjectId(user_id)}},
        {"$group": {
            "_id": None,
            "total_scans": {"$sum": 1},
            "healthy_count": {
                "$sum": {"$cond": [{"$eq": ["$prediction.is_healthy", True]}, 1, 0]}
            },
            "disease_count": {
                "$sum": {"$cond": [{"$eq": ["$prediction.is_healthy", False]}, 1, 0]}
            },
        }},
    ]
    agg = list(db[SCANS_COLLECTION].aggregate(pipeline))
    stats = agg[0] if agg else {"total_scans": 0, "healthy_count": 0, "disease_count": 0}
    stats.pop("_id", None)

    # Disease frequency
    disease_pipeline = [
        {"$match": {"user_id": ObjectId(user_id), "prediction.is_healthy": False}},
        {"$group": {"_id": "$prediction.disease_name", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 5},
    ]
    top_diseases = [
        {"disease": d["_id"], "count": d["count"]}
        for d in db[SCANS_COLLECTION].aggregate(disease_pipeline)
    ]

    # Recent activity (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    recent_pipeline = [
        {"$match": {"user_id": ObjectId(user_id), "created_at": {"$gte": thirty_days_ago}}},
        {"$group": {
            "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$created_at"}},
            "count": {"$sum": 1},
        }},
        {"$sort": {"_id": 1}},
    ]
    recent = [{"date": r["_id"], "count": r["count"]}
              for r in db[SCANS_COLLECTION].aggregate(recent_pipeline)]

    return jsonify({
        **stats,
        "top_diseases": top_diseases,
        "recent_activity": recent,
        "health_rate": (
            round(stats["healthy_count"] / stats["total_scans"] * 100, 1)
            if stats["total_scans"] > 0 else 100.0
        ),
    })


# ── Helper ────────────────────────────────────────────────────────────────────

def _update_farm_health(db, farm_id: str, prediction: dict) -> None:
    """Adjust farm health score based on new scan."""
    try:
        from models.scan import SCANS_COLLECTION
        severity_penalty = {"High": 15, "Medium": 8, "Low": 3, "None": 0}
        delta = -severity_penalty.get(prediction.get("severity", "None"), 0)
        if prediction.get("is_healthy"):
            delta = +2  # Recover slowly when healthy

        db["farms"].update_one(
            {"_id": ObjectId(farm_id)},
            {
                "$inc": {"health_score": delta, "total_scans": 1},
                "$set": {"updated_at": datetime.utcnow()},
            },
        )
        # Clamp health_score to [0, 100]
        db["farms"].update_one(
            {"_id": ObjectId(farm_id), "health_score": {"$gt": 100}},
            {"$set": {"health_score": 100}},
        )
        db["farms"].update_one(
            {"_id": ObjectId(farm_id), "health_score": {"$lt": 0}},
            {"$set": {"health_score": 0}},
        )
    except Exception as e:
        current_app.logger.error(f"Farm health update failed: {e}")
