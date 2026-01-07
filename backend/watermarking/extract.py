# extract.py
import numpy as np
import pywt
import cv2
from backend.utils.image_utils import load_image


def _pad_to_block(img, block_size):
    h, w = img.shape
    pad_h = (block_size - (h % block_size)) % block_size
    pad_w = (block_size - (w % block_size)) % block_size
    if pad_h == 0 and pad_w == 0:
        return img, (0, 0)
    padded = np.pad(img, ((0, pad_h), (0, pad_w)), mode='symmetric')
    return padded, (pad_h, pad_w)


def _unpad(img, pad):
    pad_h, pad_w = pad
    if pad_h == 0 and pad_w == 0:
        return img
    if pad_h > 0:
        img = img[:-pad_h, :]
    if pad_w > 0:
        img = img[:, :-pad_w]
    return img


def _dct2(block):
    return cv2.dct(block)


def detect_block_size(image_path: str) -> int:
    """
    Auto-detect block_size from the 8-bit header embedded in the watermark.
    The trick: when we extract with the CORRECT block_size, the header will decode to that same block_size.
    Example: If embedded with block_size=13, the header is '00001101' (13 in binary).
             When we extract with block_size=13, we'll read '00001101' → 13. Match!
    Returns the detected block_size or 8 (default) if detection fails.
    """
    print("🔍 Starting block_size auto-detection (trying all values 2-64)...")

    # Try each possible block size from 2 to 64
    for try_block_size in range(2, 65):
        try:
            header_bits = extract_watermark(image_path, n_bits=8, block_size=try_block_size)
            detected_value = int(header_bits, 2)

            # The correct block_size will decode its own value from the header!
            if detected_value == try_block_size:
                print(f"✅ Auto-detected block_size: {detected_value} (header matched: '{header_bits}')")
                return detected_value

            # Optional: show first few and last few attempts for debugging
            if try_block_size <= 4 or try_block_size >= 62:
                print(f"  Trying block_size={try_block_size}: header_bits='{header_bits}' → value={detected_value} (no match)")

        except Exception as e:
            if try_block_size <= 4 or try_block_size >= 62:
                print(f"  Trying block_size={try_block_size}: ERROR - {e}")
            continue

    # Fallback to default
    print("⚠️ Could not auto-detect block_size, using default: 8")
    return 8


def extract_watermark(image_path: str, n_bits: int, block_size: int = 8) -> str:
    """
    Hybrid DWT + block-DCT watermark extraction.
    - Load image (color or grayscale).
    - Use blue channel when color.
    - 1-level DWT -> cA, pad to block size, per-block DCT, read chosen coefficient sign to recover bits.
    """
    img = load_image(image_path)
    color = img.ndim == 3
    if color:
        blue = img[:, :, 0].astype(np.float32).copy()
    else:
        blue = img.astype(np.float32).copy()

    coeffs2 = pywt.dwt2(blue, 'haar')
    cA, (cH, cV, cD) = coeffs2

    cA_f = cA.astype(np.float32)
    padded, pad = _pad_to_block(cA_f, block_size)
    H, W = padded.shape
    nb_h = H // block_size
    nb_w = W // block_size
    available_blocks = nb_h * nb_w
    n_bits = min(available_blocks, n_bits)

    bits = []
    # Choose same mid-frequency coefficient position as embed
    # Position depends on block size for optimal robustness
    if block_size <= 4:
        u, v = 1, 2  # For small blocks, use lower frequency
    elif block_size >= 10:
        u, v = 4, 4  # For large blocks, use slightly higher frequency
    else:
        u, v = 3, 3  # Standard mid-frequency for 6x6, 7x7, 8x8, 9x9

    # Ensure coefficients are within block bounds
    u = min(u, block_size-1)
    v = min(v, block_size-1)

    bit_idx = 0
    for by in range(nb_h):
        for bx in range(nb_w):
            if bit_idx >= n_bits:
                break
            y0 = by * block_size
            x0 = bx * block_size
            block = padded[y0:y0+block_size, x0:x0+block_size].astype(np.float32)
            d = _dct2(block)
            coeff = d[u, v]
            bits.append('1' if coeff > 0 else '0')
            bit_idx += 1
        if bit_idx >= n_bits:
            break

    return ''.join(bits)