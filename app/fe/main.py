"""
PrecisionCast Frontend - Streamlit UI
Entry point for the application
"""

import streamlit as st
from PIL import Image
import os
import pandas as pd

# Import modules
try:
    from utils.helper import load_css
    from pages.uploadPage import page_upload
    from pages.statusPage import page_stats_table, page_stats_charts, page_model_evaluation
except ImportError:
    # Fallback nếu chưa có module (để code chạy được demo)
    def load_css(f): pass
    


API_URL = os.getenv("API_URL", "http://backend:8000")
# 1. Cấu hình trang (Phải đặt đầu tiên)
st.set_page_config(
    page_title="PrecisionCast - Quality Inspection",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)
p_upload = st.Page(page_upload, title="Kiểm tra sản phẩm", icon="🚀", default=True)
p_table  = st.Page(page_stats_table, title="Bảng dữ liệu", icon="📄", url_path="table")
p_chart  = st.Page(page_stats_charts, title="Biểu đồ phân tích", icon="📈", url_path="charts")
p_eval   = st.Page(page_model_evaluation, title="Đánh giá hiệu suất", icon="🎯")

nav_structure = {
    "Vận hành": [p_upload],
    "Thống kê & Báo cáo": [p_table, p_chart], # Tab mẹ chứa 2 tab con
    "Quản trị": [p_eval]
}

pg = st.navigation(nav_structure)

# --- SIDEBAR & MAIN NAVIGATION ---
def main():
    # --- A. Sidebar Branding (Logo & Caption) ---
    # st.logo là tính năng mới của 1.46, nó sẽ hiện logo ngay trên menu điều hướng rất đẹp
    st.logo(
        "https://img.icons8.com/color/96/000000/industrial-robot.png",
        icon_image="https://img.icons8.com/color/96/000000/industrial-robot.png",
        link="https://google.com"
    )

    # Các thành phần phụ trong Sidebar (hiện bên dưới menu)
    with st.sidebar:
        st.caption("AI Quality Control System v1.0")
        st.divider()
        # Lưu ý: Bạn KHÔNG cần vẽ menu ở đây, pg.run() sẽ tự vẽ menu vào sidebar

    # --- B. Chạy trang hiện tại ---
    pg.run()

    # --- C. Footer chung (Hiển thị ở cuối mọi trang) ---
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: grey; font-size: 0.8em;'>
            © 2024 PrecisionCast AI Team | Powered by FastAPI & Streamlit 1.46
        </div>
        """, 
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()