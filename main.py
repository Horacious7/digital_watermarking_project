from utils.hashing import hash_image
from utils.conversions import text_to_bits, bits_to_text
from utils.image_utils import load_image, save_image

print("HASH:", hash_image("data/test.jpg").hex()[:32], "...")

text = "MuseumTest"
bits = text_to_bits(text)
print("Bits:", bits[:32], "...")
print("Recovered:", bits_to_text(bits))

img = load_image("data/test.jpg")
save_image(img, "data/copy_test.jpg")
print("✅ Image loaded and saved successfully!")
