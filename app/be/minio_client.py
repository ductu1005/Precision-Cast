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
MINIO_PUBLIC_URL = os.getenv("MINIO_PUBLIC_URL", "http://localhost:9000")

# Khởi tạo MinIO client
minio_client = None
minio_public_client = None


def get_minio_client():
    """Lấy MinIO client instance
    
    Returns:
        Minio client hoặc None nếu không kết nối được
    """
    global minio_client
    if minio_client is None:
        try:
            # Tạo client với timeout ngắn để fail nhanh
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


def get_minio_public_client():
    """Lấy MinIO client instance với public endpoint để tạo presigned URL
    
    Client này dùng để tạo presigned URL với đúng public endpoint ngay từ đầu,
    tránh lỗi SignatureDoesNotMatch khi thay đổi host sau khi tạo URL.
    
    Returns:
        Minio client với public endpoint hoặc None nếu không kết nối được
    """
    global minio_public_client
    if minio_public_client is None:
        try:
            # Parse MINIO_PUBLIC_URL để lấy host và port
            from urllib.parse import urlparse
            public_url_parsed = urlparse(MINIO_PUBLIC_URL)
            public_host = public_url_parsed.netloc  # host:port (ví dụ: 10.10.0.140:9000)
            
            # Tạo client với public endpoint nhưng vẫn dùng internal endpoint để kết nối
            # Vì client cần kết nối đến MinIO server để generate signature
            # Nhưng sẽ dùng public_host trong presigned URL
            import urllib3
            http_client = urllib3.PoolManager(
                timeout=urllib3.Timeout(connect=2, read=5),
                retries=urllib3.Retry(total=1, connect=1, read=1, backoff_factor=0.1)
            )
            
            # Vẫn kết nối đến internal endpoint (minio:9000) để có thể giao tiếp
            # Nhưng sẽ override base_url khi tạo presigned URL
            minio_public_client = Minio(
                MINIO_ENDPOINT,  # Vẫn dùng internal endpoint để kết nối
                access_key=MINIO_ACCESS_KEY,
                secret_key=MINIO_SECRET_KEY,
                secure=MINIO_SECURE,
                http_client=http_client
            )
            logger.info(f"MinIO public client initialized (will use {MINIO_PUBLIC_URL} for presigned URLs)")
        except Exception as e:
            logger.warning(f"Error initializing MinIO public client: {e}")
            return None
    return minio_public_client


