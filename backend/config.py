# Configuration file for Digital Watermarking Application

# API Configuration
API_HOST = '0.0.0.0'
API_PORT = 5000
DEBUG_MODE = True

# File Upload Configuration
MAX_FILE_SIZE_MB = 16
ALLOWED_EXTENSIONS = ['png', 'jpg', 'jpeg', 'bmp']

# Cryptography Configuration
PRIVATE_KEY_PATH = 'data/keys/private.pem'
PUBLIC_KEY_PATH = 'data/keys/public.pem'

# Watermarking Configuration
DEFAULT_BLOCK_SIZE = 8
MIN_BLOCK_SIZE = 2
MAX_BLOCK_SIZE = 64

# DWT Configuration
WAVELET_TYPE = 'haar'  # Options: 'haar', 'db1', 'db2', etc.

# Paths
UPLOAD_FOLDER = 'temp'
WATERMARKED_FOLDER = 'data/watermarked'

# CORS Configuration
CORS_ORIGINS = ['http://localhost:3000', 'http://127.0.0.1:3000']

