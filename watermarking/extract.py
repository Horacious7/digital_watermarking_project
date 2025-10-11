# extract.py
import numpy as np
import pywt
from utils.image_utils import load_image

def extract_watermark(image_path: str, n_bits: int) -> str:
    """
    Extract binary watermark from the blue channel of a color image using 1-level DWT (robust quantization).
    """
    img = load_image(image_path)  # shape: (h, w, 3) for color
    if img.ndim == 3:
        blue = img[:, :, 0].copy()  # select blue channel
    else:
        blue = img.copy()  # fallback for grayscale
    coeffs2 = pywt.dwt2(blue, 'haar')
    cA, (cH, cV, cD) = coeffs2
    flat = cA.flatten()
    bits = []
    for i in range(n_bits):
        bits.append('1' if flat[i] > 0 else '0')
    return ''.join(bits)