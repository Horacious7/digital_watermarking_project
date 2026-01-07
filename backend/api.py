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
import zipfile
from io import BytesIO

from crypto.sign import sign_hash
from crypto.verify import verify_signature
from utils.conversions import bytes_to_bits, bits_to_bytes
from watermarking.embed import embed_watermark
from watermarking.extract import extract_watermark, detect_block_size

app = Flask(__name__)
CORS(app)  # Enable CORS for React frontend

# Debug: Store last embedded signature for comparison
_last_signature = None
_last_message = None

# Configuration
UPLOAD_FOLDER = tempfile.gettempdir()
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'bmp'}
PRIVATE_KEY = "data/keys/private.pem"
PUBLIC_KEY = "data/keys/public.pem"

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max for batch processing

# RSA-2048 signature size: 256 bytes
# Payload structure: 4 bytes (sig_len) + 256 bytes (signature) + message + 4 bytes (terminator)
RSA_SIGNATURE_SIZE = 256  # bytes for RSA-2048
SIGNATURE_LENGTH_FIELD = 4  # bytes to store signature length
MESSAGE_TERMINATOR_SIZE = 4  # bytes for null terminator
SIGNATURE_OVERHEAD = SIGNATURE_LENGTH_FIELD + RSA_SIGNATURE_SIZE + MESSAGE_TERMINATOR_SIZE  # 264 bytes total

# Safety margin: Reserve at least 1 byte (8 bits) to avoid edge cases with bit/byte conversion
# This prevents issues when payload uses exactly all available capacity
SAFETY_MARGIN_BYTES = 1  # Extra byte for safe extraction
TOTAL_OVERHEAD = SIGNATURE_OVERHEAD + SAFETY_MARGIN_BYTES  # 265 bytes

