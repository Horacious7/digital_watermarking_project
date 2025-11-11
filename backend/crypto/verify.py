# verify.py
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes

def verify_signature(public_key_path, image_hash, signature):
    """
    Verify the signature of the image hash.
    :return: True if valid, False otherwise
    """
    from cryptography.hazmat.primitives import serialization

    #loading public key
    with open(public_key_path, 'rb') as f:
        public_key = serialization.load_pem_public_key(f.read())

    try:
        #verifying the signature
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
