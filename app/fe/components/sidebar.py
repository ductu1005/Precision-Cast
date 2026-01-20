# components/sidebar.py
import streamlit as st
from core.api_client import QualityInspectorClient, API_URL

def render_sidebar():
    """Hiển thị sidebar"""
    with st.sidebar:
        st.header("📋 Thông tin hệ thống")
        st.markdown("""
        **PrecisionCast - Quality Inspection**
        
        Hệ thống kiểm tra chất lượng sản phẩm đúc tự động sử dụng AI.
        
        **Phân loại:**
        - 🔴 **Defective**: Sản phẩm lỗi
        - 🟢 **OK**: Đạt tiêu chuẩn
        """)
        
        st.markdown("---")
        
        # Status Check Section
        st.subheader("🔌 Trạng thái Server")
        if QualityInspectorClient.check_health():
            st.success("✅ Online")
        else:
            st.error("❌ Offline")
            st.caption(f"Endpoint: {API_URL}")
            
        st.markdown("---")
        st.caption("Version 1.0.0 | PrecisionCast Inc.")