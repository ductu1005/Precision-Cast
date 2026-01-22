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

def get_image(object_name: str) -> bytes:
    """
    Lấy ảnh từ MinIO dưới dạng bytes
    """
    try:
        client = get_minio_client()
        if client is None:
            raise Exception("MinIO client not available")
        
        # Lấy object từ MinIO
        from io import BytesIO
        response = client.get_object(MINIO_BUCKET, object_name)
        image_data = response.read()
        response.close()
        response.release_conn()
        
        if not image_data or len(image_data) == 0:
            raise Exception(f"Ảnh rỗng trong MinIO: {object_name}")
        
        logger.info(f"Retrieved {len(image_data)} bytes from MinIO: {object_name}")
        return image_data
        
    except S3Error as e:
        error_code = e.code if hasattr(e, 'code') else 'UNKNOWN'
        if error_code == 'NoSuchKey':
            raise Exception(f"Ảnh không tồn tại: {object_name}")
        raise Exception(f"Lỗi MinIO: {str(e)}")
    except Exception as e:
        logger.error(f"Error getting image: {e}", exc_info=True)
        raise


def get_image_url(object_name: str, expires_in_seconds: int = 3600) -> str:
    """
    Tạo URL để truy cập ảnh qua backend proxy endpoint
    Thay vì dùng presigned URL (có vấn đề với signature khi thay đổi host),
    ta sẽ dùng backend endpoint để proxy ảnh từ MinIO
    """
    if not object_name:
        return None
    
    # URL sẽ là: http://10.10.0.140:8000/images/{object_name}
    # Backend sẽ proxy ảnh từ MinIO và trả về trực tiếp
    # Cần import urllib.parse để encode object_name
    from urllib.parse import quote
    
    # Encode object_name để xử lý ký tự đặc biệt
    encoded_name = quote(object_name, safe='/')
    
    # Tạo URL với external endpoint (IP server)
    # Lưu ý: Đây là URL của backend API, không phải MinIO trực tiếp
    # Backend sẽ proxy request đến MinIO
    base_url = f"http://{MINIO_EXTERNAL_ENDPOINT.split(':')[0]}:8000"
    image_url = f"{base_url}/images/{encoded_name}"
    
    logger.info(f"Generated image URL (proxy): {image_url}")
    return image_url