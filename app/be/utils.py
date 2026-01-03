"""
Utility functions cho backend
"""

import os
from pathlib import Path

def ensure_model_directory():
    """Tạo thư mục models nếu chưa tồn tại"""
    model_dir = Path("models")
    model_dir.mkdir(exist_ok=True)
    return model_dir

