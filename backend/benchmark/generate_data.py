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

    # Vom avea 30 de imagini atent calculate pentru a atinge limitele fizice
    # la diferite block size-uri, avand mesajul FIX de 2272 biti.

    configs = [
        # --- GRUPUL 1: Cutii Mici (High Density pentru Block 4 și 6) ---
        # Aici Block 8/10/12 probabil vor da "CapacityExceeded", dar e normal.
        ("01_G1_Solid_Reso_400x400.png", 400, 400, _gen_solid),
        ("02_G1_Noise_Reso_400x400.png", 400, 400, _gen_noise),
        ("03_G1_Solid_Odd_410x390.png", 410, 390, _gen_solid),  # Asimetric
        ("04_G1_Noise_Odd_410x390.png", 410, 390, _gen_noise),
        ("05_G1_Solid_Extreme_500x300.png", 500, 300, _gen_solid),  # Raport diferit

        # --- GRUPUL 2: Cutii Medii (High Density pentru Block 8) ---
        # Aici Block 4/6 au Low Density (sunt safe). Block 10/12 s-ar putea sa pice de spatiu.
        ("06_G2_Solid_Reso_800x800.png", 800, 800, _gen_solid),
        ("07_G2_Noise_Reso_800x800.png", 800, 800, _gen_noise),
        ("08_G2_Solid_Odd_814x786.png", 814, 786, _gen_solid),  # Lățime dă rest, padding masiv
        ("09_G2_Noise_Odd_814x786.png", 814, 786, _gen_noise),
        ("10_G2_Gradient_Odd_822x750.png", 822, 750, _gen_gradient),

        # --- GRUPUL 3: Cutii Mari (High Density pentru Block 10 și 12) ---
        ("11_G3_Solid_Reso_1040x960.png", 1040, 960, _gen_solid),  # Aproape 1 milion de pixeli
        ("12_G3_Noise_Reso_1040x960.png", 1040, 960, _gen_noise),
        ("13_G3_Solid_Odd_1058x942.png", 1058, 942, _gen_solid),  # Padding puternic
        ("14_G3_Noise_Odd_1058x942.png", 1058, 942, _gen_noise),
        ("15_G3_Checker_Odd_1100x900.png", 1100, 900, _gen_checkerboard),

        # --- GRUPUL 4: Formate Real-World și Asimetrice ---
        # Astea au lățimi/înălțimi ciudate din viața reală.
        ("16_G4_Solid_Legacy_1024x768.png", 1024, 768, _gen_solid),  # 4:3 clasic
        ("17_G4_Noise_Legacy_1024x768.png", 1024, 768, _gen_noise),
        ("18_G4_Solid_Laptop_1366x768.png", 1366, 768, _gen_solid),  # Laptop clasic (1366 / 2 = 683 - mereu cu rest)
        ("19_G4_Noise_Laptop_1366x768.png", 1366, 768, _gen_noise),
        ("20_G4_Solid_Vertical_720x1280.png", 720, 1280, _gen_solid),  # Poza de telefon verticala
        ("21_G4_Noise_Vertical_720x1280.png", 720, 1280, _gen_noise),

        # --- GRUPUL 5: Imagini Uriașe (Low Density pentru toate blocurile) ---
        # Aici payload-ul se oprește devreme. Padding-ul de la margini NU ar trebui să afecteze deloc.
        ("22_G5_Solid_FHD_1920x1080.png", 1920, 1080, _gen_solid),
        ("23_G5_Noise_FHD_1920x1080.png", 1920, 1080, _gen_noise),
        ("24_G5_Solid_FHD_Odd_1934x1094.png", 1934, 1094, _gen_solid),  # HD asimetric
        ("25_G5_Noise_FHD_Odd_1934x1094.png", 1934, 1094, _gen_noise),

        # --- GRUPUL 6: Extreme Stress ---
        ("26_G6_Solid_Ultrawide_2560x500.png", 2560, 500, _gen_solid),  # Foarte lata, scurta
        ("27_G6_Noise_Ultrawide_2560x500.png", 2560, 500, _gen_noise),
        ("28_G6_Solid_Prime_1009x1009.png", 1009, 1009, _gen_solid),  # Numere prime absolute
        ("29_G6_Noise_Prime_1009x1009.png", 1009, 1009, _gen_noise),
        ("30_G6_Checker_Prime_1009x1009.png", 1009, 1009, _gen_checkerboard),
    ]

    for filename, w, h, fn in configs:
        img = fn(w, h)
        out = _write_png(filename, img)
        print(f"  [+] {out.name:<40} | DWT: {w // 2}x{h // 2}")

    print("\nDataset ready! 30 carefully crafted stress images.")


if __name__ == "__main__":
    main()