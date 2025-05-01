"""
Database package for Customer Feedback Form application.
"""

# Database package for Customer Feedback Form
# This file makes the 'database' directory a Python package

__all__ = ['connection', 'models', 'operations']

import streamlit as st

try:
    DB_USER = st.secrets["DB_USER"]
    DB_PASSWORD = st.secrets["DB_PASSWORD"]
    DB_NAME = st.secrets["DB_NAME"]
    DB_HOST = st.secrets.get("DB_HOST", "103.173.18.175")  # fallback default
    DB_PORT = st.secrets.get("DB_PORT", 5432)         # fallback default
except KeyError as e:
    raise RuntimeError(f"Missing key in Streamlit secrets: {e}")

