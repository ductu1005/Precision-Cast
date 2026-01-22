import streamlit as st
from PIL import Image
import pandas as pd
import time


# Import modules
# Giả sử các module này đã tồn tại như code cũ của bạn
from core.api_client import QualityInspectorClient
# from components.display import show_prediction_result # Không dùng cái cũ nữa vì ta cần hiển thị dạng bảng


def page_upload():
    """Trang 1: Upload và kiểm tra hàng loạt (Batch Inference)"""
    st.markdown('<p class="main-header">🚀 Kiểm tra chất lượng hàng loạt (Batch Inspector)</p>', unsafe_allow_html=True)


    # Layout: Sidebar (Upload) và Main (Kết quả) để tối ưu diện tích cho bảng
    col_upload, col_result = st.columns([1, 2], gap="large")


    # --- Cột trái: Upload & Cấu hình ---
    with col_upload:
        st.subheader("1. Nguồn dữ liệu")
        st.info("💡 Mẹo: Bạn có thể chọn nhiều ảnh cùng lúc hoặc **kéo thả cả một thư mục** ảnh vào ô bên dưới.")
       
        uploaded_files = st.file_uploader(
            "Chọn ảnh hoặc Folder ảnh",
            type=['jpg', 'jpeg', 'png', 'bmp'],
            accept_multiple_files=True  # <--- QUAN TRỌNG: Cho phép nhiều file
        )


        if uploaded_files:
            st.success(f"Đã nhận: {len(uploaded_files)} file ảnh.")
           
            # Hiển thị preview nhanh 1 vài ảnh đầu (nếu muốn)
            with st.expander("🔍 Xem trước danh sách file"):
                file_names = [f.name for f in uploaded_files]
                st.write(file_names)


    # --- Cột phải: Xử lý & Kết quả ---
    with col_result:
        st.subheader("2. Tiến trình & Bảng kết quả")


        # Nút chạy
        run_btn = st.button("⚡ Bắt đầu kiểm tra hàng loạt", type="primary", disabled=not uploaded_files)


        # Placeholder: Nơi chứa bảng kết quả để update liên tục
        status_container = st.container()
        table_placeholder = st.empty()
        metrics_placeholder = st.empty()


        if run_btn and uploaded_files:
            # Khởi tạo list chứa kết quả
            results_data = []
           
            # Thanh tiến trình
            progress_bar = status_container.progress(0)
            status_text = status_container.empty()
           
            total_files = len(uploaded_files)


            # --- VÒNG LẶP XỬ LÝ ---
            for i, file_obj in enumerate(uploaded_files):
                # 1. Cập nhật trạng thái
                status_text.markdown(f"⏳ Đang xử lý: **{file_obj.name}** ({i+1}/{total_files})")
               
                # 2. Gọi API (Giả lập logic gọi API của bạn)
                try:
                    file_obj.seek(0) # Reset con trỏ file
                   
                    # Gọi API thực tế
                    api_result = QualityInspectorClient.predict(file_obj)
                   
                    # Giả sử api_result trả về dict: {'status': 'OK', 'confidence': 0.98, 'defect_type': None}
                    # Ta cần parse nó ra dòng dữ liệu phẳng
                    row = {
                        "Tên file": file_obj.name,
                        "Kết quả": api_result.get("status", "Unknown"), # Ví dụ: OK / NG
                        "Độ tin cậy": f"{api_result.get('confidence', 0)*100:.2f}%",
                        "Loại lỗi": api_result.get("defect_type", "N/A"),
                        "Thời gian": pd.Timestamp.now().strftime("%H:%M:%S")
                    }
                   
                except Exception as e:
                    # Xử lý nếu lỗi kết nối hoặc file hỏng
                    row = {
                        "Tên file": file_obj.name,
                        "Kết quả": "ERROR",
                        "Độ tin cậy": "0%",
                        "Loại lỗi": str(e),
                        "Thời gian": pd.Timestamp.now().strftime("%H:%M:%S")
                    }


                # 3. Thêm vào danh sách tổng
                results_data.append(row)


                # 4. Cập nhật Bảng hiển thị (Real-time update)
                df = pd.DataFrame(results_data)
               
                # Tô màu cho bảng (nếu cần visual đẹp hơn)
                # Ta hiển thị bảng mới nhất lên trên cùng hoặc dưới cùng tùy ý
                table_placeholder.dataframe(
                    df,
                    use_container_width=True,
                    column_config={
                        "Kết quả": st.column_config.TextColumn(
                            "Trạng thái",
                            help="Kết quả từ AI",
                            validate="^(OK|DEFECTIVE|ERROR)$"
                        ),
                    }
                )


                # 5. Cập nhật thanh tiến trình
                progress_bar.progress((i + 1) / total_files)


            # --- KẾT THÚC ---
            status_text.success("✅ Đã hoàn tất kiểm tra toàn bộ danh sách!")
            progress_bar.empty()
           
            # Tổng hợp thống kê nhanh
            total_ok = len(df[df['Kết quả'] == 'OK'])
            total_ng = len(df[df['Kết quả'] == 'DEFECTIVE'])
           
            metrics_placeholder.markdown(f"""
            ### 📊 Tổng kết:
            - **Tổng số ảnh:** {total_files}
            - <span style="color:green">**OK:** {total_ok}</span>
            - <span style="color:red">**DEFECTIVE:** {total_ng}</span>
            """, unsafe_allow_html=True)


        elif not uploaded_files:
            # Màn hình chờ
            st.info("👈 Vui lòng upload ảnh hoặc folder ở cột bên trái.")
            st.markdown(
                """
                <div style="text-align: center; opacity: 0.5; margin-top: 50px;">
                    <h2>Waiting for batch input...</h2>
                    <p>Hệ thống sẵn sàng quét hàng loạt</p>
                </div>
                """, unsafe_allow_html=True
            )
