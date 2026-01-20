"""
PrecisionCast Frontend - Streamlit UI
Entry point for the application
"""

import streamlit as st
from PIL import Image

# Import modules
from utils.helper import load_css
from core.api_client import QualityInspectorClient
from components.sidebar import render_sidebar
from components.display import show_prediction_result

# 1. Cấu hình trang (Phải đặt đầu tiên)
st.set_page_config(
    page_title="PrecisionCast - Quality Inspection",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Load CSS & Sidebar
load_css("style.css")
render_sidebar()

def main():
    # Header
    st.markdown('<p class="main-header">🔍 PrecisionCast - Quality Inspection System</p>', unsafe_allow_html=True)

    # Layout chính: 2 Cột
    col_upload, col_result = st.columns([1, 1], gap="large")

    # --- Cột trái: Upload ---
    with col_upload:
        st.subheader("1. Upload hình ảnh")
        uploaded_file = st.file_uploader(
            "Chọn file ảnh (JPG, PNG, BMP)", 
            type=['jpg', 'jpeg', 'png', 'bmp']
        )

        if uploaded_file:
            # Hiển thị ảnh
            image = Image.open(uploaded_file)
            st.image(image, caption="Preview ảnh đầu vào")
            st.caption(f"Kích thước: {image.size[0]}x{image.size[1]} px")

    # --- Cột phải: Kết quả ---
    with col_result:
        st.subheader("2. Kết quả phân tích")
        
        if uploaded_file:
            # Button trigger
            if st.button("🚀 Chạy kiểm tra chất lượng", type="primary"):
                with st.spinner("AI đang phân tích bề mặt đúc..."):
                    # Gọi API qua Client Service
                    result = QualityInspectorClient.predict(uploaded_file)
                    
                    # Hiển thị kết quả qua Component
                    if result:
                        show_prediction_result(result)
        else:
            # Placeholder khi chưa có ảnh
            st.info("👈 Vui lòng upload ảnh ở cột bên trái để bắt đầu.")
            st.markdown(
                """
                <div style="text-align: center; margin-top: 50px; opacity: 0.5;">
                    <h1>Waiting for input...</h1>
                    <p>Hệ thống sẵn sàng phân tích</p>
                </div>
                """, unsafe_allow_html=True
            )

    # Footer
    st.markdown("---")
    st.markdown("<div style='text-align: center; color: grey;'>© 2024 PrecisionCast AI Team</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()