import os
from minio import Minio
from minio.error import S3Error
import logging
from datetime import datetime, timedelta # <--- Import thêm timedelta
import uuid

logger = logging.getLogger(__name__)

# MinIO configuration
# Endpoint nội bộ (để Backend kết nối)
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "minio:9000")
# Endpoint bên ngoài (để Trình duyệt User truy cập)
MINIO_EXTERNAL_ENDPOINT = os.getenv("MINIO_EXTERNAL_ENDPOINT", "localhost:9000")

MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin123")
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "precisioncast-images")
MINIO_SECURE = os.getenv("MINIO_SECURE", "false").lower() == "true"

minio_client = None

def get_minio_client():
    global minio_client
    if minio_client is None:
        try:
            import urllib3
            http_client = urllib3.PoolManager(
                timeout=urllib3.Timeout(connect=2, read=5),
                retries=urllib3.Retry(total=1, connect=1, read=1, backoff_factor=0.1)
            )
            
            minio_client = Minio(
                MINIO_ENDPOINT,
                access_key=MINIO_ACCESS_KEY,
                secret_key=MINIO_SECRET_KEY,
                secure=MINIO_SECURE,
                http_client=http_client
            )
            logger.info("MinIO client initialized successfully")
        except Exception as e:
            logger.warning(f"Error initializing MinIO client: {e}")
            return None
    return minio_client

def init_bucket():
    try:
        client = get_minio_client()
        if client is None: return False
        
        if not client.bucket_exists(MINIO_BUCKET):
            client.make_bucket(MINIO_BUCKET)
            logger.info(f"Created bucket: {MINIO_BUCKET}")
        return True
    except Exception as e:
        logger.warning(f"MinIO init error: {str(e)}")
        return False

def upload_image(image_data: bytes, filename: str = None) -> str:
    try:
        client = get_minio_client()
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_id = str(uuid.uuid4())[:8]
            filename = f"{timestamp}_{unique_id}.jpg"
        
        object_name = filename.replace("\\", "/").lstrip("/")
        
        from io import BytesIO
        client.put_object(
            MINIO_BUCKET, object_name, BytesIO(image_data),
            len(image_data), content_type="image/jpeg"
        )
        return object_name
    except S3Error as e:
        logger.error(f"Upload error: {e}")
        raise

def get_image_url(object_name: str, expires_in_seconds: int = 3600) -> str:
    """
    Tạo Presigned URL và đổi hostname nội bộ thành localhost
    """
    try:
        client = get_minio_client()
        if client is None: return None
        
        # 1. Tạo link nội bộ (vd: http://minio:9000/...)
        url = client.presigned_get_object(
            MINIO_BUCKET,
            object_name,
            expires=timedelta(seconds=expires_in_seconds)
        )
        
        # 2. Thay thế hostname để trình duyệt truy cập được (http://localhost:9000/...)
        if MINIO_ENDPOINT in url and MINIO_EXTERNAL_ENDPOINT:
            url = url.replace(MINIO_ENDPOINT, MINIO_EXTERNAL_ENDPOINT)
            
        return url
    except Exception as e:
        logger.error(f"Error generating URL: {e}")
        return None