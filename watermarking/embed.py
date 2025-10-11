# embed.py
import numpy as np
from scipy.fftpack import dct, idct
from utils.image_utils import load_image, save_image

def embed_watermark(image_path: str, watermark_bits: str, output_path: str):
    """
    Embed binary watermark into image using block-based DCT (8x8 blocks).
    """
    img = load_image(image_path)
    h, w = img.shape
    block_size = 8
    wm_idx = 0
    watermarked = np.zeros_like(img)
    for i in range(0, h, block_size):
        for j in range(0, w, block_size):
            block = img[i:i+block_size, j:j+block_size]
            if block.shape != (block_size, block_size):
                continue  # skip incomplete blocks
            dct_block = dct(dct(block.T, norm='ortho').T, norm='ortho')
            # Embed watermark bit in (4,4) coefficient (mid-frequency)
            if wm_idx < len(watermark_bits):
                bit = int(watermark_bits[wm_idx])
                # Robust quantization: set to +20 for 1, -20 for 0
                dct_block[4, 4] = 20 if bit == 1 else -20
                wm_idx += 1
            watermarked[i:i+block_size, j:j+block_size] = idct(idct(dct_block.T, norm='ortho').T, norm='ortho')
    save_image(watermarked, output_path)
    print(f"✅ Watermark embedded (block DCT): {output_path}")
