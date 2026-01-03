"""
PrecisionCast Backend - FastAPI Inference Engine
Endpoint: POST /predict - Nhận ảnh và trả về kết quả phân loại
"""

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import numpy as np
from PIL import Image
import io
from typing import Optional
import logging

from model_loader import load_model, predict_image

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
model = None

@app.on_event("startup")
async def startup_event():
    """Load model khi ứng dụng khởi động"""
    global model
    try:
        model = load_model()
        logger.info("Model loaded successfully")
    except Exception as e:
        logger.error(f"Error loading model: {e}")
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
        "model_loaded": model is not None
    }

@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    """
    Endpoint chính để phân loại ảnh sản phẩm đúc
    
    Args:
        file: File ảnh upload từ client
        
    Returns:
        JSON response với status (defective/ok) và confidence score
    """
    try:
        # Validate file type
        if not file.content_type.startswith('image/'):
            raise HTTPException(
                status_code=400,
                detail="File phải là hình ảnh"
            )
        
        # Đọc ảnh từ file upload
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
        
        # Convert sang RGB nếu cần (xử lý grayscale và RGBA)
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        logger.info(f"Received image: {file.filename}, size: {image.size}")
        
        # Dự đoán bằng model
        if model is None:
            raise HTTPException(
                status_code=503,
                detail="Model chưa được load. Vui lòng thử lại sau."
            )
        
        status, confidence = predict_image(model, image)
        
        # Trả về kết quả
        return JSONResponse({
            "status": status,
            "confidence": float(confidence)
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing image: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi khi xử lý ảnh: {str(e)}"
        )

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

