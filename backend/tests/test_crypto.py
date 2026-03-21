import hashlib
from pathlib import Path

import pytest

from crypto.keys import generate_rsa_keys
from crypto.sign import sign_hash_with_key_content
from crypto.verify import verify_signature_with_key_content


@pytest.fixture(scope="module")
def rsa_keypair(tmp_path_factory):
    """Generate a temporary RSA keypair once per test module."""
    temp_dir = tmp_path_factory.mktemp("crypto_keys")
    private_path = temp_dir / "private.pem"
    public_path = temp_dir / "public.pem"

    generate_rsa_keys(str(private_path), str(public_path), key_size=2048)

    private_pem = private_path.read_bytes()
    public_pem = public_path.read_bytes()

    return {
        "private_path": private_path,
        "public_path": public_path,
        "private_pem": private_pem,
        "public_pem": public_pem,
    }


def test_rsa_keypair_generation_creates_valid_pem_files(rsa_keypair):
    """RSA key generation should create non-empty PEM files with expected headers."""
    private_path: Path = rsa_keypair["private_path"]
    public_path: Path = rsa_keypair["public_path"]

    assert private_path.exists()
    assert public_path.exists()
    assert private_path.stat().st_size > 0
    assert public_path.stat().st_size > 0

    private_pem = rsa_keypair["private_pem"]
    public_pem = rsa_keypair["public_pem"]

    assert b"BEGIN" in private_pem and b"PRIVATE KEY" in private_pem
    assert b"BEGIN" in public_pem and b"PUBLIC KEY" in public_pem


def test_sha256_hash_from_test_string():
    """SHA-256 from a known input string should match hashlib output."""
    data = b"TRACE test string"
    digest = hashlib.sha256(data).digest()

    assert isinstance(digest, bytes)
    assert len(digest) == 32
    assert digest == hashlib.sha256(data).digest()


def test_sign_and_verify_cycle_success(rsa_keypair):
    """Signing a message hash and verifying with matching public key should succeed."""
    message = b"hello trace"
    message_hash = hashlib.sha256(message).digest()

    signature = sign_hash_with_key_content(rsa_keypair["private_pem"], message_hash)
    is_valid = verify_signature_with_key_content(
        rsa_keypair["public_pem"], message_hash, signature
    )

    assert isinstance(signature, bytes)
    assert len(signature) > 0
    assert is_valid is True


def test_verify_fails_when_message_is_modified(rsa_keypair):
    """Verification should fail if message hash differs from signed hash."""
    original = b"original message"
    tampered = b"original message!"

    original_hash = hashlib.sha256(original).digest()
    tampered_hash = hashlib.sha256(tampered).digest()

    signature = sign_hash_with_key_content(rsa_keypair["private_pem"], original_hash)
    is_valid = verify_signature_with_key_content(
        rsa_keypair["public_pem"], tampered_hash, signature
    )

    assert is_valid is False


def test_verify_fails_when_signature_is_modified(rsa_keypair):
    """Verification should fail if signature bytes are tampered."""
    message = b"another message"
    message_hash = hashlib.sha256(message).digest()

    signature = bytearray(
        sign_hash_with_key_content(rsa_keypair["private_pem"], message_hash)
    )
    signature[-1] ^= 0x01  # Flip one bit

    is_valid = verify_signature_with_key_content(
        rsa_keypair["public_pem"], message_hash, bytes(signature)
    )

    assert is_valid is False
