# sign.py
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding

def sign_hash(private_key_path, image_hash):
    """
    Sign the image hash using RSA private key.
    :param private_key_path: path to private key file
    :param image_hash: bytes of image hash
    :return: signature bytes
    """
    # TODO: implement signing
    pass
