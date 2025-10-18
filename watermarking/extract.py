# extract.py
import numpy as np
import pywt
import cv2
from utils.image_utils import load_image


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
    u, v = 3, 3
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