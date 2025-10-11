from utils.hashing import hash_image

from crypto.sign import sign_hash
from crypto.verify import verify_signature

## 1️⃣ Generate keys
#generate_rsa_keys("data/keys/private.pem", "data/keys/public.pem")
#
## 2️⃣ Hash image
#img_hash = hash_image("data/test.jpg")
#print("HASH:", img_hash.hex()[:32], "...")
#
## 3️⃣ Sign hash
#signature = sign_hash("data/keys/private.pem", img_hash)
#print("Signature length:", len(signature))
#
## 4️⃣ Verify signature
#valid = verify_signature("data/keys/public.pem", img_hash, signature)
#print("Signature valid?", valid)
#print("✅ All done!")

from utils.conversions import text_to_bits, bits_to_text
from watermarking.embed import embed_watermark
from watermarking.extract import extract_watermark
import cv2
import numpy as np

text = "GloryToLordJesusChrist"
bits = text_to_bits(text)

# Check number of available blocks
img = cv2.imread("data/test.png", cv2.IMREAD_GRAYSCALE)
h, w = img.shape
block_size = 8
num_blocks = (h // block_size) * (w // block_size)
print(f"Available blocks: {num_blocks}, Watermark bits: {len(bits)}")

# Embed
embed_watermark("data/test.png", bits, "data/watermarked/test_wm.png")

# Extract
extracted_bits = extract_watermark("data/watermarked/test_wm.png", len(bits))
print("Embedded bits:", bits)
print("Extracted bits:", extracted_bits)
recovered_text = bits_to_text(extracted_bits)

print("Original:", text)
print("Recovered:", recovered_text)
print("✅ Watermark extraction correct?", recovered_text == text)
