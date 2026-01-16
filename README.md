# PrecisionCast - Quality Inspection System

🔍 **Hệ thống kiểm tra chất lượng tự động sử dụng Computer Vision**

PrecisionCast là một hệ thống phần mềm nguyên mẫu (prototype) để tự động hóa quy trình kiểm tra chất lượng sản phẩm đúc (casting products) bằng thị giác máy tính. Hệ thống phân loại sản phẩm thành **"Defective" (Lỗi)** hoặc **"OK"** với độ tin cậy cao.

---

## 📋 Mục lục

- [Kiến trúc hệ thống](#kiến-trúc-hệ-thống)
- [Cấu trúc dự án](#cấu-trúc-dự-án)
- [Yêu cầu hệ thống](#yêu-cầu-hệ-thống)
- [Cài đặt và chạy](#cài-đặt-và-chạy)
- [API Documentation](#api-documentation)
- [Development](#development)
- [Deployment](#deployment)

---

## 🏗️ Kiến trúc hệ thống

Hệ thống bao gồm 3 thành phần chính:

### **Component A: Mô hình AI (The "Brain")**
- CNN model để phân loại ảnh (Defective/OK)
- Data Augmentation để tăng khả năng khái quát
- Được huấn luyện trong `/notebooks`

### **Component B: Inference Engine (Backend)**
- **FastAPI** REST API
- Endpoint: `POST /predict`
- Nhận ảnh → Trả về JSON với status và confidence

### **Component C: Frontend UI**
- **Streamlit** web interface
- Upload ảnh và hiển thị kết quả
- Màu đỏ cho Defective, màu xanh cho OK

### **Component D: Infrastructure**
- **Docker** containerization
- Docker Compose để orchestrate services

---

## 📁 Cấu trúc dự án

```
Precision-Cast/
├── notebooks/              # Jupyter notebooks cho EDA và training model
├── app/
│   ├── be/                # Backend (FastAPI)
│   │   ├── main.py        # FastAPI application
│   │   ├── model_loader.py # Model loading và inference
│   │   ├── utils.py       # Utility functions
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   └── fe/                # Frontend (Streamlit)
│       ├── main.py        # Streamlit application
│       ├── requirements.txt
│       └── Dockerfile
├── models/                # Thư mục chứa model đã train (.h5 file)
├── docker-compose.yml     # Docker Compose configuration
├── .dockerignore
└── README.md
```

---

## 💻 Yêu cầu hệ thống

- **Python**: 3.11+
- **Docker**: 20.10+ (nếu dùng Docker)
- **Docker Compose**: 2.0+ (nếu dùng Docker)
- **RAM**: Tối thiểu 4GB (khuyến nghị 8GB)
- **GPU**: Không bắt buộc, nhưng khuyến nghị cho training

---

## 🚀 Cài đặt và chạy

### **Cách 1: Chạy với Docker (Khuyến nghị)**

1. **Clone repository:**
```bash
git clone <repository-url>
cd Precision-Cast
```

2. **Chuẩn bị model:**
   - Đặt file model đã train vào thư mục `models/`
   - File model nên có tên: `casting_classifier.h5`
   - Nếu chưa có model, backend sẽ tạo dummy model để test

3. **Chạy với Docker Compose:**
```bash
docker-compose up --build
```

4. **Truy cập ứng dụng:**
   - **Frontend**: http://localhost:8501
   - **Backend API**: http://localhost:8000
   - **API Docs**: http://localhost:8000/docs

5. **Dừng services:**
```bash
docker-compose down
```

### **Cách 2: Chạy thủ công (Development)**

#### **Backend:**

1. **Tạo virtual environment:**
```bash
cd app/be
python -m venv venv
source venv/bin/activate  # Trên Windows: venv\Scripts\activate
```

2. **Cài đặt dependencies:**
```bash
pip install -r requirements.txt
```

3. **Chạy backend:**
```bash
python main.py
# hoặc
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Backend sẽ chạy tại: http://localhost:8000

#### **Frontend:**

1. **Tạo virtual environment:**
```bash
cd app/fe
python -m venv venv
source venv/bin/activate  # Trên Windows: venv\Scripts\activate
```

2. **Cài đặt dependencies:**
```bash
pip install -r requirements.txt
```

3. **Chạy frontend:**
```bash
streamlit run main.py
```

Frontend sẽ chạy tại: http://localhost:8501

**Lưu ý:** Đảm bảo backend đang chạy trước khi chạy frontend!

---

## 📡 API Documentation

### **Base URL:**
```
http://localhost:8000
```

### **Endpoints:**

#### **1. Health Check**
```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "model_loaded": true
}
```

#### **2. Predict (Main Endpoint)**
```http
POST /predict
Content-Type: multipart/form-data
```

**Request:**
- File upload: `file` (image file)

**Response:**
```json
{
  "status": "defective",  // hoặc "ok"
  "confidence": 0.95      // 0.0 - 1.0
}
```

**Example với curl:**
```bash
curl -X POST "http://localhost:8000/predict" \
  -F "file=@path/to/image.jpg"
```

**Example với Python:**
```python
import requests

url = "http://localhost:8000/predict"
files = {"file": open("image.jpg", "rb")}
response = requests.post(url, files=files)
print(response.json())
```

#### **3. API Documentation (Swagger UI)**
Truy cập: http://localhost:8000/docs

---

## 🔧 Development

### **Cấu hình môi trường:**

#### **Backend:**
- `MODEL_PATH`: Đường dẫn đến file model (mặc định: `models/casting_classifier.h5`)

#### **Frontend:**
- `API_URL`: URL của backend API (mặc định: `http://localhost:8000`)

### **Thêm model mới:**

1. Train model trong `/notebooks`
2. Export model thành file `.h5`
3. Đặt file vào thư mục `models/`
4. Cập nhật `MODEL_PATH` nếu cần

### **Testing:**

#### **Test Backend:**
```bash
cd app/be
pytest  # (cần thêm test files)
```

#### **Test API với curl:**
```bash
curl -X POST "http://localhost:8000/predict" \
  -F "file=@test_image.jpg"
```

---

## 🐳 Deployment

### **Docker Production:**

1. **Build images:**
```bash
docker-compose build
```

2. **Run với production settings:**
```bash
docker-compose -f docker-compose.yml up -d
```

3. **View logs:**
```bash
docker-compose logs -f
```

### **Environment Variables:**

Tạo file `.env` hoặc set environment variables:

```env
# Backend
MODEL_PATH=models/casting_classifier.h5

# Frontend
API_URL=http://backend:8000
```

---

## 📊 Dataset

- **Nguồn:** Kaggle - Casting Product Image Data
- **Loại:** Grayscale images 512x512
- **Classes:** 
  - `defective`
  - `ok_front`

---

## 🛠️ Technologies

- **Backend:** FastAPI, TensorFlow/Keras, Uvicorn
- **Frontend:** Streamlit
- **ML:** TensorFlow/Keras
- **Containerization:** Docker, Docker Compose
- **Language:** Python 3.11+

---

## 👥 Phân chia vai trò

1. **ML Lead**: Xử lý dữ liệu, xây dựng model, đánh giá
2. **Backend/Ops Engineer**: API, Docker, performance
3. **Frontend/Integration Engineer**: UI, UX, integration

---

## 📝 Notes

- **Dummy Model**: Backend sẽ tạo dummy model nếu không tìm thấy model file. Trong production, phải thay bằng model thật.
- **CORS**: Hiện tại CORS cho phép tất cả origins. Trong production nên giới hạn.
- **Model Path**: Đảm bảo model file được đặt đúng đường dẫn.

---

## 📄 License

Dự án course project - PrecisionCast Quality Inspection System

---

## 🤝 Contributing

Đây là dự án course project. Vui lòng liên hệ team lead để đóng góp.

---

## 📧 Contact

Team PrecisionCast
