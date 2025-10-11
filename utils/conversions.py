# conversions.py

def text_to_bits(text):
    """Convert text string to bits."""
    return ''.join(format(ord(c), '08b') for c in text)

def bits_to_text(bits):
    """Convert bits string to text."""
    chars = [bits[i:i + 8] for i in range(0, len(bits), 8)]
    return ''.join(chr(int(b, 2)) for b in chars)

# Testing the functions
s = "Museum123"
print(bits_to_text(text_to_bits(s)) == s)