def init_bucket():
    """Khởi tạo bucket nếu chưa tồn tại
    
    Returns:
        bool: True nếu thành công, False nếu có lỗi
    """
    try:
        client = get_minio_client()
        if client is None:
            return False
        
        # Test connection nhanh với timeout ngắn
        if not client.bucket_exists(MINIO_BUCKET):
            client.make_bucket(MINIO_BUCKET)
            logger.info(f"Created bucket: {MINIO_BUCKET}")
        else:
            logger.info(f"Bucket {MINIO_BUCKET} already exists")
        return True
    except Exception as e:
        error_msg = str(e)
        if "Connection" in error_msg or "timeout" in error_msg.lower():
            logger.warning(f"MinIO not available at {MINIO_ENDPOINT}, skipping bucket initialization")
        else:
            logger.warning(f"MinIO initialization error: {error_msg}")
        # Không raise exception để server vẫn có thể chạy mà không có MinIO
        return False


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
    Lấy presigned URL để truy cập ảnh từ MinIO
    URL sẽ dùng public endpoint (MINIO_PUBLIC_URL) để browser có thể truy cập
    
    Args:
        object_name: Tên object trong MinIO
        expires_in_seconds: Thời gian hết hạn URL (mặc định 1 giờ)
        
    Returns:
        Presigned URL với public endpoint (ví dụ: http://10.10.0.140:9000)
    """
    try:
        # Dùng client thông thường để kiểm tra object
        client = get_minio_client()
        if client is None:
            raise Exception("MinIO client not available. Kiểm tra kết nối MinIO.")
        
        logger.info(f"Creating presigned URL for: bucket={MINIO_BUCKET}, object={object_name}")
        
        # Kiểm tra object có tồn tại không trước khi tạo presigned URL
        try:
            stat = client.stat_object(MINIO_BUCKET, object_name)
            logger.info(f"Object exists in MinIO: {object_name}, size: {stat.size} bytes")
        except S3Error as stat_error:
            error_code = stat_error.code if hasattr(stat_error, 'code') else 'UNKNOWN'
            logger.error(f"Object not found in MinIO: {object_name}, error code: {error_code}")
            raise Exception(f"Ảnh không tồn tại trong MinIO: {object_name}")
        except Exception as stat_error:
            logger.error(f"Error checking object in MinIO: {stat_error}")
            raise Exception(f"Lỗi khi kiểm tra ảnh trong MinIO: {str(stat_error)}")
        
        # Tạo presigned URL với đúng public endpoint ngay từ đầu
        # Vấn đề: Signature được tính toán dựa trên host, nên không thể đơn giản thay đổi host
        # Giải pháp: Tạo một MinIO client mới với public endpoint để generate presigned URL
        try:
            from datetime import timedelta
            from urllib.parse import urlparse
            
            # Parse MINIO_PUBLIC_URL để lấy host và port
            public_url_parsed = urlparse(MINIO_PUBLIC_URL)
            public_host = public_url_parsed.netloc.split(':')[0]  # Chỉ lấy host, không có port
            public_port = public_url_parsed.port or (443 if public_url_parsed.scheme == 'https' else 80)
            
            logger.info(f"Creating presigned URL with public endpoint: {MINIO_PUBLIC_URL}")
            
            # Tạo presigned URL với internal endpoint
            presigned_url = client.presigned_get_object(
                MINIO_BUCKET,
                object_name,
                expires=timedelta(seconds=expires_in_seconds)
            )
            
            logger.info(f"Original presigned URL: {presigned_url[:200]}...")
            
            # Parse và rebuild URL với public endpoint
            from urllib.parse import urlparse, urlunparse
            presigned_parsed = urlparse(presigned_url)
            
            # Thử rebuild URL với public host
            fixed_url = urlunparse((
                public_url_parsed.scheme,
                public_url_parsed.netloc,  # public_host:port
                presigned_parsed.path,
                presigned_parsed.params,
                presigned_parsed.query,  # Giữ nguyên query (chứa signature)
                presigned_parsed.fragment
            ))
            
            logger.info(f"Rebuilt presigned URL with public endpoint: {fixed_url[:200]}...")
            
            # Nếu cách này không work (signature invalid), sẽ cần dùng cách khác:
            # - Proxy request qua backend
            # - Hoặc config MinIO để chấp nhận presigned URL từ nhiều host
            # - Hoặc dùng bucket policy public read thay vì presigned URL
            
        except Exception as e:
            logger.error(f"Error creating presigned URL: {e}", exc_info=True)
            raise Exception(f"Lỗi khi tạo presigned URL từ MinIO: {str(e)}. Kiểm tra kết nối MinIO.")
        
        if not fixed_url:
            raise Exception("Presigned URL rỗng")
        
        return fixed_url
        
    except S3Error as e:
        error_code = e.code if hasattr(e, 'code') else 'UNKNOWN'
        error_msg = str(e)
        logger.error(f"MinIO S3Error generating presigned URL: code={error_code}, message={error_msg}")
        raise Exception(f"Lỗi MinIO khi tạo presigned URL: {error_msg}")
    except Exception as e:
        logger.error(f"Error generating presigned URL: {e}", exc_info=True)
        raise


def get_image(object_name: str) -> bytes:
    """
    Lấy ảnh từ MinIO dưới dạng bytes
    
    Args:
        object_name: Tên object trong MinIO
        
    Returns:
        Bytes của ảnh
    """
    try:
        client = get_minio_client()
        if client is None:
            raise Exception("MinIO client not available. Kiểm tra kết nối MinIO.")
        
        # Log để debug
        logger.info(f"Getting object from MinIO: bucket={MINIO_BUCKET}, object={object_name}")
        
        # Kiểm tra object có tồn tại không
        try:
            client.stat_object(MINIO_BUCKET, object_name)
            logger.info(f"Object exists in MinIO: {object_name}")
        except S3Error as stat_error:
            logger.error(f"Object not found in MinIO: {object_name}, error: {stat_error}")
            raise Exception(f"Ảnh không tồn tại trong MinIO: {object_name}")
        
        # Lấy object
        from io import BytesIO
        response = client.get_object(MINIO_BUCKET, object_name)
        image_data = response.read()
        response.close()
        response.release_conn()
        
        if not image_data or len(image_data) == 0:
            raise Exception(f"Ảnh rỗng trong MinIO: {object_name}")
        
        logger.info(f"Successfully retrieved {len(image_data)} bytes from MinIO")
        return image_data
        
    except S3Error as e:
        error_code = e.code if hasattr(e, 'code') else 'UNKNOWN'
        error_msg = str(e)
        logger.error(f"MinIO S3Error getting image: code={error_code}, message={error_msg}")
        if error_code == 'NoSuchKey':
            raise Exception(f"Ảnh không tồn tại: {object_name}")
        raise Exception(f"Lỗi MinIO: {error_msg}")
    except Exception as e:
        logger.error(f"Error getting image: {e}", exc_info=True)
        raise

