# Backend Dockerfile - FastAPI
FROM python:3.11-slim

WORKDIR /app

# Cài đặt system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements và cài đặt dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Tạo thư mục models nếu chưa có
RUN mkdir -p models

# Expose port
EXPOSE 8000

# Command để chạy ứng dụng
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

