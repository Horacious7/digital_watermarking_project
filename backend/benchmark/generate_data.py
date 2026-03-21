from __future__ import annotations
from pathlib import Path
import cv2
import numpy as np

DATASET_DIR = Path(__file__).resolve().parent / "dataset"


def _write_png(name: str, image_bgr: np.ndarray) -> Path:
    DATASET_DIR.mkdir(parents=True, exist_ok=True)
    out_path = DATASET_DIR / name
    cv2.imwrite(str(out_path), image_bgr)
    return out_path


# --- Generatoare de Entropie ---
def _gen_solid(w, h) -> np.ndarray: return np.full((h, w, 3), 150, dtype=np.uint8)


def _gen_noise(w, h) -> np.ndarray: return np.random.randint(0, 256, (h, w, 3), dtype=np.uint8)


def _gen_gradient(w, h) -> np.ndarray:
    line = np.linspace(0, 255, w, dtype=np.uint8)
    img = np.tile(line, (h, 1))
    return cv2.merge([img, img, img])


def _gen_checkerboard(w, h, tile=16) -> np.ndarray:
    y = np.arange(h)[:, None];
    x = np.arange(w)[None, :]
    board = (((x // tile) + (y // tile)) % 2 * 255).astype(np.uint8)
    return cv2.merge([board, board, board])


def main() -> None:
    print(f"Generating THE ULTIMATE STRESS MATRIX in: {DATASET_DIR}")

    configs = [
        # --- GROUP 1: LOW RESONANCE / HIGH PADDING (Crucial for the comparison) ---
        # These resolutions are prime or near-prime, forcing maximum padding (remainder 1).
        # Prediction: Without optimization, these should fail on most block sizes.
        ("01_G1_Solid_Prime_1009x1009.png", 1009, 1009, _gen_solid),  # Extreme edge case
        ("02_G1_Noise_Prime_1009x1009.png", 1009, 1009, _gen_noise),  # Entropy vs Truncation
        ("03_G1_Solid_Remainder_513x513.png", 513, 513, _gen_solid),  # Small image, heavy padding

        # --- GROUP 2: REAL-WORLD LEGACY RESOLUTIONS ---
        # Common resolutions that are not multiples of (BlockSize * 2).
        ("04_G2_Solid_Laptop_1366x768.png", 1366, 768, _gen_solid),  # W mod 16 = 6
        ("05_G2_Noise_Laptop_1366x768.png", 1366, 768, _gen_noise),  # High entropy version
        ("06_G2_Solid_SD_720x480.png", 720, 480, _gen_solid),  # Classic DVD resolution

        # --- GROUP 3: ASPECT RATIO STRESS (Ultra-Wide vs Vertical) ---
        # Testing how the embedding behaves when rows are extremely long or short.
        ("07_G3_Solid_UltraWide_2560x601.png", 2560, 601, _gen_solid),  # H mod 16 = 1 (Bottom padding)
        ("08_G3_Noise_Mobile_1080x1921.png", 1080, 1921, _gen_noise),  # V-Padding on mobile format
        ("09_G3_Gradient_Wide_1600x900.png", 1600, 900, _gen_gradient),  # Balanced but odd grid

        # --- GROUP 4: PERFECT RESONANCE (Control Group) ---
        # These should pass 100% in both modes. Used to prove the baseline is stable.
        ("10_G4_Solid_Perfect_1024x1024.png", 1024, 1024, _gen_solid),  # Power of 2
        ("11_G4_Noise_Perfect_1920x1080.png", 1920, 1080, _gen_noise),  # Standard Full HD

        # --- GROUP 5: CAPACITY LIMIT TESTING ---
        # High-density images where message fits but fills almost the entire grid.
        ("12_G5_Solid_Dense_400x400.png", 400, 400, _gen_solid),  # High density for Block 4/6
        ("13_G5_Checker_Dense_800x800.png", 800, 800, _gen_checkerboard),  # Pattern interference

        # --- GROUP 6: UNIQUE ARTIFACTS ---
        # Testing the impact of gradients and complex checker patterns on padding truncation.
        ("14_G6_Gradient_Odd_1001x1001.png", 1001, 1001, _gen_gradient),
        ("15_G6_Checker_Odd_1203x901.png", 1203, 901, _gen_checkerboard)
    ]

    for filename, w, h, fn in configs:
        img = fn(w, h)
        out = _write_png(filename, img)
        print(f"  [+] {out.name:<40} | DWT: {w // 2}x{h // 2}")

    print("\nDataset ready! 30 carefully crafted stress images.")


if __name__ == "__main__":
    main()