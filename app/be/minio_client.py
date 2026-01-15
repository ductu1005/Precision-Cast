"""
MinIO client để lưu trữ ảnh
"""

import os
from minio import Minio
from minio.error import S3Error
import logging
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

# MinIO configuration từ environment variables
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin123")
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "precisioncast-images")
MINIO_SECURE = os.getenv("MINIO_SECURE", "false").lower() == "true"

# Khởi tạo MinIO client
minio_client = None


def get_minio_client():
    """Lấy MinIO client instance"""
    global minio_client
    if minio_client is None:
        try:
            minio_client = Minio(
                MINIO_ENDPOINT,
                access_key=MINIO_ACCESS_KEY,
                secret_key=MINIO_SECRET_KEY,
                secure=MINIO_SECURE
            )
            # Đảm bảo bucket tồn tại
            init_bucket()
            logger.info("MinIO client initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing MinIO client: {e}")
            raise
    return minio_client


def init_bucket():
    """Khởi tạo bucket nếu chưa tồn tại"""
    try:
        client = get_minio_client()
        if not client.bucket_exists(MINIO_BUCKET):
            client.make_bucket(MINIO_BUCKET)
            logger.info(f"Created bucket: {MINIO_BUCKET}")
        else:
            logger.info(f"Bucket {MINIO_BUCKET} already exists")
    except S3Error as e:
        logger.error(f"Error creating bucket: {e}")
        raise


def upload_image(image_data: bytes, filename: str = None) -> str:
    """
    Upload ảnh lên MinIO
    
    Args:
        image_data: Bytes của ảnh
        filename: Tên file (nếu None sẽ tự động generate)
        
    Returns:
        Đường dẫn object trong MinIO (object_name)
    """
    try:
        client = get_minio_client()
        
        # Generate filename nếu không có
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_id = str(uuid.uuid4())[:8]
            filename = f"{timestamp}_{unique_id}.jpg"
        
        # Đảm bảo filename không có path separator
        object_name = filename.replace("\\", "/").lstrip("/")
        
        # Upload file
        from io import BytesIO
        image_stream = BytesIO(image_data)
        image_size = len(image_data)
        
        client.put_object(
            MINIO_BUCKET,
            object_name,
            image_stream,
            image_size,
            content_type="image/jpeg"
        )
        
        logger.info(f"Image uploaded to MinIO: {object_name}")
        return object_name
        
    except S3Error as e:
        logger.error(f"Error uploading image to MinIO: {e}")
        raise


def get_image_url(object_name: str, expires_in_seconds: int = 3600) -> str:
    """
    Lấy URL để truy cập ảnh từ MinIO
    
    Args:
        object_name: Tên object trong MinIO
        expires_in_seconds: Thời gian hết hạn URL (mặc định 1 giờ)
        
    Returns:
        Presigned URL
    """
    try:
        client = get_minio_client()
        url = client.presigned_get_object(
            MINIO_BUCKET,
            object_name,
            expires=expires_in_seconds
        )
        return url
    except S3Error as e:
        logger.error(f"Error generating presigned URL: {e}")
        raise

