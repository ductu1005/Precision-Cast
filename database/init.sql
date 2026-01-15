-- PrecisionCast Database Schema
-- MariaDB initialization script

-- Tạo database nếu chưa tồn tại
CREATE DATABASE IF NOT EXISTS precisioncast CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE precisioncast;

-- Bảng thông tin sản phẩm được kiểm tra
CREATE TABLE IF NOT EXISTS products
(
    id           BIGINT AUTO_INCREMENT PRIMARY KEY,
    product_code VARCHAR(50) COMMENT 'Mã sản phẩm',
    batch_code   VARCHAR(50) COMMENT 'Mã lô sản xuất',
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
    ENGINE = InnoDB
    COMMENT ='Thông tin sản phẩm được kiểm tra';

-- Bảng kết quả kiểm tra chất lượng
CREATE TABLE IF NOT EXISTS inspection_results
(
    id           BIGINT AUTO_INCREMENT PRIMARY KEY,
    product_id   BIGINT COMMENT 'Tham chiếu tới sản phẩm được kiểm tra',
    image_path   TEXT                     NOT NULL COMMENT 'Đường dẫn ảnh',
    prediction   ENUM ('ok', 'defective') NOT NULL COMMENT 'Kết quả dự đoán của AI',
    confidence   DECIMAL(5, 4) COMMENT 'Độ tin cậy của dự đoán (0-1)',
    inspected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT 'Thời điểm AI thực hiện inference',
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE SET NULL
)
    ENGINE = InnoDB
    COMMENT ='Kết quả kiểm tra chất lượng sản phẩm bằng AI';

-- Bảng log chi tiết quá trình suy luận
CREATE TABLE IF NOT EXISTS prediction_logs
(
    id                BIGINT AUTO_INCREMENT PRIMARY KEY,
    inspection_id     BIGINT COMMENT 'Tham chiếu tới kết quả kiểm tra',
    raw_score         FLOAT COMMENT 'Giá trị raw output từ model (logit/sigmoid)',
    threshold         FLOAT COMMENT 'Ngưỡng phân loại dùng tại thời điểm inference',
    inference_time_ms INT COMMENT 'Thời gian suy luận (ms)',
    created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT 'Thời điểm ghi log',
    FOREIGN KEY (inspection_id) REFERENCES inspection_results(id) ON DELETE CASCADE
)
    ENGINE = InnoDB
    COMMENT ='Log chi tiết quá trình suy luận của mô hình AI';

-- Tạo indexes
CREATE INDEX idx_products_batch_code ON products(batch_code);
CREATE INDEX idx_products_created_at ON products(created_at);
CREATE INDEX idx_inspection_results_product_id ON inspection_results(product_id);
CREATE INDEX idx_inspection_results_prediction ON inspection_results(prediction);
CREATE INDEX idx_inspection_results_inspected_at ON inspection_results(inspected_at);
CREATE INDEX idx_prediction_logs_inspection_id ON prediction_logs(inspection_id);

