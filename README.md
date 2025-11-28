# Digital Watermarking System

A robust digital watermarking application for image authentication and copyright protection using hybrid DWT+DCT embedding and RSA-2048 cryptographic signatures.

## Overview

This system embeds invisible, cryptographically-signed watermarks into images for authenticity verification and tamper detection. Designed for museums, archives, photographers, and institutions protecting digital image collections.

### Key Features

- **Invisible Watermarking**: Hybrid DWT+DCT algorithm for imperceptible embedding
- **Cryptographic Security**: RSA-2048 digital signatures with PSS padding
- **Modern UI**: React/TypeScript frontend with real-time preview
- **REST API**: Easy integration with existing workflows
- **Batch Processing**: Handle multiple images efficiently
- **Auto-Detection**: Automatic block size detection during verification
- **High Capacity**: Embed substantial metadata (varies by image size)

## Architecture

```
┌─────────────────────────────────────────────┐
│     Frontend (React + TypeScript)           │
│  ┌──────────────┐    ┌──────────────┐     │
│  │  Embed Tab   │    │  Verify Tab  │     │
│  └──────────────┘    └──────────────┘     │
└──────────────┬──────────────────────────────┘
               │ HTTP REST API
┌──────────────▼──────────────────────────────┐
│       Backend (Flask + Python)              │
│  ┌────────────────────────────────┐        │
│  │      REST API Endpoints        │        │
│  └────────────────────────────────┘        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐ │
│  │  Crypto  │  │Watermark │  │  Utils   │ │
│  │  (RSA)   │  │(DWT+DCT) │  │          │ │
│  └──────────┘  └──────────┘  └──────────┘ │
└─────────────────────────────────────────────┘
```

## Requirements

### Backend
- Python 3.8+
- pip package manager

### Frontend
- Node.js 14+
- npm or yarn

## Installation

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/digital_watermarking_project.git
cd digital_watermarking_project
```

### 2. Backend Setup

```bash
cd backend
pip install -r requirements.txt
python api.py
```

Backend will start on `http://localhost:5000`

### 3. Frontend Setup (new terminal)

```bash
cd frontend
npm install
npm start
```

Frontend will start on `http://localhost:3000` and open automatically in your browser

The application will be available at:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:5000

## Usage

### Embedding a Watermark

1. Navigate to the **Embed** tab
2. Upload an image (PNG, JPG, BMP)
3. Enter your watermark message
4. Adjust block size if needed (default: 8)
5. Verify message fits within capacity
6. Click **Embed & Sign Watermark**
7. Download the watermarked image

### Verifying a Watermark

1. Navigate to the **Verify** tab
2. Upload a watermarked image
3. Set the block size used during embedding
4. Click **Extract & Verify Watermark**
5. View extracted message and signature status
   - ✅ **Valid**: Signature verified, image authentic
   - ❌ **Invalid**: Signature failed, image may be tampered

## Technical Details

### Watermarking Algorithm

This system uses a **hybrid DWT+DCT approach** for robust, invisible watermarking:

1. **DWT (Discrete Wavelet Transform)**: 
   - 1-level Haar wavelet decomposition on blue channel
   - Embeds in approximation coefficients (cA)
   - Provides frequency domain robustness

2. **Block DCT (Discrete Cosine Transform)**:
   - Divides cA into blocks (8×8 default)
   - Applies 2D DCT per block
   - Embeds bits in mid-frequency coefficients (position 3,3)
   - Uses magnitude modulation: +150 (bit=1) or -150 (bit=0)

3. **Header Encoding**:
   - First 8 bits encode block size for auto-detection
   - Remaining bits contain: signature length + RSA signature + message

**Advantages**:
- **Imperceptible**: Invisible to human observers (PSNR >40 dB)
- **Robust**: Survives minor modifications and noise
- **High Capacity**: Scales with image size

### Cryptographic Security

Each watermark includes an RSA-2048 digital signature:

```python
# Signing (during embed)
signature = private_key.sign(
    message_bytes,
    padding.PSS(
        mgf=padding.MGF1(hashes.SHA256()),
        salt_length=padding.PSS.MAX_LENGTH
    ),
    hashes.SHA256()
)

# Verification (during extract)
public_key.verify(signature, message_bytes, ...)
```