def get_safety_margin_bits(block_size):
    """
    Get adaptive safety margin based on block size reliability.

    Based on extensive testing on native PNG images:
    - Safe block sizes (4,6,8,9,13): 100% reliable → minimal margin
    - Warning block sizes (10,12,15): 80-90% reliable → moderate margin
    - Danger block sizes (7,11,14,16,17,18): <80% reliable → large margin

    Returns safety margin in bits.
    """
    # Safe block sizes (100% tested) - minimal margin
    if block_size in [4, 6, 8, 9, 13]:
        return 32  # 4 bytes = header (8) + extraction safety (8) + padding (16)

    # Warning block sizes (80-90% reliable) - moderate margin
    elif block_size in [10, 12, 15]:
        return 64  # 8 bytes = safe + extra buffer for edge cases

    # Danger/unknown block sizes (<80% reliable) - large margin
    else:
        return 96  # 12 bytes = warning + extra protection for unstable sizes

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

        # Adaptive safety margin based on block size reliability
        safety_margin = get_safety_margin_bits(block_size)
        # Embed requires: len(payload_bits) + 8 (header) + safety_margin <= num_blocks
        usable_capacity_bits = max(0, num_blocks - safety_margin)

        # Clean up
        os.remove(filepath)

        return jsonify({
            'capacity_bits': usable_capacity_bits,
            'capacity_bytes': usable_capacity_bits // 8,
            'image_size': {'width': img.shape[1], 'height': img.shape[0]},
            'block_size': block_size,
            'signature_overhead_bytes': TOTAL_OVERHEAD  # Include signature overhead + safety margin
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
        # Check if private key is provided in request
        private_key_content = None
        if 'private_key' in request.files:
            private_key_file = request.files['private_key']
            private_key_content = private_key_file.read()
        elif 'private_key' in request.form:
            private_key_content = request.form.get('private_key').encode('utf-8')

        # Save input file with unique name
        filename = secure_filename(file.filename)
        unique_id = uuid.uuid4()
        input_path = os.path.join(app.config['UPLOAD_FOLDER'], f'input_{unique_id}_{filename}')
        file.save(input_path)

        # Prepare payload with null terminator
        message_bytes = message.encode('utf-8')
        # Add 4 null bytes as terminator to mark end of message
        message_bytes_with_terminator = message_bytes + b'\x00\x00\x00\x00'

        # Require private key to be provided (no fallback to default)
        if not private_key_content:
            os.remove(input_path)
            return jsonify({
                'error': 'Private key is required for signing. Please upload a private key in the Key Management section.'
            }), 400

        from crypto.sign import sign_hash_with_key_content
        signature = sign_hash_with_key_content(private_key_content, message_bytes)

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

        # Check capacity with adaptive safety margin based on block size reliability
        safety_margin = get_safety_margin_bits(block_size)
        required_bits = len(payload_bits) + safety_margin

        if required_bits > num_blocks:
            os.remove(input_path)
            return jsonify({
                'error': 'Message + signature too long for image capacity',
                'details': f'Need {required_bits} bits ({required_bits//8} bytes) including safety margin, but image only has {num_blocks} bits ({num_blocks//8} bytes)',
                'message_size_bytes': len(message_bytes),
                'signature_overhead_bytes': TOTAL_OVERHEAD,
                'total_required_bytes': required_bits // 8,
                'available_bytes': num_blocks // 8,
                'required_bits': required_bits,
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

    # Optional: allow manual override, but auto-detect by default
    block_size_param = request.form.get('block_size', None)

    try:
        # Check if public key is provided in request
        public_key_content = None
        if 'public_key' in request.files:
            public_key_file = request.files['public_key']
            public_key_content = public_key_file.read()
        elif 'public_key' in request.form:
            public_key_content = request.form.get('public_key').encode('utf-8')

        # Save file with unique name
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(filepath)

        # Auto-detect block_size if not provided
        if block_size_param is None or block_size_param == '':
            block_size = detect_block_size(filepath)
            print(f"🔍 Auto-detected block_size: {block_size}")
        else:
            block_size = int(block_size_param)
            print(f"📌 Using manual block_size: {block_size}")

        # Calculate capacity to know how many bits to extract
        img = cv2.imread(filepath, cv2.IMREAD_COLOR)
        blue = img[:, :, 0].astype(np.float32)
        coeffs2 = pywt.dwt2(blue, 'haar')
        cA, _ = coeffs2
        cA_h, cA_w = cA.shape
        num_blocks = (cA_h // block_size) * (cA_w // block_size)

        # Extract watermark (skip first 8 bits as they're the header)
        # But we need to extract all bits first to get the full payload
        extracted_bits = extract_watermark(filepath, num_blocks, block_size=block_size)

        # Skip the first 8 bits (block_size header)
        if len(extracted_bits) > 8:
            extracted_bits = extracted_bits[8:]  # Remove header

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

        # Require public key to be provided (no fallback to default)
        if not public_key_content:
            os.remove(filepath)
            return jsonify({
                'error': 'Public key is required for verification. Please upload a public key in the Key Management section.'
            }), 400

        from crypto.verify import verify_signature_with_key_content
        is_valid = verify_signature_with_key_content(public_key_content, message_bytes_clean, signature)

        # Clean up
        os.remove(filepath)

        return jsonify({
            'message': message,
            'valid': is_valid,
            'signature_length': sig_len,
            'block_size': block_size  # Return detected/used block_size
        })
    except Exception as e:
        # Clean up file if it exists
        if 'filepath' in locals() and os.path.exists(filepath):
            os.remove(filepath)
        return jsonify({'error': f'Error verifying watermark: {str(e)}'}), 500

@app.route('/api/embed/batch', methods=['POST'])
def embed_batch():
    """Embed watermark into multiple images"""
    if 'images' not in request.files:
        return jsonify({'error': 'No image files provided'}), 400

    files = request.files.getlist('images')
    if not files or len(files) == 0:
        return jsonify({'error': 'No files selected'}), 400

    message = request.form.get('message', '')
    block_size = int(request.form.get('block_size', 8))

    print(f"📊 BATCH EMBED REQUEST: {len(files)} images, block_size={block_size}, message='{message[:50]}...'")

    if not message:
        return jsonify({'error': 'No message provided'}), 400

    results = []
    temp_files = []

    try:
        # Check if private key is provided in request
        private_key_content = None
        if 'private_key' in request.files:
            private_key_file = request.files['private_key']
            private_key_content = private_key_file.read()
        elif 'private_key' in request.form:
            private_key_content = request.form.get('private_key').encode('utf-8')

        # Prepare payload once (same for all images)
        message_bytes = message.encode('utf-8')
        message_bytes_with_terminator = message_bytes + b'\x00\x00\x00\x00'

        # Require private key to be provided (no fallback to default)
        if not private_key_content:
            return jsonify({
                'error': 'Private key is required for signing. Please upload a private key in the Key Management section.'
            }), 400

        from crypto.sign import sign_hash_with_key_content
        signature = sign_hash_with_key_content(private_key_content, message_bytes)

        # Store for debugging
        global _last_signature, _last_message
        _last_signature = signature
        _last_message = message_bytes

        sig_len_bytes = len(signature).to_bytes(4, 'big')
        payload = sig_len_bytes + signature + message_bytes_with_terminator
        payload_bits = bytes_to_bits(payload)
        payload_bits = bytes_to_bits(payload)

        for idx, file in enumerate(files):
            if not file or file.filename == '' or not allowed_file(file.filename):
                results.append({
                    'filename': file.filename if file else f'file_{idx}',
                    'success': False,
                    'error': 'Invalid file'
                })
                continue

            try:
                # Save input file
                filename = secure_filename(file.filename)
                unique_id = uuid.uuid4()
                input_path = os.path.join(app.config['UPLOAD_FOLDER'], f'input_{unique_id}_{filename}')

                # IMPORTANT: Seek to beginning before saving (in case stream was read)
                file.seek(0)
                file.save(input_path)
                temp_files.append(input_path)

                print(f"  📥 {idx+1}/{len(files)}: Saved {filename} to temp")

                # Check capacity
                img = cv2.imread(input_path, cv2.IMREAD_COLOR)
                if img is None:
                    results.append({
                        'filename': filename,
                        'success': False,
                        'error': 'Could not read image'
                    })
                    print(f"  ❌ {idx+1}/{len(files)}: Could not read {filename}")
                    continue

                blue = img[:, :, 0].astype(np.float32)
                coeffs2 = pywt.dwt2(blue, 'haar')
                cA, _ = coeffs2
                cA_h, cA_w = cA.shape
                num_blocks = (cA_h // block_size) * (cA_w // block_size)

                # Check capacity with adaptive safety margin based on block size reliability
                safety_margin = get_safety_margin_bits(block_size)
                required_bits = len(payload_bits) + safety_margin

                if required_bits > num_blocks:
                    results.append({
                        'filename': filename,
                        'success': False,
                        'error': f'Message + signature too long (need {required_bits//8} bytes including safety margin, have {num_blocks//8} bytes)'
                    })
                    print(f"  ❌ {idx+1}/{len(files)}: {filename} - Message + signature too long")
                    continue

                # Embed watermark
                output_path = os.path.join(app.config['UPLOAD_FOLDER'], f'watermarked_{unique_id}_{filename}')
                embed_watermark(input_path, payload_bits, output_path, block_size=block_size)
                temp_files.append(output_path)

                results.append({
                    'filename': filename,
                    'success': True,
                    'output_path': output_path,
                    'watermarked_filename': f'watermarked_{filename}'
                })

                print(f"  ✅ {idx+1}/{len(files)}: {filename} embedded successfully")

            except Exception as e:
                results.append({
                    'filename': file.filename if file else f'file_{idx}',
                    'success': False,
                    'error': str(e)
                })
                print(f"  ❌ {idx+1}/{len(files)}: {file.filename if file else 'unknown'} - ERROR: {e}")

        # Create a zip file with all watermarked images
        import zipfile
        from io import BytesIO

        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for result in results:
                if result['success']:
                    zip_file.write(result['output_path'], result['watermarked_filename'])

        zip_buffer.seek(0)

        # Clean up temp files
        for temp_file in temp_files:
            if os.path.exists(temp_file):
                os.remove(temp_file)

        print(f"✅ Batch embed complete: {sum(1 for r in results if r['success'])}/{len(files)} successful")

        return send_file(
            zip_buffer,
            mimetype='application/zip',
            as_attachment=True,
            download_name='watermarked_images.zip'
        )

    except Exception as e:
        # Clean up on error
        for temp_file in temp_files:
            if os.path.exists(temp_file):
                os.remove(temp_file)
        return jsonify({'error': f'Batch processing failed: {str(e)}'}), 500


@app.route('/api/verify/batch', methods=['POST'])
def verify_batch():
    """Verify watermarks from multiple images"""
    if 'images' not in request.files:
        return jsonify({'error': 'No image files provided'}), 400

    files = request.files.getlist('images')
    if not files or len(files) == 0:
        return jsonify({'error': 'No files selected'}), 400

    print(f"🔍 BATCH VERIFY REQUEST: {len(files)} images")

    results = []
    temp_files = []

    try:
        # Check if public key is provided in request
        public_key_content = None
        if 'public_key' in request.files:
            public_key_file = request.files['public_key']
            public_key_content = public_key_file.read()
        elif 'public_key' in request.form:
            public_key_content = request.form.get('public_key').encode('utf-8')

        for idx, file in enumerate(files):
            if not file or file.filename == '' or not allowed_file(file.filename):
                results.append({
                    'filename': file.filename if file else f'file_{idx}',
                    'success': False,
                    'error': 'Invalid file'
                })
                continue

            try:
                # Save file
                filename = secure_filename(file.filename)
                unique_filename = f"{uuid.uuid4()}_{filename}"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)

                # IMPORTANT: Seek to beginning before saving
                file.seek(0)
                file.save(filepath)
                temp_files.append(filepath)

                print(f"  📥 {idx+1}/{len(files)}: Processing {filename}")

                # Auto-detect block_size
                block_size = detect_block_size(filepath)

                # Calculate capacity
                img = cv2.imread(filepath, cv2.IMREAD_COLOR)
                if img is None:
                    results.append({
                        'filename': filename,
                        'success': False,
                        'error': 'Could not read image'
                    })
                    continue

                blue = img[:, :, 0].astype(np.float32)
                coeffs2 = pywt.dwt2(blue, 'haar')
                cA, _ = coeffs2
                cA_h, cA_w = cA.shape
                num_blocks = (cA_h // block_size) * (cA_w // block_size)

                # Extract watermark
                extracted_bits = extract_watermark(filepath, num_blocks, block_size=block_size)

                if len(extracted_bits) > 8:
                    extracted_bits = extracted_bits[8:]  # Remove header

                extracted_bytes = bits_to_bytes(extracted_bits)

                # Parse payload
                if len(extracted_bytes) < 4:
                    results.append({
                        'filename': filename,
                        'success': True,
                        'message': '',
                        'valid': False,
                        'block_size': block_size,
                        'error': 'No valid watermark found'
                    })
                    continue

                sig_len = int.from_bytes(extracted_bytes[0:4], 'big')

                if sig_len > len(extracted_bytes) - 4 or sig_len <= 0:
                    results.append({
                        'filename': filename,
                        'success': True,
                        'message': '',
                        'valid': False,
                        'block_size': block_size,
                        'error': 'Invalid watermark format'
                    })
                    continue

                signature = extracted_bytes[4:4+sig_len]
                message_bytes = extracted_bytes[4+sig_len:]


                # Find terminator
                terminator = b'\x00\x00\x00\x00'
                terminator_idx = message_bytes.find(terminator)

                if terminator_idx != -1:
                    message_bytes_clean = message_bytes[:terminator_idx]
                else:
                    message_bytes_clean = b''
                    for i in range(1, len(message_bytes) + 1):
                        try:
                            test_decode = message_bytes[:i].decode('utf-8', errors='strict')
                            message_bytes_clean = message_bytes[:i]
                        except UnicodeDecodeError:
                            break
                        if message_bytes[i-1:i] == b'\x00':
                            break

                # Decode message
                try:
                    message = message_bytes_clean.decode('utf-8', errors='strict')
                except UnicodeDecodeError:
                    message = message_bytes_clean.decode('utf-8', errors='ignore')

                # Require public key to be provided (no fallback to default)
                if not public_key_content:
                    results.append({
                        'filename': filename,
                        'success': False,
                        'error': 'Public key is required for verification'
                    })
                    continue

                from crypto.verify import verify_signature_with_key_content
                is_valid = verify_signature_with_key_content(public_key_content, message_bytes_clean, signature)

                results.append({
                    'filename': filename,
                    'success': True,
                    'message': message,
                    'valid': is_valid,
                    'block_size': block_size,
                    'signature_length': sig_len
                })

                status = "✅" if is_valid else "⚠️"
                print(f"  {status} {idx+1}/{len(files)}: {filename} - '{message[:30]}...' (valid={is_valid})")

            except Exception as e:
                results.append({
                    'filename': file.filename if file else f'file_{idx}',
                    'success': False,
                    'error': str(e)
                })
                print(f"  ❌ {idx+1}/{len(files)}: {file.filename} - {e}")

        # Clean up temp files
        for temp_file in temp_files:
            if os.path.exists(temp_file):
                os.remove(temp_file)

        valid_count = sum(1 for r in results if r.get('valid', False))
        print(f"✅ Batch verify complete: {valid_count}/{len(files)} valid signatures")

        return jsonify({
            'results': results,
            'summary': {
                'total': len(files),
                'successful': sum(1 for r in results if r['success']),
                'valid_signatures': valid_count
            }
        })

    except Exception as e:
        # Clean up on error
        for temp_file in temp_files:
            if os.path.exists(temp_file):
                os.remove(temp_file)
        return jsonify({'error': f'Batch processing failed: {str(e)}'}), 500


@app.route('/api/keys/generate', methods=['POST'])
def generate_keys():
    """Generate new RSA key pair and return as downloadable ZIP"""
    try:
        from crypto.keys import generate_rsa_keys

        # Create temporary directory for keys
        temp_dir = tempfile.mkdtemp()
        private_key_path = os.path.join(temp_dir, 'private.pem')
        public_key_path = os.path.join(temp_dir, 'public.pem')

        # Generate keys
        generate_rsa_keys(private_key_path, public_key_path, key_size=2048)

        # Create ZIP file in memory
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.write(private_key_path, 'private.pem')
            zip_file.write(public_key_path, 'public.pem')

        # Clean up temp files
        os.remove(private_key_path)
        os.remove(public_key_path)
        os.rmdir(temp_dir)

        # Send ZIP file
        zip_buffer.seek(0)
        return send_file(
            zip_buffer,
            mimetype='application/zip',
            as_attachment=True,
            download_name='trace_rsa_keys.zip'
        )

    except Exception as e:
        return jsonify({'error': f'Key generation failed: {str(e)}'}), 500


@app.route('/api/keys/validate', methods=['POST'])
def validate_keys():
    """Validate uploaded RSA keys"""
    try:
        if 'private_key' not in request.files and 'public_key' not in request.files:
            return jsonify({'error': 'No key files provided'}), 400

        result = {'valid': True, 'errors': []}

        # Validate private key if provided
        if 'private_key' in request.files:
            private_file = request.files['private_key']
            private_content = private_file.read().decode('utf-8')

            if not ('BEGIN RSA PRIVATE KEY' in private_content or 'BEGIN PRIVATE KEY' in private_content):
                result['valid'] = False
                result['errors'].append('Invalid private key format. Expected PEM format.')
            else:
                # Try to load it
                try:
                    from cryptography.hazmat.primitives import serialization
                    serialization.load_pem_private_key(
                        private_content.encode('utf-8'),
                        password=None
                    )
                except Exception as e:
                    result['valid'] = False
                    result['errors'].append(f'Failed to parse private key: {str(e)}')

        # Validate public key if provided
        if 'public_key' in request.files:
            public_file = request.files['public_key']
            public_content = public_file.read().decode('utf-8')

            if not ('BEGIN PUBLIC KEY' in public_content or 'BEGIN RSA PUBLIC KEY' in public_content):
                result['valid'] = False
                result['errors'].append('Invalid public key format. Expected PEM format.')
            else:
                # Try to load it
                try:
                    from cryptography.hazmat.primitives import serialization
                    serialization.load_pem_public_key(public_content.encode('utf-8'))
                except Exception as e:
                    result['valid'] = False
                    result['errors'].append(f'Failed to parse public key: {str(e)}')

        if result['valid']:
            return jsonify({'valid': True, 'message': 'Keys are valid'}), 200
        else:
            return jsonify(result), 400

    except Exception as e:
        return jsonify({'error': f'Key validation failed: {str(e)}'}), 500


if __name__ == '__main__':
    print("Digital Watermarking API Server")
    print("Users must upload their own RSA keys through the frontend Key Management section.")
    app.run(debug=True, host='0.0.0.0', port=5000)