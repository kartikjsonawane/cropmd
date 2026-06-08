"""
CropMD – Flask Application Factory
"""

from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from pymongo import MongoClient
from config import get_config
import logging

logger = logging.getLogger(__name__)

# ── Singletons ────────────────────────────────────────────────────────────────
jwt = JWTManager()
limiter = Limiter(key_func=get_remote_address)


def create_app() -> Flask:
    app = Flask(__name__)
    cfg = get_config()
    app.config.from_object(cfg)

    # ── Logging ───────────────────────────────────────────────────────────────
    logging.basicConfig(
        level=logging.DEBUG if cfg.DEBUG else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    # ── CORS ──────────────────────────────────────────────────────────────────
    CORS(app, resources={r"/api/*": {"origins": cfg.CORS_ORIGINS}},
         supports_credentials=True)

    # ── JWT ───────────────────────────────────────────────────────────────────
    jwt.init_app(app)

    # ── Rate Limiting ─────────────────────────────────────────────────────────
    limiter.init_app(app)

    # ── MongoDB ───────────────────────────────────────────────────────────────
    client = MongoClient(cfg.MONGO_URI)
    app.db = client[cfg.DB_NAME]
    logger.info(f"Connected to MongoDB: {cfg.DB_NAME}")

    # ── ML Model ─────────────────────────────────────────────────────────────
    from ml.predictor import CropMDPredictor
    app.predictor = CropMDPredictor(
        model_path=cfg.MODEL_PATH,
        class_names_path=cfg.CLASS_NAMES_PATH,
    )
    logger.info("ML model loaded")

    # ── Blueprints ────────────────────────────────────────────────────────────
    from routes.auth import auth_bp
    from routes.predictions import predictions_bp
    from routes.analytics import analytics_bp
    from routes.farmer import farmer_bp
    from routes.admin import admin_bp
    from routes.chatbot import chatbot_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(predictions_bp, url_prefix="/api/predictions")
    app.register_blueprint(analytics_bp, url_prefix="/api/analytics")
    app.register_blueprint(farmer_bp, url_prefix="/api/farmer")
    app.register_blueprint(admin_bp, url_prefix="/api/admin")
    app.register_blueprint(chatbot_bp, url_prefix="/api/chatbot")

    # ── JWT Error Handlers ────────────────────────────────────────────────────
    @jwt.expired_token_loader
    def expired_token(_jwt_header, _jwt_data):
        return jsonify({"error": "Token has expired", "code": "TOKEN_EXPIRED"}), 401

    @jwt.invalid_token_loader
    def invalid_token(reason):
        return jsonify({"error": f"Invalid token: {reason}", "code": "INVALID_TOKEN"}), 401

    @jwt.unauthorized_loader
    def missing_token(reason):
        return jsonify({"error": "Authorization required", "code": "MISSING_TOKEN"}), 401

    # ── Global Error Handlers ─────────────────────────────────────────────────
    @app.errorhandler(404)
    def not_found(_):
        return jsonify({"error": "Resource not found"}), 404

    @app.errorhandler(500)
    def server_error(e):
        logger.exception(e)
        return jsonify({"error": "Internal server error"}), 500

    @app.errorhandler(413)
    def too_large(_):
        return jsonify({"error": "File too large"}), 413

    # ── Health Check ─────────────────────────────────────────────────────────
    @app.get("/api/health")
    def health():
        return jsonify({
            "status": "healthy",
            "service": "CropMD API",
            "version": "1.0.0",
        })

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)
