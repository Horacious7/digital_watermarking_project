# extract.py
import numpy as np
from scipy.fftpack import dct
from utils.image_utils import load_image

def extract_watermark(image_path: str, n_bits: int) -> str:
    """
    Extract binary watermark from image using block-based DCT (8x8 blocks).
    """
    img = load_image(image_path)
    h, w = img.shape
    block_size = 8
    wm_idx = 0
    bits = []
    for i in range(0, h, block_size):
        for j in range(0, w, block_size):
            block = img[i:i+block_size, j:j+block_size]
            if block.shape != (block_size, block_size):
                continue
            dct_block = dct(dct(block.T, norm='ortho').T, norm='ortho')
            if wm_idx < n_bits:
                coeff = dct_block[4, 4]
                bits.append('1' if coeff > 0 else '0')
                wm_idx += 1
    return ''.join(bits)
