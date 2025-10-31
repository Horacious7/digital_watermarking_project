"""
Flask API for Digital Watermarking
"""
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import tempfile
from pathlib import Path
import cv2
import pywt
import numpy as np
import time
import uuid

from crypto.sign import sign_hash
from crypto.verify import verify_signature
from utils.conversions import bytes_to_bits, bits_to_bytes
from watermarking.embed import embed_watermark
from watermarking.extract import extract_watermark

app = Flask(__name__)
CORS(app)  # Enable CORS for React frontend

# Configuration
UPLOAD_FOLDER = tempfile.gettempdir()
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'bmp'}
PRIVATE_KEY = "data/keys/private.pem"
PUBLIC_KEY = "data/keys/public.pem"

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'ok', 'message': 'Digital Watermarking API is running'})

@app.route('/api/capacity', methods=['POST'])
def calculate_capacity():
    """Calculate embedding capacity for an image"""
    if 'image' not in request.files:
        return jsonify({'error': 'No image file provided'}), 400

    file = request.files['image']
    if file.filename == '' or not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file'}), 400

    block_size = int(request.form.get('block_size', 8))

    try:
        # Save temp file with unique name to avoid race conditions
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(filepath)

        # Calculate capacity
        img = cv2.imread(filepath, cv2.IMREAD_COLOR)
        if img is None:
            os.remove(filepath)
            return jsonify({'error': 'Could not read image. Make sure it is a valid image file.'}), 400

        if img.shape[0] < block_size * 2 or img.shape[1] < block_size * 2:
            os.remove(filepath)
            return jsonify({'error': f'Image too small for block size {block_size}'}), 400

        blue = img[:, :, 0].astype(np.float32)
        coeffs2 = pywt.dwt2(blue, 'haar')
        cA, _ = coeffs2
        cA_h, cA_w = cA.shape
        num_blocks = (cA_h // block_size) * (cA_w // block_size)

        # Clean up
        os.remove(filepath)

        return jsonify({
            'capacity_bits': num_blocks,
            'capacity_bytes': num_blocks // 8,
            'image_size': {'width': img.shape[1], 'height': img.shape[0]},
            'block_size': block_size
        })
    except Exception as e:
        # Clean up file if it exists
        if 'filepath' in locals() and os.path.exists(filepath):
            os.remove(filepath)
        return jsonify({'error': f'Error processing image: {str(e)}'}), 500

@app.route('/api/embed', methods=['POST'])
def embed():
    """Embed watermark into image"""
    if 'image' not in request.files:
        return jsonify({'error': 'No image file provided'}), 400

    file = request.files['image']
    if file.filename == '' or not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file'}), 400

    message = request.form.get('message', '')
    block_size = int(request.form.get('block_size', 8))

    if not message:
        return jsonify({'error': 'No message provided'}), 400

    try:
        # Save input file with unique name
        filename = secure_filename(file.filename)
        unique_id = uuid.uuid4()
        input_path = os.path.join(app.config['UPLOAD_FOLDER'], f'input_{unique_id}_{filename}')
        file.save(input_path)

        # Prepare payload with null terminator
        message_bytes = message.encode('utf-8')
        # Add 4 null bytes as terminator to mark end of message
        message_bytes_with_terminator = message_bytes + b'\x00\x00\x00\x00'

        signature = sign_hash(PRIVATE_KEY, message_bytes)  # Sign ONLY the message, not the terminator
        sig_len_bytes = len(signature).to_bytes(4, 'big')
        payload = sig_len_bytes + signature + message_bytes_with_terminator
        payload_bits = bytes_to_bits(payload)

        # Check capacity
        img = cv2.imread(input_path, cv2.IMREAD_COLOR)
        blue = img[:, :, 0].astype(np.float32)
        coeffs2 = pywt.dwt2(blue, 'haar')
        cA, _ = coeffs2
        cA_h, cA_w = cA.shape
        num_blocks = (cA_h // block_size) * (cA_w // block_size)

        if len(payload_bits) > num_blocks:
            os.remove(input_path)
            return jsonify({
                'error': 'Message too long for image capacity',
                'required_bits': len(payload_bits),
                'available_bits': num_blocks
            }), 400

        # Embed watermark
        output_path = os.path.join(app.config['UPLOAD_FOLDER'], f'watermarked_{unique_id}_{filename}')
        embed_watermark(input_path, payload_bits, output_path, block_size=block_size)

        # Clean up input
        os.remove(input_path)

        # Return watermarked image
        return send_file(output_path, mimetype='image/png', as_attachment=True,
                        download_name=f'watermarked_{filename}')
    except Exception as e:
        # Clean up any temporary files
        if 'input_path' in locals() and os.path.exists(input_path):
            os.remove(input_path)
        if 'output_path' in locals() and os.path.exists(output_path):
            os.remove(output_path)
        return jsonify({'error': f'Error embedding watermark: {str(e)}'}), 500

@app.route('/api/verify', methods=['POST'])
def verify():
    """Extract and verify watermark from image"""
    if 'image' not in request.files:
        return jsonify({'error': 'No image file provided'}), 400

    file = request.files['image']
    if file.filename == '' or not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file'}), 400

    block_size = int(request.form.get('block_size', 8))

    try:
        # Save file with unique name
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(filepath)

        # Calculate capacity to know how many bits to extract
        img = cv2.imread(filepath, cv2.IMREAD_COLOR)
        blue = img[:, :, 0].astype(np.float32)
        coeffs2 = pywt.dwt2(blue, 'haar')
        cA, _ = coeffs2
        cA_h, cA_w = cA.shape
        num_blocks = (cA_h // block_size) * (cA_w // block_size)

        # Extract watermark (try to extract maximum capacity)
        extracted_bits = extract_watermark(filepath, num_blocks, block_size=block_size)
        extracted_bytes = bits_to_bytes(extracted_bits)

        # Parse payload
        if len(extracted_bytes) < 4:
            os.remove(filepath)
            return jsonify({
                'error': 'No valid watermark found',
                'message': '',
                'valid': False
            })

        sig_len = int.from_bytes(extracted_bytes[0:4], 'big')

        if sig_len > len(extracted_bytes) - 4 or sig_len <= 0:
            os.remove(filepath)
            return jsonify({
                'error': 'Invalid watermark format',
                'message': '',
                'valid': False
            })

        signature = extracted_bytes[4:4+sig_len]
        message_bytes = extracted_bytes[4+sig_len:]

        # Find the null terminator (4 consecutive null bytes)
        terminator = b'\x00\x00\x00\x00'
        terminator_idx = message_bytes.find(terminator)

        if terminator_idx != -1:
            # Found terminator, extract message up to that point
            message_bytes_clean = message_bytes[:terminator_idx]
        else:
            # No terminator found, use the progressive UTF-8 decoding method
            message_bytes_clean = b''
            message = ''

            for i in range(1, len(message_bytes) + 1):
                try:
                    test_decode = message_bytes[:i].decode('utf-8', errors='strict')
                    message_bytes_clean = message_bytes[:i]
                    message = test_decode
                except UnicodeDecodeError:
                    break

                if message_bytes[i-1:i] == b'\x00':
                    break

        # Decode the clean message
        try:
            message = message_bytes_clean.decode('utf-8', errors='strict')
        except UnicodeDecodeError:
            message = message_bytes_clean.decode('utf-8', errors='ignore')


        # Verify signature using the clean message bytes
        is_valid = verify_signature(PUBLIC_KEY, message_bytes_clean, signature)

        # Clean up
        os.remove(filepath)

        return jsonify({
            'message': message,
            'valid': is_valid,
            'signature_length': sig_len
        })
    except Exception as e:
        # Clean up file if it exists
        if 'filepath' in locals() and os.path.exists(filepath):
            os.remove(filepath)
        return jsonify({'error': f'Error verifying watermark: {str(e)}'}), 500

if __name__ == '__main__':
    # Ensure keys exist
    if not os.path.exists(PRIVATE_KEY) or not os.path.exists(PUBLIC_KEY):
        print("Warning: Cryptographic keys not found. Please generate them first.")

    app.run(debug=True, host='0.0.0.0', port=5000)