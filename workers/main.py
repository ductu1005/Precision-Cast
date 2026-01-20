# workers/main.py
from fastapi import FastAPI, UploadFile, File, HTTPException
import tensorflow as tf
import numpy as np
from io import BytesIO
from PIL import Image
import uvicorn
import logging

# Cấu hình logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Load model một lần khi khởi động
try:
    model = tf.keras.models.load_model('/app/models/casting_model_v1.h5')
    logger.info("Worker: Model loaded successfully")
except Exception as e:
    logger.error(f"Worker: Error loading model: {e}")
    model = None

def preprocess_image(img_content):
    """Hàm xử lý ảnh thuần túy (CPU bound)"""
    img = Image.open(BytesIO(img_content))
    
    # Convert sang RGB nếu ảnh là RGBA hoặc Grayscale
    if img.mode != 'RGB':
        img = img.convert('RGB')
        
    img = img.resize((300, 300))
    img_array = np.array(img) / 255.0
    img_array = np.expand_dims(img_array, axis=0)
    return img_array

@app.get("/health")
def health():
    return {"status": "healthy", "model_loaded": model is not None}

@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    try:
        contents = await file.read()
        # 1. Tiền xử lý
        img_array = preprocess_image(contents)
        # 2. Dự đoán (TensorFlow mặc định chạy eager execution, chặn thread)
        # Nếu tải cao, nên dùng run_in_threadpool, nhưng với demo này chạy trực tiếp ok
        prediction = model.predict(img_array)
        
        score = float(prediction[0][0])
        label = "OK" if score > 0.5 else "DEFECTIVE"
        
        logger.info(f"Worker predicted: {label} ({score})")
        
        return {
            "prediction": label, 
            "confidence": score
        }
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)