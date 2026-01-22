import streamlit as st
import pandas as pd


# Import modules
from core.api_client import load_inspection_data


def change_page(direction):
    if direction == "next":
        st.session_state.current_page += 1
    elif direction == "prev":
        st.session_state.current_page -= 1


def page_stats_table():
    st.markdown('<p class="main-header">📊 Dữ liệu chi tiết</p>', unsafe_allow_html=True)


    # 1. Khởi tạo state và cấu hình trang
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 1
       
    col_conf, _ = st.columns([1, 4])
    with col_conf:
        rows_per_page = st.selectbox("Số dòng/trang:", [10, 20, 50], index=0)


    # 2. Tính toán skip và Load dữ liệu
    skip_val = (st.session_state.current_page - 1) * rows_per_page
   
    with st.spinner(f"Đang tải dữ liệu..."):
        df = load_inspection_data(skip=skip_val, limit=rows_per_page)


    # 3. HIỂN THỊ BẢNG (Đã sửa lỗi Type Compatibility)
    if not df.empty:
        # --- FIX LỖI Ở ĐÂY ---
        display_df = df.copy()


        # A. Ép kiểu thời gian từ String sang Datetime object
        if 'created_at' in display_df.columns:
            display_df['created_at'] = pd.to_datetime(display_df['created_at'], errors='coerce')


        # B. Format cột độ tin cậy (nếu có)
        if 'confidence' in display_df.columns:
            # Đảm bảo là số trước khi format
            display_df['confidence'] = pd.to_numeric(display_df['confidence'], errors='coerce')
            display_df['confidence_display'] = display_df['confidence'].apply(
                lambda x: f"{x*100:.1f}%" if pd.notnull(x) else "0%"
            )
           
        # C. Xử lý image_path để đảm bảo là URL hợp lệ
        # Backend trả về image_path là presigned URL, nhưng cần đảm bảo không None
        if 'image_path' in display_df.columns:
            # Thay thế None hoặc giá trị rỗng bằng placeholder
            display_df['image_path'] = display_df['image_path'].apply(
                lambda x: x if x and str(x).startswith('http') else None
            )
        
        # D. Hiển thị Data Editor
        st.data_editor(
            display_df,
            column_config={
                # Cột ảnh - image_path đã là presigned URL từ backend
                "image_path": st.column_config.ImageColumn(
                    "Ảnh minh họa",
                    width="small",
                    help="Ảnh chụp từ camera (click để xem lớn)"
                ),
                # Cột thời gian (Bây giờ đã an toàn vì dữ liệu là datetime object)
                "created_at": st.column_config.DatetimeColumn(
                    "Thời gian",
                    format="DD/MM/YYYY HH:mm:ss",
                    width="medium"
                ),
                # Các cột khác
                "prediction": st.column_config.TextColumn("Kết quả"),
                "confidence_display": st.column_config.TextColumn("Độ tin cậy"),
            },
            # Chỉ định hiển thị các cột cần thiết, ẩn các cột thừa
            column_order=["id", "image_path", "prediction", "confidence_display", "created_at"],
            use_container_width=True,
            hide_index=True,
            disabled=True, # Không cho chỉnh sửa
            key=f"editor_{st.session_state.current_page}" # Key unique để tránh lỗi khi reload
        )
    else:
        st.warning(f"Không có dữ liệu ở trang {st.session_state.current_page}.")


    # 4. THANH ĐIỀU HƯỚNG (Pagination Controls) - Giữ nguyên logic cũ
    st.divider()
    c1, c2, c3 = st.columns([1, 2, 1])


    # Hàm callback chuyển trang (định nghĩa bên ngoài hoặc trên cùng file)
    def change_page(direction):
        if direction == "next":
            st.session_state.current_page += 1
        elif direction == "prev":
            st.session_state.current_page -= 1


    with c1:
        st.button("⬅️ Trang trước",
                  disabled=(st.session_state.current_page <= 1),
                  use_container_width=True,
                  on_click=change_page, args=("prev",))


    with c2:
        st.markdown(f"<div style='text-align: center; margin-top: 10px;'>Trang <b>{st.session_state.current_page}</b></div>", unsafe_allow_html=True)


    with c3:
        is_last_page = len(df) < rows_per_page
        st.button("Trang sau ➡️",
                  disabled=is_last_page,
                  use_container_width=True,
                  on_click=change_page, args=("next",))


