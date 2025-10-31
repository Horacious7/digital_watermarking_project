# conversions.py

def text_to_bits(text: str) -> str:
    """Convert text string to bits."""
    return ''.join(format(ord(c), '08b') for c in text)


def bits_to_text(bits: str) -> str:
    """Convert bits string to text."""
    chars = [bits[i:i + 8] for i in range(0, len(bits), 8)]
    return ''.join(chr(int(b, 2)) for b in chars)


def bytes_to_bits(data: bytes) -> str:
    """Convert bytes to bit string."""
    return ''.join(format(b, '08b') for b in data)


def bits_to_bytes(bits: str) -> bytes:
    """Convert bit string to bytes. If bits length not multiple of 8, it will pad with zeros on the right."""
    # pad to full byte
    rem = len(bits) % 8
    if rem != 0:
        bits = bits + '0' * (8 - rem)
    byte_chunks = [bits[i:i+8] for i in range(0, len(bits), 8)]
    return bytes(int(b, 2) for b in byte_chunks)
