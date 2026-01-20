import streamlit as st
from PIL import Image

# Import modules
from core.api_client import QualityInspectorClient
from components.display import show_prediction_result

def page_upload():
    """Trang 1: Upload và kiểm tra (Giữ nguyên giao diện cũ)"""
    st.markdown('<p class="main-header">🚀 Kiểm tra chất lượng (Live Inference)</p>', unsafe_allow_html=True)

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
            st.image(image, caption="Preview ảnh đầu vào", use_column_width=True)
            st.caption(f"Kích thước: {image.size[0]}x{image.size[1]} px")

    # --- Cột phải: Kết quả ---
    with col_result:
        st.subheader("2. Kết quả phân tích")
        
        if uploaded_file:
            # Button trigger
            if st.button("⚡ Chạy kiểm tra ngay", type="primary", use_container_width=True):
                with st.spinner("AI đang phân tích bề mặt đúc..."):
                    # Gọi API qua Client Service
                    # Lưu ý: Upload file lại cần seek(0) nếu đã đọc trước đó
                    uploaded_file.seek(0)
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