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
    def get_product_details(product_id: int) -> dict:
        """
        Gọi API lấy chi tiết TRỌN GÓI sản phẩm và lịch sử kiểm tra.
        Endpoint: GET /products/{product_id}
        """
        try:
            # Lưu ý: 
            # 1. URL đã đổi từ .../products/{id}/inspections thành .../products/{id}
            # 2. Không truyền params skip/limit nữa vì API này trả về toàn bộ danh sách
            
            response = requests.get(f"{API_URL}/products/{product_id}", timeout=10)
            
            if response.status_code == 200:
                return response.json() 
                # Kết quả trả về sẽ có dạng: 
                # { "product_info": {...}, "total_inspections": 5, "inspections": [...] }
            
            elif response.status_code == 404:
                return {"error": "Not Found", "message": f"Không tìm thấy sản phẩm với ID {product_id}."}
            else:
                return {"error": "API Error", "message": f"Lỗi Server (Status: {response.status_code})"}
                
        except requests.exceptions.ConnectionError:
            return {"error": "Connection Error", "message": "Không thể kết nối tới Backend."}
        except Exception as e:
            return {"error": "Client Error", "message": str(e)}


    @staticmethod
    def get_history(skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Lấy lịch sử kiểm tra từ Server có phân trang.
        Args:
            skip (int): Số lượng bản ghi cần bỏ qua (để phân trang).
            limit (int): Số lượng bản ghi tối đa muốn lấy.
        """
        try:
            # Cập nhật payload để nhận cả skip và limit từ tham số truyền vào
            payload = {
                "skip": skip,   # <--- Đã sửa: dùng biến skip thay vì số 0
                "limit": limit
            }
           
            # Requests sẽ tự động ghép thành: .../inspections?skip=20&limit=100
            response = requests.get(f"{API_URL}/inspections", params=payload, timeout=10)
           
            if response.status_code == 200:
                result = response.json()
                # Trả về list data
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
def load_inspection_data(skip: int = 0, limit: int = 100) -> pd.DataFrame:
    """
    Wrapper gọi API với đầy đủ tham số phân trang.
    """
    # 1. Gọi API (Client phải hỗ trợ skip và limit)
    data_list = QualityInspectorClient.get_history(skip=skip, limit=limit)
   
    # 2. Xử lý kết quả trả về
    if not data_list:
        return pd.DataFrame()
   
    df = pd.DataFrame(data_list)
   
    # Chuẩn hóa dữ liệu (nếu cần)
    if 'confidence' in df.columns:
        df['confidence'] = pd.to_numeric(df['confidence'], errors='coerce')
       
    return df
