"""
CropMD – Analytics Routes
GET /api/analytics/dashboard    – Overall platform analytics
GET /api/analytics/trends       – Disease trends over time
GET /api/analytics/heatmap      – Geographic disease heatmap data
GET /api/analytics/crop-health  – Per-crop health breakdown
"""

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request
from bson import ObjectId
from datetime import datetime, timedelta

from models.scan import SCANS_COLLECTION
from models.user import USERS_COLLECTION

analytics_bp = Blueprint("analytics", __name__)


@analytics_bp.get("/dashboard")
@jwt_required()
def dashboard():
    user_id = get_jwt_identity()
    db = current_app.db
    days = int(request.args.get("days", 30))
    since = datetime.utcnow() - timedelta(days=days)

    match = {"user_id": ObjectId(user_id), "created_at": {"$gte": since}}

    # Summary counts
    total = db[SCANS_COLLECTION].count_documents({"user_id": ObjectId(user_id)})
    recent_total = db[SCANS_COLLECTION].count_documents(match)
    healthy = db[SCANS_COLLECTION].count_documents({**match, "prediction.is_healthy": True})
    diseased = recent_total - healthy

    # Severity breakdown
    sev_pipeline = [
        {"$match": match},
        {"$group": {"_id": "$prediction.severity", "count": {"$sum": 1}}},
    ]
    severity = {r["_id"]: r["count"] for r in db[SCANS_COLLECTION].aggregate(sev_pipeline)}

    # Top crops scanned
    crop_pipeline = [
        {"$match": {"user_id": ObjectId(user_id)}},
        {"$group": {"_id": "$prediction.crop_name", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 6},
    ]
    top_crops = [{"crop": r["_id"], "count": r["count"]}
                 for r in db[SCANS_COLLECTION].aggregate(crop_pipeline)]

    # Top diseases
    disease_pipeline = [
        {"$match": {"user_id": ObjectId(user_id), "prediction.is_healthy": False}},
        {"$group": {"_id": "$prediction.disease_name", "count": {"$sum": 1},
                    "crop": {"$first": "$prediction.crop_name"}}},
        {"$sort": {"count": -1}},
        {"$limit": 5},
    ]
    top_diseases = [
        {"disease": r["_id"], "crop": r["crop"], "count": r["count"]}
        for r in db[SCANS_COLLECTION].aggregate(disease_pipeline)
    ]

    return jsonify({
        "period_days": days,
        "total_scans": total,
        "recent_scans": recent_total,
        "healthy": healthy,
        "diseased": diseased,
        "health_rate": round(healthy / recent_total * 100, 1) if recent_total else 100.0,
        "severity_breakdown": severity,
        "top_crops": top_crops,
        "top_diseases": top_diseases,
    })


@analytics_bp.get("/trends")
@jwt_required()
def trends():
    user_id = get_jwt_identity()
    db = current_app.db
    days = int(request.args.get("days", 30))
    since = datetime.utcnow() - timedelta(days=days)

    pipeline = [
        {"$match": {"user_id": ObjectId(user_id), "created_at": {"$gte": since}}},
        {"$group": {
            "_id": {
                "date": {"$dateToString": {"format": "%Y-%m-%d", "date": "$created_at"}},
                "is_healthy": "$prediction.is_healthy",
            },
            "count": {"$sum": 1},
        }},
        {"$sort": {"_id.date": 1}},
    ]
    raw = list(db[SCANS_COLLECTION].aggregate(pipeline))

    # Pivot into {date, healthy, diseased}
    day_map: dict = {}
    for r in raw:
        date = r["_id"]["date"]
        if date not in day_map:
            day_map[date] = {"date": date, "healthy": 0, "diseased": 0, "total": 0}
        if r["_id"]["is_healthy"]:
            day_map[date]["healthy"] += r["count"]
        else:
            day_map[date]["diseased"] += r["count"]
        day_map[date]["total"] += r["count"]

    return jsonify({"trends": list(day_map.values())})


@analytics_bp.get("/heatmap")
@jwt_required()
def heatmap():
    """Return geographic disease hotspot data for map visualization."""
    user_id = get_jwt_identity()
    db = current_app.db

    pipeline = [
        {"$match": {
            "user_id": ObjectId(user_id),
            "prediction.is_healthy": False,
            "location.lat": {"$exists": True},
        }},
        {"$project": {
            "lat": "$location.lat",
            "lng": "$location.lng",
            "disease": "$prediction.disease_name",
            "severity": "$prediction.severity",
            "created_at": 1,
        }},
        {"$sort": {"created_at": -1}},
        {"$limit": 500},
    ]
    points = [
        {
            "lat": r["lat"],
            "lng": r["lng"],
            "disease": r.get("disease"),
            "severity": r.get("severity"),
            "weight": {"High": 1.0, "Medium": 0.6, "Low": 0.3}.get(r.get("severity"), 0.5),
        }
        for r in db[SCANS_COLLECTION].aggregate(pipeline)
    ]
    return jsonify({"points": points})


@analytics_bp.get("/crop-health")
@jwt_required()
def crop_health():
    user_id = get_jwt_identity()
    db = current_app.db

    pipeline = [
        {"$match": {"user_id": ObjectId(user_id)}},
        {"$group": {
            "_id": "$prediction.crop_name",
            "total": {"$sum": 1},
            "healthy": {"$sum": {"$cond": ["$prediction.is_healthy", 1, 0]}},
            "last_scan": {"$max": "$created_at"},
        }},
        {"$project": {
            "crop": "$_id",
            "total": 1,
            "healthy": 1,
            "diseased": {"$subtract": ["$total", "$healthy"]},
            "health_pct": {
                "$multiply": [{"$divide": ["$healthy", "$total"]}, 100]
            },
            "last_scan": 1,
        }},
        {"$sort": {"health_pct": 1}},
    ]
    results = list(db[SCANS_COLLECTION].aggregate(pipeline))
    for r in results:
        r.pop("_id", None)
        if r.get("last_scan"):
            r["last_scan"] = r["last_scan"].isoformat()

    return jsonify({"crop_health": results})
