# embed.py
import numpy as np
import pywt
from utils.image_utils import load_image, save_image

def embed_watermark(image_path: str, watermark_bits: str, output_path: str):
    """
    Embed binary watermark into the blue channel of a color image using 1-level DWT (robust quantization).
    """
    img = load_image(image_path)  # shape: (h, w, 3) for color
    if img.ndim == 3:
        blue = img[:, :, 0].copy()  # select blue channel
    else:
        blue = img.copy()  # fallback for grayscale
    coeffs2 = pywt.dwt2(blue, 'haar')
    cA, (cH, cV, cD) = coeffs2
    flat = cA.flatten()
    n_bits = min(len(flat), len(watermark_bits))
    for i in range(n_bits):
        bit = int(watermark_bits[i])
        flat[i] = 100 if bit == 1 else -100  # strong quantization
    cA = flat.reshape(cA.shape)
    coeffs2 = (cA, (cH, cV, cD))
    watermarked_blue = pywt.idwt2(coeffs2, 'haar')
    # Ensure shape matches original blue channel
    watermarked_blue = watermarked_blue[:blue.shape[0], :blue.shape[1]]
    if img.ndim == 3:
        img[:, :, 0] = watermarked_blue
        save_image(img, output_path)
    else:
        save_image(watermarked_blue, output_path)
    print(f"✅ Watermark embedded (DWT, blue channel): {output_path}")
