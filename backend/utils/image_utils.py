# image_utils.py
import cv2
import numpy as np

def load_image(path: str, grayscale: bool = False) -> np.ndarray:
    """
    Load image as NumPy array. Default = color.
    """
    flag = cv2.IMREAD_GRAYSCALE if grayscale else cv2.IMREAD_COLOR
    image = cv2.imread(path, flag)
    if image is None:
        raise FileNotFoundError(f"Image not found: {path}")
    return image.astype(np.float32)

def save_image(image: np.ndarray, path: str):
    """
    Save NumPy array as image.
    """
    cv2.imwrite(path, np.clip(image, 0, 255).astype(np.uint8))

def get_resonant_crop(image: np.ndarray, block_size: int) -> np.ndarray:
    """
    Ensure the image is perfectly divisible by block_size * 2, 
    so DWT sub-bands align precisely with block analysis.
    """
    h, w = image.shape[:2]
    # DWT (Haar) reduces size by 2. We want the resulting cA to be divisible by block_size.
    # So original image must be divisible by block_size * 2.
    m = block_size * 2
    
    new_h = h - (h % m)
    new_w = w - (w % m)

    # Perform crop (bottom-right based, equivalent to image[:new_h, :new_w])
    cropped = image[:new_h, :new_w]
    return cropped

def embed_lsb_watermark(image_path: str, watermark_bits: str, output_path: str):
    img = load_image(image_path)
    flat = img.flatten()
    n_bits = min(len(flat), len(watermark_bits))
    for i in range(n_bits):
        flat[i] = flat[i] - (flat[i] % 2) + int(watermark_bits[i])
    img_wm = flat.reshape(img.shape)
    save_image(img_wm, output_path)
    print(f"✅ LSB Watermark embedded: {output_path}")

def extract_lsb_watermark(image_path: str, n_bits: int) -> str:
    img = load_image(image_path)
    flat = img.flatten()
    bits = ''.join(str(int(flat[i]) % 2) for i in range(n_bits))
    return bits