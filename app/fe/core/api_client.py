# core/api_client.py
import requests
import os
from typing import Optional, Dict, Any, List
import requests
import pandas as pd
import streamlit as st

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
        
    @staticmethod
    def get_history(limit: int = 100) -> List[Dict[str, Any]]:
        """
        Lấy lịch sử kiểm tra từ Server.
        Luôn trả về một List (có thể rỗng), không bao giờ raise Exception để UI không bị crash.
        """
        try:
            # Gọi endpoint GET /inspections
            response = requests.get(f"{API_URL}/inspections?skip=0&limit={limit}", timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                # API trả về { "total": ..., "data": [...] }
                # Chúng ta chỉ cần lấy phần "data" để trả về cho UI
                return result.get("data", [])
            else:
                print(f"Error fetching history: {response.status_code}")
                return []
                
        except requests.exceptions.ConnectionError:
            print("Connection Error: Cannot connect to Backend")
            return []
        except Exception as e:
            print(f"Unexpected Error: {e}")
            return []
        
        

# --- HÀM HỖ TRỢ LẤY DỮ LIỆU ---
@st.cache_data(ttl=10) # Cache dữ liệu trong 10 giây
def load_inspection_data():
    """Hàm wrapper để cache dữ liệu từ API Client"""
    data = QualityInspectorClient.get_history(limit=200)
    if not data:
        return pd.DataFrame() # Trả về DF rỗng nếu lỗi hoặc không có data
    
    df = pd.DataFrame(data)
    
    # Chuẩn hóa dữ liệu ngay khi load xong để dùng chung cho cả Table và Chart
    if 'created_at' in df.columns:
        df['created_at'] = pd.to_datetime(df['created_at'])
    
    if 'confidence' in df.columns:
        # Ép kiểu số, lỗi biến thành NaN rồi fill bằng 0
        df['confidence'] = pd.to_numeric(df['confidence'], errors='coerce').fillna(0.0)
        
    return df
        
    