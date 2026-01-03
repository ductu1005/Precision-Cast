**PrecisionCast** là một công ty sản xuất các cánh bơm chìm (submersible pump impellers). Hiện tại, quy trình kiểm tra chất lượng (QC) của họ đang được thực hiện thủ công, chậm và dễ xảy ra lỗi.

Nhiệm vụ của bạn là thiết kế và xây dựng một hệ thống phần mềm nguyên mẫu (prototype) để **tự động hóa quy trình kiểm tra bằng thị giác máy tính (Computer Vision)**.

Hệ thống phải nhận vào một hình ảnh của sản phẩm đúc và xác định xem nó là **“Defective” (Lỗi)** hay **“OK”** với độ tin cậy cao.

Không giống như một dự án khoa học dữ liệu thuần túy, mục tiêu của bạn không chỉ là huấn luyện một mô hình, mà còn phải **kỹ nghệ hóa (engineer) một sản phẩm phần mềm có thể triển khai thực tế**.

Bạn cũng phải **tài liệu hóa những thay đổi tư duy cơ bản** khi chuyển từ **Kỹ nghệ phần mềm (SE)** mang tính xác định sang **Kỹ nghệ AI** mang tính xác suất.

---

# **Dataset**

Bạn sẽ sử dụng tập dữ liệu **Casting Product Image Data for Quality Inspection** (Dữ liệu hình ảnh sản phẩm đúc phục vụ kiểm tra chất lượng – dữ liệu công nghiệp thực tế).

- **Nguồn:** Kaggle – *Casting Product Image Data*
- **Loại dữ liệu:** Hình ảnh grayscale 512x512
- **Phân lớp:**
    - *defective*
    - *ok_front*

---

# **Yêu cầu Kỹ thuật & Kiến trúc**

Sản phẩm cuối phải bao gồm **3 thành phần riêng biệt**, được tích hợp trong cùng một pipeline:

---

## **Component A: Mô hình AI (The “Brain”)**

- **Công nghệ:** Python, TensorFlow/Keras hoặc PyTorch
- **Nhiệm vụ:** Huấn luyện một mô hình CNN để phân loại ảnh
- **Yêu cầu:** Phải có **Data Augmentation** để tăng khả năng khái quát
- **Đánh giá:** Accuracy, Precision, Recall, Confusion Matrix

---

## **Component B: Bộ máy suy luận (Inference Engine – “Backend”)**

- **Công nghệ:** FastAPI hoặc Flask
- **Nhiệm vụ:** Triển khai REST API phục vụ mô hình đã huấn luyện
- **API Endpoint:**
    
    `POST /predict`
    
    Nhận ảnh → Trả về JSON:
    
    ```json
    {
      "status": "defective",
      "confidence": 0.95
    }
    
    ```
    

---

## **Component C: Giao diện người dùng (Frontend)**

- **Công nghệ:** Streamlit (đề xuất) hoặc React
- **Nhiệm vụ:**
    
    Giao diện web để công nhân nhà máy upload hình ảnh và xem kết quả
    
    - Màu **đỏ** nếu sản phẩm *defective*
    - Màu **xanh** nếu sản phẩm *OK*

---

## **Component D: Hạ tầng (Infrastructure)**

- **Công nghệ:** Docker
- **Nhiệm vụ:**
    
    Toàn bộ ứng dụng (Backend + Frontend) phải được **đóng gói container**.