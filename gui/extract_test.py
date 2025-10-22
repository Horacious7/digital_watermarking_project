import traceback
from pathlib import Path
import cv2, pywt

project_root = Path(__file__).resolve().parent.parent
img_path = project_root / 'watermarked' / 'test_wm_signed.png'
print('Testing image:', img_path)
if not img_path.exists():
    print('Image not found, abort')
    raise SystemExit(1)

from watermarking.extract import extract_watermark
from utils.conversions import bits_to_bytes

# find public key
candidate_pub = [project_root / 'data' / 'keys' / 'public.pem', project_root / 'keys' / 'public.pem']
pub = None
for p in candidate_pub:
    if p.exists():
        pub = p
        break
print('Public key used:', pub)

for b in range(2, 17):
    try:
        img = cv2.imread(str(img_path), cv2.IMREAD_COLOR)
        blue = img[:, :, 0].astype('float32')
        cA, _ = pywt.dwt2(blue, 'haar')
        h, w = cA.shape
        num_blocks = (h // b) * (w // b)
        print('\nblock_size=', b, 'capacity_bits=', num_blocks)
        bits = extract_watermark(str(img_path), num_blocks, block_size=b)
        print('extracted bits len=', len(bits))
        ex_bytes = bits_to_bytes(bits)
        print('extracted bytes len=', len(ex_bytes))
        if len(ex_bytes) >= 4:
            sig_len = int.from_bytes(ex_bytes[0:4], 'big')
            print('sig_len field=', sig_len)
            if len(ex_bytes) >= 4 + sig_len:
                signature = ex_bytes[4:4+sig_len]
                message = ex_bytes[4+sig_len:]
                print('message bytes len=', len(message))
                try:
                    msg_text = message.decode('utf-8')
                except Exception:
                    msg_text = message.decode('utf-8', errors='replace')
                print('message preview:', repr(msg_text[:200]))
                # try verify if pub exists
                if pub is not None:
                    from crypto.verify import verify_signature
                    ok = verify_signature(str(pub), message, signature)
                    print('verify_signature ->', ok)
            else:
                print('Not enough bytes for signature: have', len(ex_bytes)-4, 'need', sig_len)
        else:
            print('Too few extracted bytes (<4)')
    except Exception:
        print('ERROR for block size', b)
        traceback.print_exc()

print('\nDone')

