"""
CropMD – Cloud Storage Utility (Cloudinary + S3 fallback)
"""

import os
import io
import logging
import uuid
from datetime import datetime
from typing import Tuple, Optional

logger = logging.getLogger(__name__)


def upload_image(
    image_bytes: bytes,
    filename: str,
    user_id: str,
    folder: str = "cropmd/scans",
) -> Tuple[str, str]:
    """
    Upload image to Cloudinary (primary) or S3 (fallback).
    Returns (public_url, storage_key).
    """
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "jpg"
    unique_name = f"{user_id}/{datetime.utcnow().strftime('%Y%m%d')}_{uuid.uuid4().hex[:8]}.{ext}"
    key = f"{folder}/{unique_name}"

    # Try Cloudinary first
    if os.environ.get("CLOUDINARY_CLOUD_NAME"):
        return _upload_cloudinary(image_bytes, key)

    # Fallback to S3
    if os.environ.get("AWS_ACCESS_KEY_ID"):
        return _upload_s3(image_bytes, key)

    # Dev fallback – return placeholder
    logger.warning("No cloud storage configured. Using placeholder URL.")
    return (f"https://placeholder.cropmd.io/{key}", key)


def delete_image(storage_key: str) -> bool:
    if os.environ.get("CLOUDINARY_CLOUD_NAME"):
        return _delete_cloudinary(storage_key)
    if os.environ.get("AWS_ACCESS_KEY_ID"):
        return _delete_s3(storage_key)
    return True


# ── Cloudinary ─────────────────────────────────────────────────────────────

def _upload_cloudinary(image_bytes: bytes, public_id: str) -> Tuple[str, str]:
    import cloudinary
    import cloudinary.uploader

    cloudinary.config(
        cloud_name=os.environ["CLOUDINARY_CLOUD_NAME"],
        api_key=os.environ["CLOUDINARY_API_KEY"],
        api_secret=os.environ["CLOUDINARY_API_SECRET"],
        secure=True,
    )
    result = cloudinary.uploader.upload(
        image_bytes,
        public_id=public_id,
        resource_type="image",
        transformation=[{"width": 800, "height": 800, "crop": "limit", "quality": "auto:good"}],
    )
    return result["secure_url"], result["public_id"]


def _delete_cloudinary(public_id: str) -> bool:
    import cloudinary
    import cloudinary.uploader
    try:
        cloudinary.uploader.destroy(public_id)
        return True
    except Exception as e:
        logger.error(f"Cloudinary delete failed: {e}")
        return False


# ── AWS S3 ──────────────────────────────────────────────────────────────────

def _upload_s3(image_bytes: bytes, key: str) -> Tuple[str, str]:
    import boto3
    s3 = boto3.client(
        "s3",
        aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
        region_name=os.environ.get("AWS_REGION", "us-east-1"),
    )
    bucket = os.environ["AWS_S3_BUCKET"]
    s3.put_object(
        Bucket=bucket,
        Key=key,
        Body=image_bytes,
        ContentType="image/jpeg",
        ACL="public-read",
    )
    url = f"https://{bucket}.s3.amazonaws.com/{key}"
    return url, key


def _delete_s3(key: str) -> bool:
    import boto3
    try:
        s3 = boto3.client("s3")
        s3.delete_object(Bucket=os.environ["AWS_S3_BUCKET"], Key=key)
        return True
    except Exception as e:
        logger.error(f"S3 delete failed: {e}")
        return False
