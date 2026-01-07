# sign.py
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import serialization

def sign_hash(private_key_path: str, image_hash: bytes) -> bytes:
    """
    Sign the image hash using RSA private key from file.
    """
    # Load private key
    with open(private_key_path, 'rb') as f:
        private_key = serialization.load_pem_private_key(
            f.read(),
            password=None,
        )

    # Signing the hash
    signature = private_key.sign(
        image_hash,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )
    return signature  # Returns bytes


def sign_hash_with_key_content(private_key_pem: bytes, image_hash: bytes) -> bytes:
    """
    Sign the image hash using RSA private key from PEM content.
    :param private_key_pem: Private key in PEM format (as bytes)
    :param image_hash: Hash of the image to sign
    :return: Signature bytes
    """
    # Load private key from content
    private_key = serialization.load_pem_private_key(
        private_key_pem,
        password=None,
    )

    # Signing the hash
    signature = private_key.sign(
        image_hash,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )
    return signature  # Returns bytes
