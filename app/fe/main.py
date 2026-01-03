"""
PrecisionCast Frontend - Streamlit UI
Giao diện web để upload ảnh và xem kết quả phân loại
"""

import streamlit as st
import requests
from PIL import Image
import io
import os
from typing import Optional

# Cấu hình trang
st.set_page_config(
    page_title="PrecisionCast - Quality Inspection",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API Backend URL (có thể override bằng biến môi trường)
API_URL = os.getenv("API_URL", "http://localhost:8000")

# CSS tùy chỉnh
st.markdown("""
    <style>
        .main-header {
            font-size: 2.5rem;
            font-weight: bold;
            color: #1f77b4;
            text-align: center;
            margin-bottom: 2rem;
        }
        .status-box {
            padding: 1.5rem;
            border-radius: 10px;
            margin: 1rem 0;
            text-align: center;
            font-size: 1.5rem;
            font-weight: bold;
        }
        .status-defective {
            background-color: #ffebee;
            color: #c62828;
            border: 3px solid #c62828;
        }
        .status-ok {
            background-color: #e8f5e9;
            color: #2e7d32;
            border: 3px solid #2e7d32;
        }
        .confidence-text {
            font-size: 1.2rem;
            margin-top: 1rem;
            color: #555;
        }
        .stButton>button {
            width: 100%;
            background-color: #1f77b4;
            color: white;
            font-size: 1.1rem;
            padding: 0.75rem;
            border-radius: 5px;
        }
    </style>
""", unsafe_allow_html=True)

def check_api_health() -> bool:
    """Kiểm tra API backend có đang chạy không"""
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def predict_image(image_file) -> Optional[dict]:
    """
    Gửi ảnh đến API backend để dự đoán
    
    Args:
        image_file: Uploaded file object từ Streamlit
        
    Returns:
        Dictionary với status và confidence, hoặc None nếu lỗi
    """
    try:
        files = {"file": (image_file.name, image_file.getvalue(), image_file.type)}
        response = requests.post(f"{API_URL}/predict", files=files, timeout=30)
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Lỗi API: {response.status_code} - {response.text}")
            return None
    except requests.exceptions.ConnectionError:
        st.error(f"Không thể kết nối đến API backend tại {API_URL}")
        st.info("Vui lòng đảm bảo backend đang chạy!")
        return None
    except Exception as e:
        st.error(f"Lỗi khi gửi request: {str(e)}")
        return None

def main():
    # Header
    st.markdown('<p class="main-header">🔍 PrecisionCast - Quality Inspection System</p>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("📋 Thông tin")
        st.markdown("""
        **Hệ thống kiểm tra chất lượng tự động**
        
        Upload hình ảnh sản phẩm đúc để kiểm tra:
        - 🔴 **Defective**: Sản phẩm lỗi
        - 🟢 **OK**: Sản phẩm đạt chất lượng
        
        ---
        """)
        
        # Kiểm tra kết nối API
        st.subheader("🔌 Trạng thái kết nối")
        if check_api_health():
            st.success("✅ API Backend đang hoạt động")
        else:
            st.error("❌ Không kết nối được API Backend")
            st.info(f"URL: {API_URL}")
        
        st.markdown("---")
        st.markdown("**Phiên bản:** 1.0.0")
    
    # Main content
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.header("📤 Upload hình ảnh")
        
        uploaded_file = st.file_uploader(
            "Chọn file ảnh sản phẩm đúc",
            type=['jpg', 'jpeg', 'png', 'bmp'],
            help="Hỗ trợ định dạng: JPG, JPEG, PNG, BMP"
        )
        
        if uploaded_file is not None:
            # Hiển thị ảnh preview
            image = Image.open(uploaded_file)
            st.image(image, caption="Ảnh đã upload", use_container_width=True)
            
            # Thông tin ảnh
            st.info(f"📏 Kích thước: {image.size[0]} x {image.size[1]} pixels")
    
    with col2:
        st.header("📊 Kết quả")
        
        if uploaded_file is not None:
            # Nút Predict
            if st.button("🔍 Phân tích chất lượng", type="primary"):
                with st.spinner("Đang xử lý ảnh..."):
                    result = predict_image(uploaded_file)
                    
                    if result:
                        status = result.get("status", "")
                        confidence = result.get("confidence", 0.0)
                        
                        # Hiển thị kết quả với màu sắc
                        if status == "defective":
                            st.markdown(
                                f'<div class="status-box status-defective">'
                                f'🔴 DEFECTIVE<br>'
                                f'<span class="confidence-text">Độ tin cậy: {confidence:.2%}</span>'
                                f'</div>',
                                unsafe_allow_html=True
                            )
                            st.error("⚠️ Sản phẩm này có lỗi và cần kiểm tra lại!")
                        elif status == "ok":
                            st.markdown(
                                f'<div class="status-box status-ok">'
                                f'🟢 OK<br>'
                                f'<span class="confidence-text">Độ tin cậy: {confidence:.2%}</span>'
                                f'</div>',
                                unsafe_allow_html=True
                            )
                            st.success("✅ Sản phẩm đạt chất lượng!")
                        else:
                            st.warning(f"⚠️ Trạng thái không xác định: {status}")
                            
                        # Hiển thị confidence bar
                        st.progress(confidence)
        else:
            st.info("👆 Vui lòng upload ảnh ở cột bên trái để bắt đầu kiểm tra")
    
    # Footer
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: #666;'>"
        "PrecisionCast Quality Inspection System v1.0.0"
        "</div>",
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()

