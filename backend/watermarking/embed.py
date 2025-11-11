# embed.py
import numpy as np
import pywt
import cv2
from backend.utils.image_utils import load_image, save_image


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


def _idct2(block):
    return cv2.idct(block)


def embed_watermark(image_path: str, watermark_bits: str, output_path: str, block_size: int = 8, mag: float = 150.0):
    """
    Hybrid DWT + block-DCT watermark embedding.
    - Load image (color or grayscale).
    - Use blue channel (channel 0) for embedding when color.
    - 1-level DWT (haar) -> get cA (approximation).
    - Pad cA to multiples of block_size, split into blocks, apply 2D DCT.
    - Embed one bit per block by setting a mid-frequency coefficient to +mag (bit=1) or -mag (bit=0).
    - First 8 bits encode block_size for auto-detection during extraction.
    - Inverse DCT per block, unpad, inverse DWT to reconstruct blue channel, save image.
    """
    img = load_image(image_path)  # float32
    color = img.ndim == 3
    if color:
        blue = img[:, :, 0].astype(np.float32).copy()
    else:
        blue = img.astype(np.float32).copy()

    # 1-level DWT
    coeffs2 = pywt.dwt2(blue, 'haar')
    cA, (cH, cV, cD) = coeffs2

    # Work on cA with block DCT
    cA_f = cA.astype(np.float32)
    padded, pad = _pad_to_block(cA_f, block_size)
    H, W = padded.shape
    nb_h = H // block_size
    nb_w = W // block_size
    available_blocks = nb_h * nb_w

    # Encode block_size as 8-bit header (valid values: 2, 4, 8, 16, 32, 64)
    block_size_header = format(block_size, '08b')
    watermark_with_header = block_size_header + watermark_bits

    n_bits = min(available_blocks, len(watermark_with_header))

    print(f"Available blocks: {available_blocks}, Watermark bits: {len(watermark_with_header)} (8-bit header + {len(watermark_bits)} data)")

    # Process blocks and embed
    embedded = padded.copy()
    bit_idx = 0
    # Choose a mid-frequency coefficient position (u,v) inside block
    u, v = 3, 3  # zero-based index; adjust if block_size < 4
    u = min(u, block_size-1)
    v = min(v, block_size-1)

    for by in range(nb_h):
        for bx in range(nb_w):
            if bit_idx >= n_bits:
                break
            y0 = by * block_size
            x0 = bx * block_size
            block = padded[y0:y0+block_size, x0:x0+block_size].copy()
            # ensure block is float32
            block_f = block.astype(np.float32)
            d = _dct2(block_f)
            bit = int(watermark_with_header[bit_idx])
            # Force chosen coefficient to +mag or -mag to encode bit
            d[u, v] = mag if bit == 1 else -mag
            # Reconstruct block
            idb = _idct2(d)
            embedded[y0:y0+block_size, x0:x0+block_size] = idb
            bit_idx += 1
        if bit_idx >= n_bits:
            break

    # Unpad and inverse DWT
    cA_emb = _unpad(embedded, pad)
    coeffs2_emb = (cA_emb, (cH, cV, cD))
    watermarked_blue = pywt.idwt2(coeffs2_emb, 'haar')
    # Match original shape (dwt/idwt may change shape slightly)
    watermarked_blue = watermarked_blue[:blue.shape[0], :blue.shape[1]]

    # Assign back and save
    if color:
        out = img.copy()
        out[:, :, 0] = watermarked_blue
        save_image(out, output_path)
    else:
        save_image(watermarked_blue, output_path)

    print(f"✅ Watermark embedded (hybrid DWT+DCT, blue channel): {output_path}")
