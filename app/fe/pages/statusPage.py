import streamlit as st
import pandas as pd

# Import modules
from core.api_client import load_inspection_data

def page_stats_table():
    st.markdown("### 📊 Dữ liệu chi tiết")
    df = load_inspection_data() # Gọi hàm cache
    
    if df.empty:
        st.info("Chưa có dữ liệu.")
        return

    # Tạo bản sao để hiển thị (format đẹp)
    display_df = df.copy()
    display_df['confidence_display'] = display_df['confidence'].apply(lambda x: f"{x*100:.1f}%")
    
    # Sắp xếp mới nhất trước
    display_df = display_df.sort_values(by='id', ascending=False)
    
    st.dataframe(
        display_df[['id', 'prediction', 'confidence_display', 'created_at', 'image_path']],
        column_config={
            "created_at": st.column_config.DatetimeColumn("Thời gian", format="DD/MM HH:mm"),
            "image_path": "File Ảnh"
        },
        use_container_width=True,
        hide_index=True
    )

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
    st.markdown('<p class="main-header">🎯 Đánh giá hiệu suất Model (Evaluation)</p>', unsafe_allow_html=True)
    
    # 1. Load dữ liệu từ cache
    df = load_inspection_data()
    
    if df.empty:
        st.warning("Chưa có dữ liệu để đánh giá.")
        return

    # 2. Xử lý dữ liệu: Trích xuất Ground Truth từ tên file
    # Quy tắc: cast_ok_... -> OK, cast_def_... -> DEFECTIVE
    def extract_ground_truth(filename):
        if not isinstance(filename, str):
            return None
        filename = filename.lower()
        if "cast_ok" in filename:
            return "OK"
        elif "cast_def" in filename:
            return "DEFECTIVE"
        return None # Skip file không đúng định dạng

    # Tạo cột ground_truth
    eval_df = df.copy()
    eval_df['ground_truth'] = eval_df['image_path'].apply(extract_ground_truth)
    
    # 3. Lọc bỏ các ảnh không xác định được nhãn (Tập Test)
    eval_df = eval_df.dropna(subset=['ground_truth'])
    
    if eval_df.empty:
        st.info("Không tìm thấy ảnh nào thuộc tập Test (có tên 'cast_ok' hoặc 'cast_def').")
        return

    # 4. Chấm điểm: Tạo cột kết quả (Đúng/Sai)
    eval_df['is_correct'] = eval_df['prediction'] == eval_df['ground_truth']
    eval_df['result_type'] = eval_df.apply(
        lambda row: "Correct" if row['is_correct'] else "Incorrect", axis=1
    )

    # --- HIỂN THỊ METRICS ---
    total_test = len(eval_df)
    correct_count = eval_df['is_correct'].sum()
    accuracy = correct_count / total_test
    
    # Tính Precision/Recall cho lỗi (Defective) - Chỉ số quan trọng trong sản xuất
    # TP: Thực tế lỗi, AI báo lỗi
    tp = len(eval_df[(eval_df['ground_truth'] == 'DEFECTIVE') & (eval_df['prediction'] == 'DEFECTIVE')])
    # FN: Thực tế lỗi, AI báo OK (Nguy hiểm nhất)
    fn = len(eval_df[(eval_df['ground_truth'] == 'DEFECTIVE') & (eval_df['prediction'] == 'OK')])
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Số lượng mẫu Test", total_test)
    col2.metric("Độ chính xác (Accuracy)", f"{accuracy*100:.2f}%")
    col3.metric("Bắt đúng lỗi (TP)", tp)
    col4.metric("Bỏ sót lỗi (FN)", fn, delta_color="inverse")

    st.divider()

    # --- BIỂU ĐỒ MỨC ĐỘ TIN TƯỞNG (CONFIDENCE ANALYSIS) ---
    st.subheader("🔍 Phân tích độ tin cậy (Confidence Analysis)")
    st.caption("Biểu đồ này giúp bạn xem khi AI đúng/sai thì nó tự tin đến mức nào.")

    # Cách 1: Dùng Streamlit Native (Scatter Chart)
    # Trục X: Index, Trục Y: Confidence, Màu sắc: Kết quả Đúng/Sai
    
    # Chuẩn bị data cho biểu đồ
    chart_data = eval_df[['confidence', 'result_type', 'prediction', 'ground_truth']].copy()
    
    # Vẽ Scatter plot để thấy phân bố
    st.scatter_chart(
        chart_data,
        y='confidence',
        color='result_type', # Màu xanh/đỏ tự động phân biệt Correct/Incorrect
        height=400,
        size=100  # Kích thước điểm
    )
    
    # --- PHÂN TÍCH CHI TIẾT ---
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Ma trận nhầm lẫn (Confusion)")
        # Tạo bảng thống kê đơn giản
        confusion = pd.crosstab(
            eval_df['ground_truth'], 
            eval_df['prediction'], 
            rownames=['Thực tế (Actual)'], 
            colnames=['Dự đoán (Predicted)']
        )
        st.dataframe(confusion, use_container_width=True)
        
    with c2:
        st.subheader("Danh sách dự đoán sai")
        wrong_preds = eval_df[~eval_df['is_correct']][['image_path', 'ground_truth', 'prediction', 'confidence']]
        if not wrong_preds.empty:
            st.dataframe(
                wrong_preds,
                column_config={
                    "confidence": st.column_config.NumberColumn("Confidence", format="%.4f")
                },
                use_container_width=True
            )
        else:
            st.success("Tuyệt vời! Model chưa dự đoán sai mẫu nào.")