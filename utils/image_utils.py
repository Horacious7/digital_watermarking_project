# image_utils.py
import cv2
import numpy as np

def load_image(path: str, grayscale: bool = True) -> np.ndarray:
    """
    Load image as NumPy array. Default = grayscale.
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
