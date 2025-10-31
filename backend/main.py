from crypto.sign import sign_hash
from crypto.verify import verify_signature
from utils.conversions import text_to_bits, bits_to_text, bytes_to_bits, bits_to_bytes
from watermarking.embed import embed_watermark
from watermarking.extract import extract_watermark
import cv2
import numpy as np
import pywt

# Configuration
PRIVATE_KEY = "data/keys/private.pem"
PUBLIC_KEY = "data/keys/public.pem"
INPUT_IMAGE = "data/test.png"
OUTPUT_IMAGE = "data/watermarked/test_wm_signed.png"
BLOCK_SIZE = 8

# Message to embed (watermark)
text = "GloryToLordJesusChrist"
message_bytes = text.encode('utf-8')

# Sign the message bytes with the private key
signature = sign_hash(PRIVATE_KEY, message_bytes)
print("Signature length (bytes):", len(signature))

# Build payload: 4-byte big-endian signature length + signature + message
sig_len_bytes = len(signature).to_bytes(4, 'big')
payload = sig_len_bytes + signature + message_bytes
payload_bits = bytes_to_bits(payload)

# Compute available capacity using DWT approximation size (must match embed logic)
img = cv2.imread(INPUT_IMAGE, cv2.IMREAD_COLOR)
if img is None:
    raise FileNotFoundError(f"Input image not found: {INPUT_IMAGE}")
blue = img[:, :, 0].astype(np.float32)
coeffs2 = pywt.dwt2(blue, 'haar')
cA, _ = coeffs2
cA_h, cA_w = cA.shape
num_blocks = (cA_h // BLOCK_SIZE) * (cA_w // BLOCK_SIZE)
print(f"Available blocks (blue channel, DWT cA): {num_blocks}, Payload bits: {len(payload_bits)}")

if len(payload_bits) > num_blocks:
    raise ValueError("Payload too large for available embedding capacity. Reduce message or use larger image.")

# Embed payload bits
embed_watermark(INPUT_IMAGE, payload_bits, OUTPUT_IMAGE, block_size=BLOCK_SIZE)

# Extract exactly the number of bits we embedded
extracted_bits = extract_watermark(OUTPUT_IMAGE, len(payload_bits), block_size=BLOCK_SIZE)
extracted_bytes = bits_to_bytes(extracted_bits)

# Parse payload
ex_sig_len = int.from_bytes(extracted_bytes[0:4], 'big')
ex_signature = extracted_bytes[4:4+ex_sig_len]
ex_message = extracted_bytes[4+ex_sig_len:]
try:
    ex_text = ex_message.decode('utf-8')
except Exception:
    ex_text = ex_message.decode('utf-8', errors='replace')

print("Original message:", text)
print("Recovered message:", ex_text)

# Verify signature with public key
is_valid = verify_signature(PUBLIC_KEY, ex_message, ex_signature)
print("Signature valid?", is_valid)

print("✅ End-to-end signed-watermark flow complete.")
