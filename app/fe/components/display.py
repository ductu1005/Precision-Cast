# components/display.py
import streamlit as st

def show_prediction_result(result: dict):
    """Render UI kết quả dựa trên response từ API"""
    
    # Kiểm tra lỗi trước
    if "error" in result:
        st.error(f"⚠️ Có lỗi xảy ra: {result['error']}")
        return

    status = result.get("status", "unknown")
    confidence = result.get("confidence", 0.0)

    # Hiển thị Status Box
    if status == "DEFECTIVE":
        st.markdown(f"""
            <div class="status-box status-defective">
                🔴 DEFECTIVE
                <div class="confidence-text">Độ tin cậy: {confidence:.2%}</div>
            </div>
        """, unsafe_allow_html=True)
        st.error("⚠️ Cảnh báo: Sản phẩm có lỗi đúc!")
        
    elif status == "OK":
        st.markdown(f"""
            <div class="status-box status-ok">
                🟢 OK
                <div class="confidence-text">Độ tin cậy: {confidence:.2%}</div>
            </div>
        """, unsafe_allow_html=True)
        st.success("✅ Sản phẩm đạt chất lượng xuất xưởng.")
        
    else:
        st.warning(f"Không xác định được trạng thái: {status}")

    # Thanh progress bar cho độ tin cậy
    st.write("Độ tự tin của AI:")
    st.progress(confidence)