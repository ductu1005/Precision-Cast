# core/api_client.py
import requests
import os
from typing import Optional, Dict, Any

# Lấy URL từ biến môi trường
API_URL = os.getenv("API_URL", "http://localhost:8000")

class QualityInspectorClient:
    """Class quản lý việc giao tiếp với Backend API"""
    
    @staticmethod
    def check_health() -> bool:
        """Kiểm tra kết nối server"""
        try:
            response = requests.get(f"{API_URL}/health", timeout=5)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False

    @staticmethod
    def predict(image_file) -> Optional[Dict[str, Any]]:
        """Gửi ảnh để phân loại"""
        try:
            # Reset pointer file về đầu để đảm bảo đọc đủ dữ liệu
            image_file.seek(0)
            files = {"file": (image_file.name, image_file.getvalue(), image_file.type)}
            
            response = requests.post(f"{API_URL}/predict", files=files, timeout=30)
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"API Error: {response.status_code}"}
                
        except requests.exceptions.ConnectionError:
            return {"error": "Connection Error"}
        except Exception as e:
            return {"error": str(e)}
        
    