# Thêm vào file chứa các pages (ví dụ views/pages.py hoặc main.py)
import streamlit as st
import pandas as pd


def page_product_detail():
    # 1. Lấy ID từ Session
    if 'selected_product_id' not in st.session_state:
        st.warning("Vui lòng chọn sản phẩm từ trang Danh sách.")
        if st.button("Quay lại danh sách"): st.switch_page(p_table)
        return

    product_id = st.session_state.selected_product_id

    # 2. Header & Nút Back
    c_back, c_title = st.columns([1, 5])
    with c_back:
        if st.button("⬅️ Quay lại"):
            del st.session_state.selected_product_id
            st.switch_page(p_table)
    with c_title:
        st.markdown(f"### 📦 Hồ sơ sản phẩm #{product_id}")

    # 3. Gọi API lấy chi tiết
    with st.spinner("Đang tải hồ sơ sản phẩm..."):
        data = QualityInspectorClient.get_product_details(product_id)
    
    if "error" in data:
        st.error(f"Lỗi: {data['message']}")
        return

    info = data.get("product_info", {})
    inspections = data.get("inspections", [])

    # 4. Dashboard KPIs (Hiển thị thông tin chung)
    st.markdown("---")
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)

    with kpi1:
        st.metric("Mã sản phẩm", info.get("product_code", "N/A"), border=True)
    with kpi2:
        st.metric("Mã lô (Batch)", info.get("batch_code", "N/A"), border=True)
    with kpi3:
        st.metric("Tổng lần kiểm tra", data.get("total_inspections", 0), border=True)
    
    # Tính nhanh tỷ lệ lỗi
    defects = sum(1 for i in inspections if i['prediction'] == 'DEFECTIVE')
    with kpi4:
        st.metric("Số lần phát hiện lỗi", defects, 
                  delta="Cảnh báo" if defects > 0 else "An toàn", 
                  delta_color="inverse", border=True)

    # 5. Thư viện ảnh (Image Gallery)
    st.markdown("### 📸 Lịch sử kiểm tra")
    
    if not inspections:
        st.info("Chưa có dữ liệu hình ảnh cho sản phẩm này.")
        return

    # Tabs phân loại cho dễ nhìn
    tab_all, tab_ng, tab_ok = st.tabs(["Tất cả ảnh", "🔴 Chỉ xem lỗi (NG)", "✅ Chỉ xem OK"])

    def render_gallery(items):
        if not items:
            st.caption("Không có ảnh nào.")
            return
            
        # Grid 4 cột
        cols = st.columns(4)
        for idx, item in enumerate(items):
            with cols[idx % 4]:
                # Container cho từng ảnh (Card style)
                with st.container(border=True):
                    # Ảnh
                    img_url = item.get("image_url") or "https://via.placeholder.com/300?text=No+Image"
                    st.image(img_url, use_container_width=True)
                    
                    # Thông tin dưới ảnh
                    res = item.get("prediction")
                    conf = item.get("confidence", 0) * 100
                    ts = pd.to_datetime(item.get("created_at")).strftime("%H:%M:%S %d/%m")
                    
                    # Badge màu sắc
                    if res == "OK":
                        st.markdown(f":green[**✅ {res}**] - `{conf:.1f}%`")
                    else:
                        st.markdown(f":red[**🔴 {res}**] - `{conf:.1f}%`")
                    
                    st.caption(f"🕒 {ts}")

    with tab_all:
        render_gallery(inspections)
    
    with tab_ng:
        ng_items = [i for i in inspections if i['prediction'] == 'DEFECTIVE']
        render_gallery(ng_items)

    with tab_ok:
        ok_items = [i for i in inspections if i['prediction'] == 'OK']
        render_gallery(ok_items)
    # 1. Lấy Product ID từ Session State hoặc Query Params
    # Ưu tiên lấy từ session_state (do click từ bảng), fallback sang query param (nếu reload trang)
    if 'selected_product_id' in st.session_state:
        product_id = st.session_state.selected_product_id
    else:
        # Lấy từ URL: ?product_id=123
        params = st.query_params
        product_id = params.get("product_id", None)

    if not product_id:
        st.warning("⚠️ Vui lòng chọn một sản phẩm từ Bảng dữ liệu.")
        if st.button("⬅️ Quay lại Bảng dữ liệu"):
             st.session_state.current_page_selection = "table" # Biến điều hướng giả định
             st.rerun()
        return

    st.markdown(f'<p class="main-header">📦 Chi tiết sản phẩm #{product_id}</p>', unsafe_allow_html=True)

    # 2. Gọi API lấy chi tiết
    # Lưu ý: Cần thêm hàm get_product_detail vào QualityInspectorClient trước
    with st.spinner("Đang tải thông tin chi tiết..."):
        # Giả lập gọi API (Bạn cần cập nhật Client thật)
        # response = requests.get(f"{API_URL}/products/{product_id}")
        # data = response.json()
        
        # --- CODE TẠM ĐỂ TEST (Thay bằng code gọi API thật của bạn) ---
        import requests
        try:
             response = requests.get(f"{API_URL}/products/{product_id}", timeout=5)
             if response.status_code == 200:
                 data = response.json()
             else:
                 st.error(f"Lỗi API: {response.status_code}")
                 return
        except Exception as e:
            st.error(f"Lỗi kết nối: {e}")
            return
        # -------------------------------------------------------------

    # 3. Hiển thị thông tin
    info = data.get("product_info", {})
    inspections = data.get("inspections", [])

    # Card thông tin chung
    with st.container(border=True):
        c1, c2, c3 = st.columns(3)
        c1.metric("Mã sản phẩm", info.get("product_code", "N/A"))
        c2.metric("Mã lô (Batch)", info.get("batch_code", "N/A"))
        c3.metric("Tổng lần kiểm tra", data.get("total_inspections", 0))

    st.divider()
    st.subheader("📸 Lịch sử hình ảnh")

    # Hiển thị Gallery ảnh
    if inspections:
        # Chia lưới 3 cột
        cols = st.columns(3)
        for idx, item in enumerate(inspections):
            with cols[idx % 3]:
                # Dùng image_url (Signed URL) từ API
                img_url = item.get("image_url") or "https://via.placeholder.com/150"
                
                st.image(img_url, use_column_width=True)
                
                # Badge trạng thái
                status = item.get("prediction")
                color = "green" if status == "OK" else "red"
                st.markdown(f":{color}[**{status}**] - {float(item.get('confidence',0))*100:.1f}%")
                st.caption(f"🕒 {pd.to_datetime(item.get('created_at')).strftime('%d/%m %H:%M:%S')}")
    else:
        st.info("Sản phẩm này chưa có lịch sử kiểm tra hình ảnh nào.")

    if st.button("⬅️ Quay lại danh sách"):
        # Xóa ID để quay lại trạng thái list
        del st.session_state.selected_product_id
        st.query_params.clear()
        st.rerun()