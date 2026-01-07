# verify.py
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization

def verify_signature(public_key_path, image_hash, signature):
    """
    Verify the signature of the image hash using public key from file.
    :return: True if valid, False otherwise
    """
    # Loading public key
    with open(public_key_path, 'rb') as f:
        public_key = serialization.load_pem_public_key(f.read())

    try:
        # Verifying the signature
        public_key.verify(
            signature,
            image_hash,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return True
    except Exception as e:
        print(f"Verification failed: {type(e).__name__}")
        return False


def verify_signature_with_key_content(public_key_pem: bytes, image_hash: bytes, signature: bytes) -> bool:
    """
    Verify the signature of the image hash using public key from PEM content.
    :param public_key_pem: Public key in PEM format (as bytes)
    :param image_hash: Hash of the image
    :param signature: Signature to verify
    :return: True if valid, False otherwise
    """
    # Loading public key from content
    public_key = serialization.load_pem_public_key(public_key_pem)

    try:
        # Verifying the signature
        public_key.verify(
            signature,
            image_hash,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return True
    except Exception as e:
        print(f"Verification failed: {type(e).__name__}")
        return False
