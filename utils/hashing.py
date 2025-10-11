# hashing.py
import hashlib

def hash_image(image_path):
    """
    Compute SHA-256 hash of an image file.
    :param image_path: path to image
    :return: hash bytes
    """
    hasher = hashlib.sha256()
    with open(image_path, 'rb') as f:
        while chunk := f.read(8192):
            hasher.update(chunk)
    return hasher.digest()  #returneaza bytes