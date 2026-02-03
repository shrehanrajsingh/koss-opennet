# VulnNet Configuration
# INTENTIONALLY INSECURE - For educational purposes only

import os

# Hardcoded secret key (vulnerability: exposed secret)
SECRET_KEY = 'super_secret_key_12345'

# Database configuration
DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'vulnnet.db')

# Upload configuration (no restrictions - vulnerability)
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB

# Session configuration (intentionally insecure)
SESSION_COOKIE_HTTPONLY = False  # Vulnerability: XSS can steal cookies
SESSION_COOKIE_SECURE = False    # Vulnerability: cookies sent over HTTP
SESSION_COOKIE_SAMESITE = None   # Vulnerability: CSRF possible

# Debug mode (vulnerability: exposes stack traces)
DEBUG = True

# Admin credentials (hardcoded - vulnerability)
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'admin123'
