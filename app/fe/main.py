"""
PrecisionCast Frontend - Streamlit UI
Giao diện web để upload ảnh và xem kết quả phân loại
"""

import streamlit as st
import requests
from PIL import Image
import io
import os
from typing import Optional, List, Dict
from datetime import datetime
import pandas as pd

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
        .nav-item {
            padding: 1rem;
            margin: 0.5rem 0;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.3s;
        }
        .nav-item:hover {
            background-color: #f0f0f0;
        }
        .nav-item-active {
            background-color: #1f77b4;
            color: white;
        }
    </style>
""", unsafe_allow_html=True)

# =============================================================================
# API FUNCTIONS
# =============================================================================

def check_api_health() -> tuple:
    """Kiểm tra API backend có đang chạy không"""
    try:
        response = requests.get(f"{API_URL}/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            status = data.get("status", "unknown")
            model_loaded = data.get("model_loaded", False)
            
            model_status = "✅ Model đã tải" if model_loaded else "⚠️ Model chưa tải"
            message = f"API healthy - {model_status}"
            return True, message, data
        else:
            return False, f"API trả về lỗi: {response.status_code}", None
    except requests.exceptions.Timeout:
        return False, "API timeout (>10s)", None
    except requests.exceptions.ConnectionError:
        return False, "Không thể kết nối đến API", None
    except Exception as e:
        return False, f"Lỗi: {str(e)}", None

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
        response = requests.post(f"{API_URL}/predict", files=files, timeout=60)
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Lỗi API: {response.status_code}")
            return None
    except requests.exceptions.Timeout:
        st.error("API timeout - Hình ảnh quá lớn hoặc server đang bận")
        st.info("Vui lòng thử lại hoặc sử dụng ảnh nhỏ hơn")
        return None
    except requests.exceptions.ConnectionError:
        st.error(f"Không thể kết nối đến API backend tại {API_URL}")
        return None
    except Exception as e:
        st.error(f"Lỗi khi gửi request: {str(e)}")
        return None

def save_inspection_result(image_name: str, prediction: str, confidence: float) -> bool:
    """
    Lưu kết quả kiểm tra vào database qua API
    TODO: Implement khi có API endpoint
    
    Args:
        image_name: Tên file ảnh
        prediction: Kết quả dự đoán ('ok' hoặc 'defective')
        confidence: Độ tin cậy (0-1)
        
    Returns:
        True nếu lưu thành công, False nếu thất bại
    """
    try:
        # TODO: Gọi API để lưu vào database
        # data = {
        #     "image_name": image_name,
        #     "prediction": prediction,
        #     "confidence": confidence
        # }
        # response = requests.post(f"{API_URL}/inspections", json=data, timeout=10)
        # return response.status_code == 201
        
        # Mock: Giả lập lưu thành công
        return True
    except Exception as e:
        st.error(f"Lỗi khi lưu kết quả: {str(e)}")
        return False

def get_inspection_history(limit: int = 50) -> List[Dict]:
    """
    Lấy danh sách lịch sử kiểm tra từ API
    TODO: Implement khi có API endpoint
    
    Args:
        limit: Số lượng bản ghi tối đa
        
    Returns:
        List các bản ghi inspection
    """
    try:
        # TODO: Gọi API khi backend sẵn sàng
        response = requests.get(f"{API_URL}/inspections?limit={limit}", timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data.get("data", [])
        
        return []
    except Exception as e:
        st.error(f"Lỗi khi lấy lịch sử: {str(e)}")
        return []

# =============================================================================
# TAB COMPONENTS
# =============================================================================

def render_inspection_tab():
    """Render tab kiểm tra sản phẩm"""
    st.header("🔍 Kiểm tra chất lượng sản phẩm")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("📤 Upload hình ảnh")
        
        uploaded_file = st.file_uploader(
            "Chọn file ảnh sản phẩm đúc",
            type=['jpg', 'jpeg', 'png', 'bmp'],
            help="Hỗ trợ định dạng: JPG, JPEG, PNG, BMP",
            key="file_uploader"
        )
        
        if uploaded_file is not None:
            # Hiển thị ảnh preview
            image = Image.open(uploaded_file)
            st.image(image, caption="Ảnh đã upload", use_column_width=True)
            
            # Thông tin ảnh
            st.info(f"📏 Kích thước: {image.size[0]} x {image.size[1]} pixels")
            st.info(f"📄 Tên file: {uploaded_file.name}")
    
    with col2:
        st.subheader("📊 Kết quả phân tích")
        
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
                        
                        # Lưu kết quả vào database
                        if save_inspection_result(uploaded_file.name, status, confidence):
                            st.success("💾 Đã lưu kết quả vào hệ thống")
                        
                        # Thông tin chi tiết
                        with st.expander("📋 Chi tiết phân tích"):
                            st.json({
                                "Tên file": uploaded_file.name,
                                "Kết quả": status.upper(),
                                "Độ tin cậy": f"{confidence:.4f}",
                                "Thời gian": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            })
        else:
            st.info("👆 Vui lòng upload ảnh ở cột bên trái để bắt đầu kiểm tra")

def render_history_tab():
    """Render tab danh sách sản phẩm đã kiểm tra"""
    st.header("📋 Danh sách sản phẩm đã kiểm tra")
    
    # Filters
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        filter_status = st.selectbox(
            "Lọc theo trạng thái",
            ["Tất cả", "OK", "Defective"],
            key="filter_status"
        )
    
    with col2:
        filter_date = st.date_input(
            "Lọc theo ngày",
            value=None,
            key="filter_date"
        )
    
    with col3:
        st.write("")  # Spacer
        if st.button("🔄 Làm mới"):
            st.rerun()
    
    st.markdown("---")
    
    # Lấy dữ liệu
    with st.spinner("Đang tải dữ liệu..."):
        history_data = get_inspection_history(limit=50)
    
    if not history_data:
        st.warning("⚠️ Chưa có dữ liệu kiểm tra nào")
        st.info("💡 Hãy thực hiện kiểm tra sản phẩm ở tab 'Kiểm tra sản phẩm'")
        return
    
    # Áp dụng filter
    filtered_data = history_data.copy()
    if filter_status != "Tất cả":
        status_map = {"OK": "ok", "Defective": "defective"}
        filtered_data = [d for d in filtered_data if d["prediction"] == status_map[filter_status]]
    
    # Thống kê tổng quan
    st.subheader("📊 Thống kê")
    stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)
    
    total = len(history_data)
    ok_count = sum(1 for d in history_data if d["prediction"] == "ok")
    defective_count = total - ok_count
    avg_confidence = sum(d["confidence"] for d in history_data) / total if total > 0 else 0
    
    with stat_col1:
        st.metric("Tổng số kiểm tra", total)
    with stat_col2:
        st.metric("Sản phẩm OK", ok_count, f"{ok_count/total*100:.1f}%" if total > 0 else "0%")
    with stat_col3:
        st.metric("Sản phẩm Lỗi", defective_count, f"{defective_count/total*100:.1f}%" if total > 0 else "0%")
    with stat_col4:
        st.metric("Độ tin cậy TB", f"{avg_confidence:.2%}")
    
    st.markdown("---")
    
    # Hiển thị bảng dữ liệu
    st.subheader(f"🗂️ Danh sách ({len(filtered_data)} bản ghi)")
    
    if filtered_data:
        # Chuyển sang DataFrame để hiển thị đẹp hơn
        df = pd.DataFrame(filtered_data)
        
        # Format lại các cột
        df['prediction'] = df['prediction'].apply(lambda x: "🟢 OK" if x == "ok" else "🔴 Defective")
        df['confidence'] = df['confidence'].apply(lambda x: f"{x:.2%}")
        
        # Đổi tên cột
        df_display = df.rename(columns={
            'id': 'ID',
            'image_name': 'Tên ảnh',
            'prediction': 'Kết quả',
            'confidence': 'Độ tin cậy',
            'inspected_at': 'Thời gian',
            'product_code': 'Mã SP',
            'batch_code': 'Mã lô'
        })
        
        # Hiển thị bảng
        st.dataframe(df_display)
        
        # Export CSV
        csv = df_display.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="📥 Tải xuống CSV",
            data=csv,
            file_name=f"inspection_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
        )
    else:
        st.info("Không có dữ liệu phù hợp với bộ lọc")

# =============================================================================
# MAIN APP
# =============================================================================

def main():
    # Header
    st.markdown('<p class="main-header">🔍 PrecisionCast - Quality Inspection System</p>', unsafe_allow_html=True)
    
    # Sidebar với API status
    with st.sidebar:
        st.image("https://via.placeholder.com/200x80/1f77b4/ffffff?text=PrecisionCast", width=200)
        st.markdown("---")
        
        # Kiểm tra kết nối API
        st.subheader("🔌 Trạng thái hệ thống")
        is_healthy, message, health_data = check_api_health()
        if is_healthy:
            st.success(f"✅ {message}")
        else:
            st.error(f"❌ {message}")
            st.caption(f"URL: {API_URL}")
        
        st.markdown("---")
        st.caption("**Phiên bản:** 1.0.0")
        st.caption("**© 2024 PrecisionCast**")
    
    # Main navigation tabs
    tab1, tab2 = st.tabs(["🔍 Kiểm tra sản phẩm", "📋 Danh sách sản phẩm"])
    
    with tab1:
        render_inspection_tab()
    
    with tab2:
        render_history_tab()

if __name__ == "__main__":
    main()

