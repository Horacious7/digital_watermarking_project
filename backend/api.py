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

    # Optional: allow manual override, but auto-detect by default
    block_size_param = request.form.get('block_size', None)

    try:
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

        # Verify signature using the clean message bytes
        is_valid = verify_signature(PUBLIC_KEY, message_bytes_clean, signature)

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
        # Prepare payload once (same for all images)
        message_bytes = message.encode('utf-8')
        message_bytes_with_terminator = message_bytes + b'\x00\x00\x00\x00'
        signature = sign_hash(PRIVATE_KEY, message_bytes)

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

                if len(payload_bits) > num_blocks:
                    results.append({
                        'filename': filename,
                        'success': False,
                        'error': f'Message too long (need {len(payload_bits)} bits, have {num_blocks})'
                    })
                    print(f"  ❌ {idx+1}/{len(files)}: {filename} - Message too long")
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

                # Verify signature
                is_valid = verify_signature(PUBLIC_KEY, message_bytes_clean, signature)

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


if __name__ == '__main__':
    # Ensure keys exist
    if not os.path.exists(PRIVATE_KEY) or not os.path.exists(PUBLIC_KEY):
        print("Warning: Cryptographic keys not found. Please generate them first.")

    app.run(debug=True, host='0.0.0.0', port=5000)