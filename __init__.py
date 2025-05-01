"""
Database package for Customer Feedback Form application.
"""

# Database package for Customer Feedback Form
# This file makes the 'database' directory a Python package

__all__ = ['connection', 'models', 'operations'] 
import toml
import os

# Construct path to secrets.toml in the project root
secrets_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "secrets.toml")

# Load secrets only if the file exists
if os.path.exists(secrets_path):
    secrets = toml.load(secrets_path)
    DB_USER = secrets.get("DB_USER")
    DB_PASSWORD = secrets.get("DB_PASSWORD")
    DB_NAME = secrets.get("DB_NAME")
    DB_HOST = secrets.get("DB_HOST", "localhost")  # fallback default
    DB_PORT = secrets.get("DB_PORT", 5432)         # fallback default
else:
    raise FileNotFoundError("secrets.toml file not found.")
