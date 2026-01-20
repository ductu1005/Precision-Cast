"""
PrecisionCast Backend - FastAPI Inference Engine
Endpoint: POST /predict - Nhận ảnh và trả về kết quả phân loại
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc
import uvicorn
import numpy as np
from PIL import Image
import io
import os
import httpx
from typing import Optional, List
import logging

# from model_loader import load_model, predict_image
from database import get_db, init_db, Product, InspectionResult, PredictionLog
from minio_client import upload_image, init_bucket

# Cấu hình logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Khởi tạo FastAPI app
app = FastAPI(
    title="PrecisionCast API",
    description="API để phân loại chất lượng sản phẩm đúc (Defective/OK)",
    version="1.0.0"
)

# Cấu hình CORS để frontend có thể kết nối
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Trong production nên giới hạn origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load model khi khởi động ứng dụng
WORKER_URL = os.getenv("AI_WORKER_URL", "http://ai_worker:8001")
THRESHOLD = 0.5

@app.on_event("startup")
async def startup_event():
    """Load model, init database và MinIO khi ứng dụng khởi động"""
    try:
        # Load model
        # model = load_model()
        # logger.info("Model loaded successfully")
        
        # Initialize database
        # init_db()
        logger.info("Database initialized")
        
        # Initialize MinIO bucket
        # init_bucket()
        logger.info("MinIO initialized")
        
    except Exception as e:
        logger.error(f"Error during startup: {e}")
        # Trong production, có thể không khởi động nếu không load được model
        raise

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "PrecisionCast API is running",
        "status": "healthy"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint với thông tin model"""
    return {
        "status": "healthy",
        "model_loaded": "casting_model"
    }