def page_stats_charts():
    """Trang 2.2: Biểu đồ thống kê"""
    st.markdown('<p class="main-header">📈 Phân tích xu hướng (Analytics)</p>', unsafe_allow_html=True)
   
    df = load_inspection_data()
   
    if not df.empty:
        # Layout metrics
        col1, col2, col3 = st.columns(3)
        total = len(df)
        ok_count = len(df[df['prediction'] == 'OK'])
        ng_count = len(df[df['prediction'] == 'DEFECTIVE']) # hoặc 'DEFECTIVE' tùy DB
       
        col1.metric("Tổng sản phẩm", total)
        col2.metric("Sản phẩm OK", ok_count, delta=f"{(ok_count/total)*100:.1f}%")
        col3.metric("Sản phẩm Lỗi (NG)", ng_count, delta=f"-{(ng_count/total)*100:.1f}%", delta_color="inverse")
       
        st.divider()
       
        # Layout biểu đồ
        chart_col1, chart_col2 = st.columns(2)
       
        with chart_col1:
            st.subheader("Tỷ lệ lỗi (Pie Chart)")
            # Tạo dataframe cho biểu đồ tròn
            pie_data = pd.DataFrame({
                "Status": ["OK", "Defective"],
                "Count": [ok_count, ng_count]
            })
            # Streamlit chưa có pie chart native xịn, dùng bar chart thay thế hoặc altair
            st.bar_chart(pie_data.set_index("Status"), color=["#2ecc71"]) # Màu xanh
           
        with chart_col2:
            st.subheader("Độ tin cậy trung bình (Confidence)")
            if 'confidence' in df.columns:
                # Convert confidence to numeric just in case
                df['confidence'] = pd.to_numeric(df['confidence'])
                st.line_chart(df['confidence'])
                st.caption("Biến động độ tự tin của AI qua các lần kiểm tra")


    else:
        st.warning("Chưa có dữ liệu để vẽ biểu đồ.")


def page_model_evaluation():
    st.markdown('<p class="main-header">🎯 Đánh giá hiệu suất Model</p>', unsafe_allow_html=True)
    
    # 1. Cấu hình Limit
    with st.expander("⚙️ Cấu hình lấy dữ liệu", expanded=False):
        limit_rows = st.slider(
            "Số lượng mẫu gần nhất cần đánh giá:",
            min_value=50, max_value=2000, value=200, step=50
        )
    
    # 2. Load dữ liệu (Truyền limit_rows vào hàm)
    with st.spinner("Đang tải và tính toán..."):
        # Lưu ý: Hàm load_inspection_data phải chấp nhận tham số limit như code ở bước 1
        df = load_inspection_data(limit=limit_rows)
    
    # 3. Kiểm tra dữ liệu rỗng
    if df.empty:
        st.warning("Không có dữ liệu để đánh giá.")
        return

    # 4. Xử lý Ground Truth (ĐÃ SỬA LOGIC TẠI ĐÂY)
    def extract_ground_truth(filename):
        if not isinstance(filename, str): return None
        s = filename.lower()
        
        # Logic mapping: Phải khớp 100% với output của Model
        if "cast_ok" in s: 
            return "OK"
        if "cast_def" in s: 
            return "DEFECTIVE" # <--- Đã sửa: NG thành DEFECTIVE
            
        return None

    # Tạo cột ground_truth
    eval_df = df.copy()
    eval_df['ground_truth'] = eval_df['image_path'].apply(extract_ground_truth)
    
    # Bỏ các ảnh không có nhãn (Tập dữ liệu thực tế không tuân thủ quy tắc đặt tên)
    eval_df = eval_df.dropna(subset=['ground_truth'])
    
    if eval_df.empty:
        st.info("Dữ liệu tải về không chứa thông tin nhãn thực tế (tên file không chứa 'cast_ok' hoặc 'cast_def').")
        return

    # 5. Tính toán Đúng/Sai
    # Lúc này so sánh mới chính xác vì cả 2 đều là 'DEFECTIVE'
    eval_df['is_correct'] = eval_df['prediction'] == eval_df['ground_truth']
    
    # Tạo cột màu sắc/nhãn để hiển thị biểu đồ cho đẹp
    eval_df['result_label'] = eval_df['is_correct'].map({True: 'Đúng (Correct)', False: 'Sai (Incorrect)'})

    # 6. Metrics & Charts
    acc = eval_df['is_correct'].mean()
    total = len(eval_df)
    wrong_count = int(total - eval_df['is_correct'].sum())
    
    # Layout Metrics
    m1, m2, m3 = st.columns(3)
    m1.metric("Tổng mẫu đánh giá", total)
    m2.metric("Độ chính xác (Accuracy)", f"{acc*100:.1f}%")
    m3.metric("Số mẫu sai", wrong_count, delta_color="inverse")
    
    st.divider()
    
    # Chart phân bố
    st.subheader("Phân bố độ tin cậy (Confidence Distribution)")
    st.caption("Biểu đồ giúp phát hiện: Những mẫu AI đoán sai nhưng lại rất tự tin (Điểm đỏ ở trên cao).")
    
    st.scatter_chart(
        eval_df,
        y='confidence',
        x='id', # Rải theo ID hoặc thời gian để dễ nhìn
        color='result_label', # Dùng label tiếng Việt đã map ở trên
        size=50,
        height=400
    )

    # Hiển thị bảng chi tiết các case sai
    if wrong_count > 0:
        st.subheader(f"⚠️ Danh sách {wrong_count} trường hợp dự đoán sai")
        wrong_df = eval_df[~eval_df['is_correct']]
        
        st.dataframe(
            wrong_df[['image_path', 'prediction', 'ground_truth', 'confidence']],
            use_container_width=True,
            column_config={
                "image_path": "Tên file",
                "prediction": "AI Dự đoán",
                "ground_truth": "Thực tế",
                "confidence": st.column_config.ProgressColumn(
                    "Độ tin cậy", 
                    min_value=0, 
                    max_value=1,
                    format="%.2f"
                )
            }
        )
    else:
        st.balloons() # Thả bóng bay chúc mừng
        st.success("Tuyệt vời! Model chính xác 100% trên tập dữ liệu này!")