# utils/helper.py
import streamlit as st
import os


def load_css(file_name: str):
    """Đọc và inject CSS từ file assets"""
    file_path = os.path.join("assets", file_name)
    if os.path.exists(file_path):
        with open(file_path) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    else:
        st.warning(f"CSS file not found: {file_name}")