@app.post("/predict")
async def predict(
    file: UploadFile = File(...),
    product_code: Optional[str] = Query(None, description="Mã sản phẩm"),
    batch_code: Optional[str] = Query(None, description="Mã lô sản xuất"),
    db: Session = Depends(get_db)
):
    """
    Endpoint chính để phân loại ảnh sản phẩm đúc và lưu vào database
    
    Args:
        file: File ảnh upload từ client
        product_code: Mã sản phẩm (optional)
        batch_code: Mã lô sản xuất (optional)
        db: Database session
        
    Returns:
        JSON response với status (defective/ok), confidence score và inspection_id
    """
    try:
        # 1. Validate file
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File phải là hình ảnh")
        
        contents = await file.read()
        
        # 2. Upload MinIO (Làm trước để đảm bảo ảnh đã lưu an toàn)
        try:
            image_path = upload_image(contents, file.filename)
        except Exception as e:
            logger.error(f"MinIO Upload Error: {e}")
            raise HTTPException(status_code=500, detail="Lỗi lưu trữ hình ảnh")

        # 3. Tạo record Product (nếu cần)
        product_id = None
        if product_code or batch_code:
            existing_product = db.query(Product).filter(
                Product.product_code == product_code,
                Product.batch_code == batch_code
            ).first()
            if existing_product:
                product_id = existing_product.id
            else:
                new_product = Product(product_code=product_code, batch_code=batch_code)
                db.add(new_product)
                db.flush()
                product_id = new_product.id

        # 4. Lưu Inspection vào DB với trạng thái TẠM (Pending) hoặc NULL
        # Bước này quan trọng: Lưu lại bằng chứng là đã nhận request
        inspection = InspectionResult(
            product_id=product_id,
            image_path=image_path,
            prediction="PENDING", # Hoặc để null tùy thiết kế DB của bạn
            confidence=0.0
        )
        db.add(inspection)
        db.commit() # Commit lần 1 để có ID
        db.refresh(inspection)
        
        logger.info(f"Created inspection ID {inspection.id}, sending to AI Worker...")

        # 5. GỌI SANG AI WORKER (Bước quan trọng nhất)
        ai_result = None
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Gửi file binary sang worker
                files = {'file': (file.filename, contents, file.content_type)}
                response = await client.post(f"{WORKER_URL}/predict", files=files)
                
                if response.status_code != 200:
                    raise Exception(f"Worker returned {response.status_code}: {response.text}")
                
                ai_result = response.json() # {"prediction": "OK", "confidence": 0.99}
                
        except Exception as e:
            logger.error(f"Error calling AI Worker: {e}")
            # Cập nhật trạng thái lỗi
            inspection.prediction = "ERROR"
            db.commit()
            raise HTTPException(status_code=500, detail=f"Lỗi xử lý AI: {str(e)}")

        # 6. Cập nhật kết quả vào DB sau khi có từ Worker
        inspection.prediction = ai_result['prediction']
        inspection.confidence = ai_result['confidence']
        
        # Lưu log (nếu có bảng log)
        # log = PredictionLog(...) 
        # db.add(log)
        
        db.commit() # Commit lần 2: Xác nhận kết quả
        
        logger.info(f"Updated inspection ID {inspection.id} with result {inspection.prediction}")

        # 7. Trả về kết quả cuối cùng cho Client
        return JSONResponse({
            "status": inspection.prediction,
            "confidence": float(inspection.confidence) if inspection.confidence is not None else 0.0,
            "inspection_id": inspection.id,
            "image_path": image_path,
            "product_id": product_id
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/inspections")
async def get_inspections(
    skip: int = Query(0, ge=0, description="Số bản ghi bỏ qua"),
    limit: int = Query(100, ge=1, le=1000, description="Số bản ghi trả về"),
    prediction: Optional[str] = Query(None, description="Lọc theo prediction (ok/defective)"),
    batch_code: Optional[str] = Query(None, description="Lọc theo mã lô"),
    db: Session = Depends(get_db)
):
    """
    API 1: Lấy danh sách các sản phẩm đã kiểm tra
    
    Args:
        skip: Số bản ghi bỏ qua (pagination)
        limit: Số bản ghi trả về (pagination)
        prediction: Lọc theo kết quả (ok/defective)
        batch_code: Lọc theo mã lô sản xuất
        db: Database session
        
    Returns:
        Danh sách các inspection results
    """
    try:
        query = db.query(InspectionResult).join(Product, InspectionResult.product_id == Product.id, isouter=True)
        
        # Apply filters
        if prediction:
            if prediction not in ['ok', 'defective']:
                raise HTTPException(status_code=400, detail="prediction phải là 'ok' hoặc 'defective'")
            query = query.filter(InspectionResult.prediction == prediction)
        
        if batch_code:
            query = query.filter(Product.batch_code == batch_code)
        
        # Order by inspected_at desc (mới nhất trước)
        query = query.order_by(desc(InspectionResult.inspected_at))
        
        # Pagination
        total = query.count()
        inspections = query.offset(skip).limit(limit).all()
        
        # Format response
        results = []
        for inspection in inspections:
            product = inspection.product if inspection.product else None
            results.append({
                "id": inspection.id,
                "product_id": inspection.product_id,
                "product_code": product.product_code if product else None,
                "batch_code": product.batch_code if product else None,
                "image_path": inspection.image_path,
                "prediction": inspection.prediction,
                "confidence": float(inspection.confidence) if inspection.confidence else None,
                "inspected_at": inspection.inspected_at.isoformat() if inspection.inspected_at else None,
                "created_at": inspection.created_at.isoformat() if inspection.created_at else None
            })
        
        return {
            "total": total,
            "skip": skip,
            "limit": limit,
            "data": results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching inspections: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi khi lấy danh sách kiểm tra: {str(e)}"
        )


@app.get("/products/{product_id}/inspections")
async def get_product_inspections(
    product_id: int,
    skip: int = Query(0, ge=0, description="Số bản ghi bỏ qua"),
    limit: int = Query(100, ge=1, le=1000, description="Số bản ghi trả về"),
    db: Session = Depends(get_db)
):
    """
    API 2: Lấy danh sách các lần kiểm tra của một sản phẩm cụ thể
    
    Args:
        product_id: ID của sản phẩm
        skip: Số bản ghi bỏ qua (pagination)
        limit: Số bản ghi trả về (pagination)
        db: Database session
        
    Returns:
        Danh sách các inspection results của sản phẩm
    """
    try:
        # Kiểm tra product có tồn tại không
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail=f"Không tìm thấy sản phẩm với ID: {product_id}")
        
        # Query inspections của product
        query = db.query(InspectionResult).filter(InspectionResult.product_id == product_id)
        
        # Order by inspected_at desc (mới nhất trước)
        query = query.order_by(desc(InspectionResult.inspected_at))
        
        # Pagination
        total = query.count()
        inspections = query.offset(skip).limit(limit).all()
        
        # Format response
        results = []
        for inspection in inspections:
            results.append({
                "id": inspection.id,
                "product_id": inspection.product_id,
                "product_code": product.product_code,
                "batch_code": product.batch_code,
                "image_path": inspection.image_path,
                "prediction": inspection.prediction,
                "confidence": float(inspection.confidence) if inspection.confidence else None,
                "inspected_at": inspection.inspected_at.isoformat() if inspection.inspected_at else None,
                "created_at": inspection.created_at.isoformat() if inspection.created_at else None
            })
        
        return {
            "product_id": product_id,
            "product_code": product.product_code,
            "batch_code": product.batch_code,
            "total": total,
            "skip": skip,
            "limit": limit,
            "data": results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching product inspections: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi khi lấy danh sách kiểm tra: {str(e)}"
        )


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

