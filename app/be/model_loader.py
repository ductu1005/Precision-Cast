"""
Model Loader - Tải và sử dụng model CNN đã được huấn luyện
"""

import os
import numpy as np
from PIL import Image
import tensorflow as tf
from typing import Tuple
import logging

logger = logging.getLogger(__name__)

# Đường dẫn mặc định đến model (có thể override bằng biến môi trường)
MODEL_PATH = os.getenv("MODEL_PATH", "models/casting_model_v1.h5")
IMAGE_SIZE = (512, 512)  # Kích thước ảnh input (grayscale 512x512)

def load_model():
    """
    Load model CNN đã được huấn luyện
    
    Returns:
        Loaded TensorFlow/Keras model
    """
    try:
        if os.path.exists(MODEL_PATH):
            logger.info(f"Loading model from {MODEL_PATH}")
            model = tf.keras.models.load_model(MODEL_PATH)
            logger.info("Model loaded successfully")
            return model
        else:
            logger.warning(f"Model file not found at {MODEL_PATH}")
            logger.info("Creating a dummy model for testing purposes")
            # Tạo một dummy model đơn giản để test (trong production phải có model thật)
            return create_dummy_model()
    except Exception as e:
        logger.error(f"Error loading model: {e}")
        logger.info("Creating a dummy model for testing purposes")
        return create_dummy_model()

def create_dummy_model():
    """
    Tạo một dummy model đơn giản để test API
    TRONG PRODUCTION: Phải thay bằng model thật từ notebooks/
    """
    from tensorflow.keras import layers, models
    
    model = models.Sequential([
        layers.Input(shape=(*IMAGE_SIZE, 3)),  # RGB input
        layers.Conv2D(32, (3, 3), activation='relu'),
        layers.MaxPooling2D((2, 2)),
        layers.Conv2D(64, (3, 3), activation='relu'),
        layers.MaxPooling2D((2, 2)),
        layers.Conv2D(64, (3, 3), activation='relu'),
        layers.Flatten(),
        layers.Dense(64, activation='relu'),
        layers.Dense(1, activation='sigmoid')  # Binary classification
    ])
    
    model.compile(
        optimizer='adam',
        loss='binary_crossentropy',
        metrics=['accuracy']
    )
    
    logger.warning("Using dummy model - Replace with trained model in production!")
    return model

def preprocess_image(image: Image.Image) -> np.ndarray:
    """
    Tiền xử lý ảnh để đưa vào model
    
    Args:
        image: PIL Image object
        
    Returns:
        Preprocessed numpy array
    """
    # Resize về kích thước model yêu cầu
    image = image.resize(IMAGE_SIZE)
    
    # Convert sang numpy array
    img_array = np.array(image)
    
    # Normalize pixel values về [0, 1]
    img_array = img_array.astype('float32') / 255.0
    
    # Thêm batch dimension: (1, height, width, channels)
    img_array = np.expand_dims(img_array, axis=0)
    
    return img_array

def predict_image(model, image: Image.Image) -> Tuple[str, float, float, int]:
    """
    Dự đoán ảnh và trả về status, confidence, raw_score và inference_time
    
    Args:
        model: Loaded TensorFlow/Keras model
        image: PIL Image object
        
    Returns:
        Tuple (status, confidence, raw_score, inference_time_ms)
        - status: "defective" hoặc "ok"
        - confidence: Độ tin cậy (0-1)
        - raw_score: Raw output từ model
        - inference_time_ms: Thời gian inference (milliseconds)
    """
    import time
    
    # Tiền xử lý ảnh
    processed_image = preprocess_image(image)
    
    # Đo thời gian inference
    start_time = time.time()
    prediction = model.predict(processed_image, verbose=0)
    inference_time_ms = int((time.time() - start_time) * 1000)
    
    # Lấy confidence score
    # Giả sử model output là probability của lớp "defective" (sigmoid output)
    raw_score = float(prediction[0][0])
    
    # Xác định status
    # Nếu confidence > 0.5 -> defective, ngược lại -> ok
    # (Có thể điều chỉnh threshold tùy theo model thực tế)
    threshold = 0.5
    if raw_score > threshold:
        status = "defective"
        # Confidence của lớp defective
        final_confidence = raw_score
    else:
        status = "ok"
        # Confidence của lớp ok = 1 - confidence của defective
        final_confidence = 1 - raw_score
    
    return status, final_confidence, raw_score, inference_time_ms

