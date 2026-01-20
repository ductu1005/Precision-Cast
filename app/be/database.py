"""
Database connection và models cho PrecisionCast
"""

import os
from sqlalchemy import create_engine, Column, BigInteger, String, Text, Enum, DECIMAL, Integer, Float, TIMESTAMP, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql import func
import pymysql
import logging

logger = logging.getLogger(__name__)

# Database configuration từ environment variables
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", 3306))
DB_USER = os.getenv("DB_USER", "precisioncast")
DB_PASSWORD = os.getenv("DB_PASSWORD", "precisioncast123")
DB_NAME = os.getenv("DB_NAME", "precisioncast")

# Tạo connection string
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Tạo engine
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=False
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
    """Dependency để lấy database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Khởi tạo database tables (nếu chưa tồn tại)"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise

