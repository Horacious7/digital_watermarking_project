"""
Test script to verify signature capacity calculations
"""
import sys

# Fix Windows console encoding for emojis
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Simulate capacity calculation
def calculate_payload_size(message_text):
    """Calculate total payload size including signature"""

    # Constants (matching api.py)
    RSA_SIGNATURE_SIZE = 256  # bytes for RSA-2048
    SIGNATURE_LENGTH_FIELD = 4  # bytes to store signature length
    MESSAGE_TERMINATOR_SIZE = 4  # bytes for null terminator
    SAFETY_MARGIN_BYTES = 1  # Extra byte for safe extraction
    SIGNATURE_OVERHEAD = SIGNATURE_LENGTH_FIELD + RSA_SIGNATURE_SIZE + MESSAGE_TERMINATOR_SIZE + SAFETY_MARGIN_BYTES

    # Calculate message size
    message_bytes = len(message_text.encode('utf-8'))

    # Calculate total payload
    total_payload_bytes = message_bytes + SIGNATURE_OVERHEAD
    total_payload_bits = total_payload_bytes * 8

    return {
        'message_bytes': message_bytes,
        'signature_overhead': SIGNATURE_OVERHEAD,
        'total_bytes': total_payload_bytes,
        'total_bits': total_payload_bits
    }

# Test cases
test_messages = [
    "Test",
    "deci daca mesajul este foarte lung crapa la un anumit block size aaaaaaaaaaaaaaaaaaaaaaa",
    "A" * 50,
    "A" * 90,  # Edge case: should work
    "A" * 91,  # Edge case: should now fail (previously worked but caused signature errors)
    "A" * 92,  # Edge case: should fail
    "A" * 100,
    "A" * 200
]

# Image capacities for 640x1138 image
capacities = {
    8: {'bytes': 355, 'bits': 2840},
    7: {'bytes': 455, 'bits': 3645},
    6: {'bytes': 622, 'bits': 4982}
}

print("=" * 80)
print("SIGNATURE CAPACITY TEST")
print("=" * 80)

for msg in test_messages:
    payload = calculate_payload_size(msg)

    print(f"\n📝 Message: '{msg[:50]}{'...' if len(msg) > 50 else ''}'")
    print(f"   Message size: {payload['message_bytes']} bytes")
    print(f"   Signature overhead: {payload['signature_overhead']} bytes")
    print(f"   Total payload: {payload['total_bytes']} bytes ({payload['total_bits']} bits)")
    print(f"\n   Fits in image 640x1138:")

    for block_size, cap in capacities.items():
        fits = payload['total_bits'] <= cap['bits']
        space_left = cap['bytes'] - payload['total_bytes']
        status = "✅ FITS" if fits else "❌ TOO BIG"

        print(f"   • Block {block_size} ({cap['bytes']} bytes): {status} ({space_left:+d} bytes)")

print("\n" + "=" * 80)
print("OVERHEAD BREAKDOWN")
print("=" * 80)
print("• Signature length field: 4 bytes")
print("• RSA-2048 signature: 256 bytes")
print("• Message terminator: 4 bytes")
print("• Safety margin: 1 byte (prevents extraction errors)")
print("• TOTAL OVERHEAD: 265 bytes")
print("=" * 80)