**Security Properties**:
- ✅ Authenticity: Proves message origin
- ✅ Integrity: Detects any tampering
- ✅ Non-repudiation: Cannot deny signing
- ❌ Robust to JPEG compression (lossy encoding may corrupt bits)

### Embedding Capacity

Approximate capacity based on image dimensions:

| Image Size | Block Size | Available Bits | Max Characters* |
|------------|------------|----------------|-----------------|
| 512×512    | 8          | ~4,096         | ~230            |
| 1920×1080  | 8          | ~16,200        | ~1,750          |
| 4000×3000  | 8          | ~93,750        | ~11,400         |

*Accounts for RSA signature overhead (256 bytes for RSA-2048)

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check |
| POST | `/api/capacity` | Calculate embedding capacity |
| POST | `/api/embed` | Embed watermark with signature |
| POST | `/api/verify` | Extract and verify watermark |
| POST | `/api/batch-embed` | Process multiple images |
| POST | `/api/detect` | Auto-detect block size |

### Example API Usage

```bash
# Check API health
curl http://localhost:5000/api/health

# Calculate capacity
curl -X POST -F "image=@photo.jpg" -F "block_size=8" \
  http://localhost:5000/api/capacity

# Embed watermark
curl -X POST -F "image=@photo.jpg" -F "message=Copyright 2025" \
  -F "block_size=8" http://localhost:5000/api/embed \
  --output watermarked.png

# Verify watermark
curl -X POST -F "image=@watermarked.png" -F "block_size=8" \
  http://localhost:5000/api/verify
```

## Project Structure

```
digital_watermarking_project/
├── backend/
│   ├── api.py                    # Flask REST API
│   ├── config.py                 # Configuration
│   ├── requirements.txt          # Python dependencies
│   ├── crypto/                   # RSA cryptography
│   │   ├── keys.py              # Key generation
│   │   ├── sign.py              # Message signing
│   │   └── verify.py            # Signature verification
│   ├── watermarking/             # DWT+DCT watermarking
│   │   ├── embed.py             # Embedding algorithm
│   │   └── extract.py           # Extraction algorithm
│   ├── utils/                    # Helper utilities
│   │   ├── conversions.py       # Bit/byte conversion
│   │   ├── hashing.py           # SHA-256 hashing
│   │   └── image_utils.py       # Image I/O
│   └── data/
│       ├── keys/                # RSA keypair (PEM)
│       │   ├── private.pem      # Private key
│       │   └── public.pem       # Public key
│       └── watermarked/         # Output directory
├── frontend/
│   ├── package.json             # Node dependencies
│   ├── tsconfig.json            # TypeScript configuration
│   ├── src/
│   │   ├── App.tsx              # Main application
│   │   ├── index.tsx            # Entry point
│   │   └── components/
│   │       ├── EmbedTab.tsx     # Embedding interface
│   │       ├── EmbedTab.css     # Embed styles
│   │       ├── VerifyTab.tsx    # Verification interface
│   │       └── VerifyTab.css    # Verify styles
│   └── public/
│       └── index.html           # HTML template
├── .gitignore                   # Git ignore rules
├── LICENSE                      # MIT License
└── README.md                    # This file
```

## Troubleshooting

### Backend won't start
- Ensure Python 3.8+ is installed
- Install dependencies: `pip install -r backend/requirements.txt`
- Check port 5000 is not in use

### Frontend can't connect to backend
- Verify backend is running on `http://localhost:5000`
- Check CORS is enabled in `api.py`
- Clear browser cache

### Signature verification fails
- Ensure same block size used for embed and verify
- Avoid JPEG compression (use PNG for lossless storage)
- Check RSA keys are present in `backend/data/keys/`

### Image capacity too small
- Use larger images or decrease block size
- Message includes 256-byte RSA signature overhead

## Performance

| Operation | Time (1920×1080) | Notes |
|-----------|------------------|-------|
| Capacity Check | ~0.1s | Fast calculation |
| Embed | ~1.5s | Includes DWT+DCT+IDWT |
| Verify | ~0.8s | Extraction + verification |

## License

MIT License - See LICENSE file for details

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## Citation

If you use this project in academic work, please cite:

```
Digital Watermarking System for Image Authentication
Using Hybrid DWT+DCT and RSA Signatures
2025
```

## Acknowledgments

Built for protecting historical photographs and digital image collections.

---

**Developed for secure image authentication and copyright protection**
