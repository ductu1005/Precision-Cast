# Database Schema

Thư mục này chứa các file SQL schema cho database MariaDB.

## Files

- `init.sql`: Script khởi tạo database và các bảng

## Cấu trúc Database

### Bảng `products`
Lưu thông tin sản phẩm được kiểm tra:
- `id`: Primary key
- `product_code`: Mã sản phẩm
- `batch_code`: Mã lô sản xuất
- `created_at`: Thời điểm tạo

### Bảng `inspection_results`
Lưu kết quả kiểm tra chất lượng:
- `id`: Primary key
- `product_id`: Foreign key tới `products.id`
- `image_path`: Đường dẫn ảnh trong MinIO
- `prediction`: Kết quả dự đoán ('ok' hoặc 'defective')
- `confidence`: Độ tin cậy (0-1)
- `inspected_at`: Thời điểm inference
- `created_at`: Thời điểm tạo record

### Bảng `prediction_logs`
Lưu log chi tiết quá trình suy luận:
- `id`: Primary key
- `inspection_id`: Foreign key tới `inspection_results.id`
- `raw_score`: Raw output từ model
- `threshold`: Ngưỡng phân loại
- `inference_time_ms`: Thời gian inference (ms)
- `created_at`: Thời điểm ghi log

## Sử dụng

Script `init.sql` sẽ tự động chạy khi container MariaDB khởi động lần đầu (nếu mount vào `/docker-entrypoint-initdb.d/`).

