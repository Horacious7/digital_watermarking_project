# TRACE - Digital Image Watermarking Platform
A production-ready full-stack web application for embedding and verifying cryptographically signed invisible watermarks in digital images. This system implements a hybrid DWT+DCT watermarking technique with RSA-2048 digital signatures, providing both content authentication and tamper detection for digital imagery.
**Author:** Maier Horatiu-Gabriel  
**Project Type:** Bachelor's Thesis - Computer Science  
**Year:** 2026  
**License:** All rights reserved - Proprietary intellectual property
---
## Table of Contents
1. [Overview](#overview)
2. [Core Features](#core-features)
3. [Technical Architecture](#technical-architecture)
4. [Installation and Setup](#installation-and-setup)
5. [User Guide](#user-guide)
6. [Algorithm Details](#algorithm-details)
7. [Testing and Validation](#testing-and-validation)
8. [API Reference](#api-reference)
9. [Performance Characteristics](#performance-characteristics)
10. [Security Analysis](#security-analysis)
11. [Known Limitations](#known-limitations)
12. [Future Work](#future-work)
---
## Overview
TRACE (Trusted Resource Authentication and Content Encryption) is a comprehensive platform designed for museums, archives, photographers, and content creators who need to protect digital image collections through invisible watermarking and cryptographic verification.
### Problem Statement
Digital images are easily copied, modified, and redistributed without attribution. Traditional visible watermarks degrade image quality, while metadata can be trivially stripped. This project addresses the need for:
- Invisible, robust watermark embedding
- Cryptographic proof of authenticity
- Tamper detection capabilities
- Batch processing for large collections
- User-friendly interface for non-technical users
### Solution Approach
The system combines:
1. **Hybrid DWT+DCT Watermarking**: Embeds data in frequency domain for robustness
2. **RSA-2048 Digital Signatures**: Provides cryptographic authentication
3. **Adaptive Safety Margins**: Ensures reliability across different image types
4. **Auto-Verification System**: Validates signature integrity after embedding
5. **Smart Batch Processing**: Handles multiple images with intelligent error handling
---
## Core Features
### Watermark Embedding
- **Invisible Embedding**: Messages are imperceptible in the watermarked image
- **Single and Batch Processing**: Process one image or hundreds simultaneously
- **Block Size Selection**: Multiple DCT block sizes (4x4, 6x6, 8x8, 9x9, 13x13) with visual reliability indicators
- **Capacity Calculation**: Real-time feedback on available embedding space
- **Automatic Verification**: Each embedded image is cryptographically verified before download
### Watermark Verification
- **Auto-Detection**: Automatically identifies the block size used during embedding
- **Signature Validation**: Verifies RSA-2048 digital signatures
- **Batch Verification**: Process multiple watermarked images with statistical reporting
- **Detailed Reporting**: Provides comprehensive information about extracted watermarks
### Cryptographic Key Management
- **RSA Key Generation**: Client-side generation of 2048-bit RSA key pairs
- **Session Storage**: Keys stored securely in browser session (cleared on tab close)
- **Key Upload/Download**: Import/export keys in PEM format
- **Fingerprint Display**: SHA-256 fingerprints for key verification
### User Interface
- **Modern Design**: Clean, professional interface with dark/light mode support
- **Drag & Drop**: Intuitive file upload with visual feedback
- **Image Carousel**: Navigate through multiple images with thumbnail preview
- **Toast Notifications**: Real-time feedback for all operations
- **Visual Indicators**: Color-coded reliability indicators for block sizes
- **Responsive Design**: Optimized for desktop, tablet, and mobile devices

---

## Technical Architecture

### Backend Stack

**Language:** Python 3.12
**Framework:** Flask 2.3.0 with CORS support

**Core Dependencies:**
- `PyWavelets (pywt) 1.4.1`: Discrete Wavelet Transform implementation
- `OpenCV (cv2) 4.8.1`: Image processing and Discrete Cosine Transform
- `cryptography 41.0.7`: RSA key operations and digital signatures
- `NumPy 1.24.3`: Numerical computations and array operations

**Architecture Pattern:** RESTful API with modular separation of concerns

```
backend/
├── api.py                      # Flask application and REST endpoints
├── config.py                   # Configuration management
├── crypto/
│   ├── keys.py                # RSA-2048 key generation
│   ├── sign.py                # Message signing with private key
│   └── verify.py              # Signature verification with public key
├── utils/
│   ├── conversions.py         # Binary/bytes/hex conversions
│   ├── hashing.py             # SHA-256 hashing utilities
│   └── image_utils.py         # Image I/O operations
└── watermarking/
    ├── embed.py               # Hybrid DWT+DCT embedding
    └── extract.py             # Watermark extraction and block size detection
```

### Frontend Stack

**Framework:** React 18.2.0 with TypeScript 4.9.5
**Styling:** Custom CSS with CSS variables for theming
**Build Tool:** React Scripts (Create React App)

**Architecture Pattern:** Component-based with hooks and context

```
frontend/src/
├── components/
│   ├── EmbedTab.tsx           # Watermark embedding interface
│   ├── VerifyTab.tsx          # Watermark verification interface
│   ├── KeyManager.tsx         # Cryptographic key management
│   └── Icons.tsx              # SVG icon components
├── hooks/
│   └── useTheme.ts            # Dark/light mode management
└── services/
    └── keyManager.ts          # Session storage key management
```

### Communication Protocol

- **Protocol:** HTTP/HTTPS
- **Data Format:** Multipart form-data for file uploads, JSON for responses
- **CORS:** Enabled for cross-origin requests
- **Error Handling:** Comprehensive error messages with specific codes

---

## Installation and Setup

### Prerequisites

**Required Software:**
- Python 3.12 or higher
- Node.js 18.0 or higher
- npm 9.0 or higher

**Operating System:** Windows 10/11, Linux, or macOS

### Backend Installation

1. **Clone the repository:**
```bash
git clone https://github.com/Horacious7/digital_watermarking_project.git
cd digital_watermarking_project/backend
```

2. **Create and activate virtual environment:**
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux/macOS
python3 -m venv .venv
source .venv/bin/activate
```

3. **Install Python dependencies:**
```bash
pip install -r requirements.txt
```

4. **Verify installation:**
```bash
python -c "import cv2, pywt, cryptography; print('Dependencies OK')"
```

5. **Start the Flask server:**
```bash
python api.py
```

Server will start on `http://localhost:5000`

### Frontend Installation

1. **Navigate to frontend directory:**
```bash
cd ../frontend
```

2. **Install Node.js dependencies:**
```bash
npm install
```

3. **Start development server:**
```bash
npm start
```

Application will open at `http://localhost:3000`

### Production Build

```bash
# Frontend
npm run build

# Deploy the build/ directory to your web server
# Ensure backend API is accessible via CORS
```

---

## User Guide

### Getting Started

1. **Generate Cryptographic Keys:**
   - Open the "Cryptographic Key Management" section
   - Click "Generate New Key Pair"
   - Download and securely store both private.pem and public.pem files
   - Upload the keys to the key manager (they will be stored in session only)

2. **Embed a Watermark:**
   - Navigate to the "Embed" tab
   - Upload one or more images (drag & drop supported)
   - Enter your watermark message
   - Select a block size (8x8 recommended for most images)
   - Review the capacity indicator to ensure message fits
   - Click "Embed & Sign Watermark"
   - Download the watermarked image(s)

3. **Verify a Watermark:**
   - Navigate to the "Verify" tab
   - Upload a watermarked image
   - Upload the public key used for signing
   - Click "Extract & Verify"
   - Review the extracted message and signature status

### Block Size Selection

The system supports multiple DCT block sizes with reliability indicators:

**Highly Reliable (Green):** 4x4, 6x6, 8x8, 9x9, 13x13
- 100% success rate in testing
- Recommended for all production use

**May Be Unreliable (Yellow):** 10x10, 12x12, 15x15
- 80-90% success rate in testing
- Use with caution, verify after embedding

**Unreliable (Red):** 7x7, 11x11, 14x14, 16x16, 17x17, 18x18
- Less than 80% success rate in testing
- Not recommended for production

**Recommendation:** Use 8x8 for maximum compatibility and reliability.

### Batch Processing

When processing multiple images:

1. Select all images at once
2. Configure settings (message, block size)
3. Click "Embed & Sign Watermark"
4. The system will:
   - Process each image individually
   - Verify each watermarked image automatically
   - Download a ZIP file containing only successfully watermarked images
   - Display detailed error messages for any failed images
   - Automatically remove successful images from the list, leaving only failed ones for retry

### Capacity Management

The system automatically calculates available capacity based on:
- Image dimensions
- Selected block size
- Message length
- Digital signature overhead (256 bytes)
- Safety margin (adaptive: 4-12 bytes depending on block size)

Visual feedback indicates:
- Green: Message fits comfortably
- Yellow: Message fits with minimal margin
- Red: Message too long for available capacity

---

## Algorithm Details

### Embedding Algorithm (Hybrid DWT+DCT)

**Step 1: Image Preprocessing**
```
1. Load image and convert to float32
2. Extract blue channel (for color images)
3. Apply 1-level Discrete Wavelet Transform (Haar wavelet)
4. Extract approximation coefficients (cA)
```

**Step 2: Block Partitioning**
```
5. Pad cA to multiples of block_size using symmetric padding
6. Divide padded array into non-overlapping blocks
7. Calculate number of available blocks
```

**Step 3: Payload Preparation**
```
8. Encode block_size as 8-bit header
9. Create payload: [header | signature_length | signature | message | terminator]
10. Convert payload to binary string
```

**Step 4: DCT Embedding**
```
For each block:
    11. Apply 2D Discrete Cosine Transform
    12. Select mid-frequency coefficient (u, v)
    13. Set coefficient to +magnitude (bit=1) or -magnitude (bit=0)
    14. Apply inverse DCT
    15. Replace block in padded array
```

**Step 5: Image Reconstruction**
```
16. Remove padding from modified cA
17. Apply inverse DWT to reconstruct blue channel
18. Combine with original green and red channels
19. Save watermarked image as PNG
```

### Extraction Algorithm

**Step 1: Block Size Detection**
```
For block_size in [2, 3, 4, ..., 64]:
    1. Extract 8 bits from image using current block_size
    2. Decode header value
    3. If header == block_size: MATCH FOUND
```

**Step 2: Watermark Extraction**
```
4. Apply DWT to blue channel
5. Pad approximation coefficients
6. Divide into blocks of detected size
7. For each block:
    8. Apply 2D DCT
    9. Read sign of mid-frequency coefficient
    10. Append bit to extracted bitstring
```

**Step 3: Payload Parsing**
```
11. Skip 8-bit header
12. Convert bits to bytes
13. Parse signature length (4 bytes)
14. Extract signature (signature_length bytes)
15. Extract message (remaining bytes until terminator)
```

**Step 4: Signature Verification**
```
16. Hash message using SHA-256
17. Verify RSA signature using public key
18. Return {message, valid, block_size, signature_length}
```

### Adaptive Safety Margins

Based on extensive reliability testing, the system applies different safety margins:

**Safe Block Sizes (4, 6, 8, 9, 13):** 32 bits (4 bytes)
- Minimal margin for maximum capacity
- Proven 100% reliable across all tested images

**Warning Block Sizes (10, 12, 15):** 64 bits (8 bytes)
- Moderate margin for borderline cases
- 80-90% reliability in testing

**Danger Block Sizes (all others):** 96 bits (12 bytes)
- Large margin for unstable sizes
- Less than 80% reliability

This adaptive approach maximizes usable capacity for reliable block sizes while maintaining safety for less stable configurations.

---

## Testing and Validation

### Test Methodology

Comprehensive reliability testing was conducted to validate the watermarking system across multiple variables:

**Test Matrix:**
- **Images:** 8 native PNG images with varied dimensions (640x1138 to 3000x3000 pixels) and content types (gradient, noise, checkerboard, photographs)
- **Block Sizes:** 18 different configurations (2x2 through 18x18)
- **Messages:** 5 different message lengths (1 byte to 150 bytes)
- **Iterations:** 3 repetitions per configuration for consistency verification

**Total Test Cases:** 8 images x 18 block sizes x 5 messages x 3 iterations = **2,160 individual tests**


### Test Results

**100% Reliable Block Sizes:**
- 4x4: 100% success (8/8 images tested)
- 6x6: 100% success (8/8 images tested)
- 8x8: 100% success (8/8 images tested) - RECOMMENDED
- 9x9: 100% success (7/7 images tested)
- 13x13: 100% success (5/5 images tested)

**Moderately Reliable:**
- 10x10: 83.3% success (5/6 images)
- 12x12: 83.3% success (5/6 images)
- 15x15: 80.0% success (4/5 images)

**Unreliable:**
- 7x7: 37.5% success (3/8 images) - AVOID
- 11x11: 50.0% success (3/6 images)
- 14x14: 60.0% success (3/5 images)
- 16x16: 25.0% success (1/4 images) - HIGHLY UNRELIABLE
- 17x17: 50.0% success (2/4 images)
- 18x18: 50.0% success (2/4 images)

### Key Findings

1. **Block Size Impact:** Certain block sizes (7x7, 16x16) exhibit fundamental incompatibilities with the DWT+DCT pipeline, likely due to dimension alignment issues after wavelet decomposition.

2. **Image Independence:** Reliability is primarily determined by block size, not image content or dimensions (within tested range).

3. **Message Length:** Reliability remains consistent across message lengths, provided capacity constraints are respected.

4. **Signature Overhead:** RSA-2048 signatures add a fixed 265-byte overhead (4 bytes length + 256 bytes signature + 4 bytes terminator + 1 byte safety margin).

### Test Scripts

All test scripts are included in the `backend/` directory for reproducibility and validation.

---

## API Reference

### POST /api/capacity

Calculate embedding capacity for an image.

**Request:**
```
Content-Type: multipart/form-data

Fields:
- image: File (required)
- block_size: Integer (required)
```

**Response:**
```json
{
  "capacity_bits": 5276,
  "capacity_bytes": 659,
  "block_size": 8,
  "image_size": "960x1431",
  "available_for_message_bytes": 394
}
```

---

### POST /api/embed

Embed a cryptographically signed watermark into an image.

**Request:**
```
Content-Type: multipart/form-data

Fields:
- image: File (required)
- message: String (required)
- block_size: Integer (required)
- private_key: String (required)
```

**Response:** Watermarked PNG image file

---

### POST /api/embed/batch

Embed watermarks into multiple images with auto-verification.

**Request:**
```
Content-Type: multipart/form-data

Fields:
- images: File[] (required)
- message: String (required)
- block_size: Integer (required)
- private_key: String (required)
- public_key: String (required)
```

**Response:** ZIP file containing successfully watermarked images, with batch statistics in headers

---

### POST /api/verify

Extract and verify a watermark from an image.

**Request:**
```
Content-Type: multipart/form-data

Fields:
- image: File (required)
- public_key: String (required)
- block_size: Integer (optional)
```

**Response:**
```json
{
  "message": "Copyright 2026",
  "valid": true,
  "block_size": 8,
  "signature_length": 256
}
```

---

### POST /api/verify/batch

Verify multiple watermarked images.

**Request:**
```
Content-Type: multipart/form-data

Fields:
- images: File[] (required)
- public_key: String (required)
```

**Response:**
```json
{
  "results": [...],
  "summary": {
    "total": 10,
    "valid": 8,
    "invalid": 2,
    "success_rate": 80.0
  }
}
```

---

## Performance Characteristics

### Embedding Performance

**Single Image (1920x1080, 8x8 block size):**
- Embedding time: ~0.5-1.0 seconds
- Signature generation: ~0.1 seconds
- Auto-verification: ~0.3 seconds
- Total: ~1.0-1.5 seconds per image

**Batch Processing (10 images, 1920x1080 each):**
- Sequential processing: ~15-20 seconds
- Includes auto-verification for each image

### Extraction Performance

**Single Image Verification:**
- With known block size: ~0.3-0.5 seconds
- With auto-detection: ~2-5 seconds (tests 2-64 block sizes)

**Optimization:** When block size is known, extraction is 10x faster by skipping auto-detection.

### Capacity Characteristics

**Example Capacities (8x8 block size):**

| Image Size | Total Capacity | Message Capacity |
|------------|----------------|------------------|
| 640x480 | 300 bytes | 35 bytes |
| 1920x1080 | 2,025 bytes | 1,760 bytes |
| 3840x2160 | 8,100 bytes | 7,835 bytes |

**Note:** Message capacity = Total capacity - 265 bytes (signature overhead)

---

## Security Analysis

### Cryptographic Strength

**RSA-2048 Digital Signatures:**
- Key size: 2048 bits (considered secure until 2030+ by NIST standards)
- Signature algorithm: PKCS#1 v1.5 (RSA-SHA256)
- Hash function: SHA-256 (256-bit security)

**Attack Resistance:**
- Signature forgery: Computationally infeasible with current technology
- Message tampering: Any modification invalidates the signature
- Replay attacks: Each signature is tied to specific message content

### Watermark Robustness

**Resistant To:**
- Additive noise (Gaussian, salt-and-pepper) up to ~10dB SNR
- JPEG compression at quality 90+ (message extraction possible)
- Minor geometric transformations (rotation <5 degrees)

**Vulnerable To:**
- Aggressive JPEG compression (quality <85): Signature verification fails
- Cropping: Removes watermarked blocks
- Resizing: Changes DWT/DCT domain structure
- Social media platforms (apply additional compression/processing)

### Privacy Considerations

**Data Storage:**
- Private keys: NEVER stored on server (session-only in browser)
- Public keys: Can be stored/distributed safely
- Watermarked images: Contain embedded message (not encrypted by default)

**Recommendations:**
- Encrypt messages before embedding for confidentiality
- Use strong passphrases for private key files
- Implement key rotation policies for long-term archiving

---

## Known Limitations

### Technical Limitations

1. **Image Format Dependency:** Optimal performance with PNG (lossless). JPEG/WebP may corrupt watermark.

2. **Block Size Constraints:** Not all block sizes are reliable (see testing results).

3. **Capacity Limitations:** Small images (<500x500) have very limited capacity.

4. **Robustness Trade-offs:** Invisible watermarks are more fragile than visible ones.

### Operational Limitations

1. **Single Channel Embedding:** Currently uses only blue channel.

2. **No Real-Time Processing:** Batch processing is sequential, not parallel.

3. **Browser Dependency:** Requires modern browser (ES6+), session storage cleared on tab close.

---

## Intellectual Property

This project, including all source code, documentation, algorithms, and user interface designs, is the sole intellectual property of **Maier Horațiu-Gabriel**.

**Copyright 2026 Maier Horațiu-Gabriel. All rights reserved.**

**Academic Use:** This work is submitted as part of a bachelor's thesis in Computer Science. Any reproduction, distribution, or derivative works require explicit written permission from the author.

**GitHub:** https://github.com/Horacious7/digital_watermarking_project

---

## Project Statistics

**Development Period:** September 2025 - January 2026
**Total Lines of Code:** ~9,000+ (Python + TypeScript)
**Test Coverage:** 1000+ validated configurations

**Last Updated:** January 7, 2026
