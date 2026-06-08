"""
CropMD – Configuration
All config loaded from environment variables with sensible defaults.
"""

import os
from datetime import timedelta


class Config:
    # ── App ──────────────────────────────────────────────────────────────────
    SECRET_KEY = os.environ.get("SECRET_KEY", "change-me-in-production")
    DEBUG = os.environ.get("DEBUG", "False").lower() == "true"
    ENV = os.environ.get("FLASK_ENV", "production")

    # ── MongoDB ──────────────────────────────────────────────────────────────
    MONGO_URI = os.environ.get(
        "MONGO_URI", "mongodb://localhost:27017/cropmd"
    )
    DB_NAME = os.environ.get("DB_NAME", "cropmd")

    # ── JWT ──────────────────────────────────────────────────────────────────
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "jwt-secret-change-me")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        hours=int(os.environ.get("JWT_ACCESS_HOURS", "24"))
    )
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(
        days=int(os.environ.get("JWT_REFRESH_DAYS", "30"))
    )

    # ── Cloudinary ────────────────────────────────────────────────────────────
    CLOUDINARY_CLOUD_NAME = os.environ.get("CLOUDINARY_CLOUD_NAME", "")
    CLOUDINARY_API_KEY = os.environ.get("CLOUDINARY_API_KEY", "")
    CLOUDINARY_API_SECRET = os.environ.get("CLOUDINARY_API_SECRET", "")

    # ── AWS S3 (alternative to Cloudinary) ───────────────────────────────────
    AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID", "")
    AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY", "")
    AWS_S3_BUCKET = os.environ.get("AWS_S3_BUCKET", "cropmd-images")
    AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")

    # ── AI APIs ───────────────────────────────────────────────────────────────
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

    # ── Model ─────────────────────────────────────────────────────────────────
    MODEL_PATH = os.environ.get("MODEL_PATH", "ml_models/cropmd_model.keras")
    CLASS_NAMES_PATH = os.environ.get("CLASS_NAMES_PATH", "ml_models/class_names.json")
    MAX_IMAGE_SIZE_MB = int(os.environ.get("MAX_IMAGE_SIZE_MB", "10"))

    # ── CORS ──────────────────────────────────────────────────────────────────
    CORS_ORIGINS = os.environ.get(
        "CORS_ORIGINS",
        "http://localhost:5173,http://localhost:3000,https://cropmd.vercel.app",
    ).split(",")

    # ── Rate Limiting ─────────────────────────────────────────────────────────
    RATELIMIT_DEFAULT = os.environ.get("RATELIMIT_DEFAULT", "200 per hour")
    RATELIMIT_PREDICTION = os.environ.get("RATELIMIT_PREDICTION", "50 per hour")


class DevelopmentConfig(Config):
    DEBUG = True
    ENV = "development"


class ProductionConfig(Config):
    DEBUG = False
    ENV = "production"


config_map = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}


def get_config() -> Config:
    env = os.environ.get("FLASK_ENV", "development")
    return config_map.get(env, config_map["default"])
