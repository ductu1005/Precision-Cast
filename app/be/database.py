"""
Database connection và models cho PrecisionCast
"""

import os
from sqlalchemy import create_engine, Column, BigInteger, String, Text, Enum, DECIMAL, Integer, Float, TIMESTAMP, ForeignKey, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql import func
from sqlalchemy.pool import QueuePool
import pymysql
import logging

logger = logging.getLogger(__name__)

# Database configuration từ environment variables
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", 3306))
DB_USER = os.getenv("DB_USER", "precisioncast")
DB_PASSWORD = os.getenv("DB_PASSWORD", "precisioncast123")
DB_NAME = os.getenv("DB_NAME", "precisioncast")

# Tạo connection string với charset cho MariaDB
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"

# Tạo engine với connection pool
# pool_pre_ping=True để tự động test connection trước khi dùng
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_pre_ping=True,  # Tự động test connection, reconnect nếu cần
    pool_size=5,  # Số connection trong pool
    max_overflow=10,  # Số connection tối đa khi cần
    pool_recycle=3600,  # Recycle connection sau 1 giờ
    echo=False,
    connect_args={
        "connect_timeout": 5,  # Timeout 5 giây
        "charset": "utf8mb4",
        "init_command": "SET sql_mode='STRICT_TRANS_TABLES'"
    }
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class cho models
Base = declarative_base()


class Product(Base):
    """Model cho bảng products"""
    __tablename__ = "products"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    product_code = Column(String(50), comment='Mã sản phẩm')
    batch_code = Column(String(50), comment='Mã lô sản xuất')
    created_at = Column(TIMESTAMP, server_default=func.now())
    
    # Relationship
    inspections = relationship("InspectionResult", back_populates="product")


class InspectionResult(Base):
    """Model cho bảng inspection_results"""
    __tablename__ = "inspection_results"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    product_id = Column(BigInteger, ForeignKey('products.id', ondelete='SET NULL'), comment='Tham chiếu tới sản phẩm')
    image_path = Column(Text, nullable=False, comment='Đường dẫn ảnh')
    prediction = Column(Enum('OK', 'DEFECTIVE', 'PENDING', 'ERROR', name='prediction_enum'), nullable=False, comment='Kết quả dự đoán')
    confidence = Column(DECIMAL(5, 4), comment='Độ tin cậy (0-1)')
    inspected_at = Column(TIMESTAMP, server_default=func.now(), comment='Thời điểm inference')
    created_at = Column(TIMESTAMP, server_default=func.now())
    
    # Relationships
    product = relationship("Product", back_populates="inspections")
    logs = relationship("PredictionLog", back_populates="inspection", cascade="all, delete-orphan")


class PredictionLog(Base):
    """Model cho bảng prediction_logs"""
    __tablename__ = "prediction_logs"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    inspection_id = Column(BigInteger, ForeignKey('inspection_results.id', ondelete='CASCADE'), comment='Tham chiếu tới inspection')
    raw_score = Column(Float, comment='Raw output từ model')
    threshold = Column(Float, comment='Ngưỡng phân loại')
    inference_time_ms = Column(Integer, comment='Thời gian suy luận (ms)')
    created_at = Column(TIMESTAMP, server_default=func.now(), comment='Thời điểm ghi log')
    
    # Relationship
    inspection = relationship("InspectionResult", back_populates="logs")


def get_db():
    """Dependency để lấy database session
    
    Yields:
        Session: Database session
        
    Note:
        Nếu database không có, sẽ yield None và endpoint sẽ handle
    """
    db = None
    try:
        db = SessionLocal()
        # Test connection ngay
        db.execute(text("SELECT 1"))
        yield db
    except Exception as e:
        logger.warning(f"Database not available: {e}")
        if db:
            try:
                db.close()
            except:
                pass
        # Yield None để endpoint có thể check và handle
        yield None
    finally:
        if db:
            try:
                db.close()
            except:
                pass


def init_db():
    """Khởi tạo database tables (nếu chưa tồn tại)
    
    Returns:
        bool: True nếu thành công, False nếu có lỗi
    """
    try:
        # Test connection trước (SQLAlchemy 2.0 syntax)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            result.fetchone()  # Fetch result để đảm bảo connection hoạt động
        
        # Nếu kết nối thành công, tạo tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables initialized successfully")
        return True
    except Exception as e:
        error_msg = str(e)
        # Log chi tiết hơn để debug
        if "Lost connection" in error_msg or "Can't connect" in error_msg:
            logger.warning(f"Database not available at {DB_HOST}:{DB_PORT}, skipping initialization")
            logger.info("Tip: Start MariaDB with: docker-compose up -d mariadb")
        else:
            logger.warning(f"Database initialization error: {error_msg}")
        # Không raise exception để server vẫn có thể chạy mà không có database
        return False
