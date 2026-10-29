"""Keep the API key in Streamlit Secrets or environment variables."""
import os

BASE_URL = "https://api.siliconflow.cn/v1"
MODEL = "Qwen/Qwen2.5-7B-Instruct"


def get_settings():
    import streamlit as st
    try:
        secrets = st.secrets
        key = secrets.get("API_KEY", "") or os.getenv("API_KEY", "")
        base_url = secrets.get("BASE_URL", "") or os.getenv("BASE_URL", BASE_URL)
        model = secrets.get("MODEL", "") or os.getenv("MODEL", MODEL)
    except (FileNotFoundError, KeyError):
        key = os.getenv("API_KEY", "")
        base_url = os.getenv("BASE_URL", BASE_URL)
        model = os.getenv("MODEL", MODEL)
    return str(key).strip(), str(base_url).strip(), str(model).strip()
