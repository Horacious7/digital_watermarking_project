from __future__ import annotations

from pathlib import Path
import cv2
import numpy as np

DATASET_DIR = Path(__file__).resolve().parent / "dataset"


def _write_png(name: str, image_bgr: np.ndarray) -> Path:
    DATASET_DIR.mkdir(parents=True, exist_ok=True)
    out_path = DATASET_DIR / name
    ok = cv2.imwrite(str(out_path), image_bgr)
    if not ok:
        raise RuntimeError(f"Failed to write image: {out_path}")
    return out_path


# --- Generation Helpers (using original logic) ---

def _gen_solid(w, h, val=128) -> np.ndarray:
    return np.full((h, w, 3), val, dtype=np.uint8)


def _gen_gradient(w, h) -> np.ndarray:
    line = np.linspace(0, 255, w, dtype=np.uint8)
    img = np.tile(line, (h, 1))
    return cv2.merge([img, img, img])


def _gen_checkerboard(w, h, tile: int = 16) -> np.ndarray:
    y = np.arange(h)[:, None]
    x = np.arange(w)[None, :]
    board = (((x // tile) + (y // tile)) % 2 * 255).astype(np.uint8)
    return cv2.merge([board, board, board])


def _gen_random_noise(w, h, seed: int = 1337) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return rng.integers(0, 256, size=(h, w, 3), dtype=np.uint8)


def _gen_sine_waves(w, h) -> np.ndarray:
    x = np.linspace(0, 2 * np.pi, w, dtype=np.float32)
    y = np.linspace(0, 2 * np.pi, h, dtype=np.float32)
    xv, yv = np.meshgrid(x, y)
    wave1 = (np.sin(12 * xv) + 1.0) * 127.5
    wave2 = (np.sin(8 * yv) + 1.0) * 127.5
    wave3 = (np.sin(6 * xv + 5 * yv) + 1.0) * 127.5
    return cv2.merge([
        wave1.astype(np.uint8),
        wave2.astype(np.uint8),
        wave3.astype(np.uint8),
    ])


def _gen_rgb_blocks(w, h) -> np.ndarray:
    img = np.zeros((h, w, 3), dtype=np.uint8)
    h2, w3 = h // 2, w // 3
    colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255), (0, 255, 255)]
    idx = 0
    for r in range(2):
        for c in range(3):
            y0, y1 = r * h2, h if r == 1 else (r + 1) * h2
            x0, x1 = c * w3, w if c == 2 else (c + 1) * w3
            img[y0:y1, x0:x1] = colors[idx]
            idx += 1
    return img


def _gen_concentric_circles(w, h) -> np.ndarray:
    yy, xx = np.indices((h, w), dtype=np.float32)
    cx, cy = w / 2.0, h / 2.0
    radius = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
    rings = ((np.sin(radius / 8.0) + 1.0) * 127.5).astype(np.uint8)
    return cv2.merge([rings, rings, rings])


def main() -> None:
    print(f"Initializing Empirical Dataset Generation in: {DATASET_DIR}")

    # Configuration list: (filename, width, height, generator_function)
    configs = [
        # --- 1. NEW SET (1080p Standard, Resonant) ---
        ("synthetic_1920x1080_solid_gray.png", 1920, 1080, _gen_solid),
        ("synthetic_1920x1080_gradient.png", 1920, 1080, _gen_gradient),
        ("synthetic_1920x1080_checkerboard.png", 1920, 1080, _gen_checkerboard),
        ("synthetic_1920x1080_noise.png", 1920, 1080, _gen_random_noise),
        ("synthetic_1920x1080_sinewaves.png", 1920, 1080, _gen_sine_waves),
        ("synthetic_1920x1080_rgb_blocks.png", 1920, 1080, _gen_rgb_blocks),
        ("synthetic_1920x1080_circles.png", 1920, 1080, _gen_concentric_circles),
        ("synthetic_2400x1800_uniform.png", 2400, 1800, lambda w, h: _gen_solid(w, h, 90)),

        # --- 2. LEGACY SET (Arbitrary resolutions that failed on blocks 10, 12, 14) ---
        ("legacy_0686x1024_gradient.png", 686, 1024, _gen_gradient),
        ("legacy_1024x1024_solid_200.png", 1024, 1024, lambda w, h: _gen_solid(w, h, 200)),
        ("legacy_1024x1024_solid_150.png", 1024, 1024, lambda w, h: _gen_solid(w, h, 150)),
        ("legacy_1024x0768_solid_100.png", 1024, 768, lambda w, h: _gen_solid(w, h, 100)),
        ("legacy_0819x1024_noise.png", 819, 1024, _gen_random_noise),
        ("legacy_0640x1138_colorblocks.png", 640, 1138, _gen_rgb_blocks),
        ("legacy_1024x0768_sinewaves.png", 1024, 768, _gen_sine_waves),

        # --- 3. SURGICAL EXPERIMENT (Resonance Demonstration) ---

        # For Block Size 7 (Multiplier: 14) -> Resonant DWT is 980x490
        ("surgical_block07_RESONANT_1960x0980.png", 1960, 980, _gen_random_noise),
        ("surgical_block07_NONRESONANT_1970x0990.png", 1970, 990, _gen_random_noise),

        # For Block Size 8 (Multiplier: 16) -> Resonant DWT is 960x544
        ("surgical_block08_RESONANT_1920x1088.png", 1920, 1088, _gen_random_noise),
        ("surgical_block08_NONRESONANT_1930x1098.png", 1930, 1098, _gen_random_noise),

        # For Block Size 10 (Multiplier: 20) -> Resonant DWT is 1000x500
        ("surgical_block10_RESONANT_2000x1000.png", 2000, 1000, _gen_random_noise),
        ("surgical_block10_NONRESONANT_2010x1010.png", 2010, 1010, _gen_random_noise),

        # For Block Size 11 (Multiplier: 22) -> Resonant DWT is 990x550
        ("surgical_block11_RESONANT_1980x1100.png", 1980, 1100, _gen_random_noise),
        ("surgical_block11_NONRESONANT_1990x1110.png", 1990, 1110, _gen_random_noise),

        # For Block Size 12 (Multiplier: 24) -> Resonant DWT is 960x480
        ("surgical_block12_RESONANT_1920x0960.png", 1920, 960, _gen_random_noise),
        ("surgical_block12_NONRESONANT_1930x0970.png", 1930, 970, _gen_random_noise),

        # For Block Size 13 (Multiplier: 26) -> Resonant DWT is 1040x520
        ("surgical_block13_RESONANT_2080x1040.png", 2080, 1040, _gen_random_noise),
        ("surgical_block13_NONRESONANT_2090x1050.png", 2090, 1050, _gen_random_noise),

        # =====================================================================
        # --- PHASE 1: Low-Density Controls (2000x1000, 5000 slots, ~45% density) ---
        # Data remains safe in the top-left, away from bottom-right padded edges.
        # =====================================================================

        # Scenario A: High Entropy, Resonant (Perfect grid) -> EXPECT PASS
        ("ultra_H_RESO_LODENS_2000x1000.png", 2000, 1000, _gen_random_noise),

        # Scenario B: Low Entropy, Resonant (Perfect grid) -> EXPECT PASS
        ("ultra_L_RESO_LODENS_2000x1000.png", 2000, 1000, lambda w, h: _gen_solid(w, h, 150)),

        # Scenario C: High Entropy, Non-Resonant (Padded edges) -> EXPECT PASS
        # High entropy masking prevents ripple from affecting coefficients.
        ("ultra_H_NONRESO_LODENS_2010x1010.png", 2010, 1010, _gen_random_noise),

        # Scenario D: Low Entropy, Non-Resonant (Padded edges) -> EXPECT PASS
        # Although padded edges exist, low payload density doesn't reach them.
        ("ultra_L_NONRESO_LODENS_2010x1010.png", 2010, 1010, lambda w, h: _gen_solid(w, h, 150)),

        # =====================================================================
        # --- PHASE 2: High-Density Targets (approx 1020x1020, 2601 slots, ~87% density) ---
        # Data is forced into the dangerous bottom-right edges.
        # =====================================================================

        # Target 1: High Entropy, Resonant (Perfect grid) -> EXPECT PASS
        ("ultra_H_RESO_HIDENS_1020x1020.png", 1020, 1020, _gen_random_noise),

        # Target 2: High Entropy, Non-Resonant (Padded edges) -> EXPECT PASS (w/ margin)
        # Low coefficients are corrupted, but large entropy usually absorbs it.
        ("ultra_H_NONRESO_HIDENS_1030x1030.png", 1030, 1030, _gen_random_noise),

        # Target 3: Low Entropy, Resonant (Perfect grid) -> EXPECT PASS
        ("ultra_L_RESO_HIDENS_1020x1020.png", 1020, 1020, lambda w, h: _gen_solid(w, h, 150)),

        # Target 4: Low Entropy, Non-Resonant (Padded edges) -> EXPECT FAIL (THE CRASH)
        # Triple-Constraint Mismatch: non-resonant ripple, low-entropy vulnerability, high payload density hitting edges.
        ("ultra_L_NONRESO_HIDENS_1030x1030.png", 1030, 1030, lambda w, h: _gen_solid(w, h, 150)),


    ]


    for filename, w, h, fn in configs:
        img = fn(w, h)
        out = _write_png(filename, img)
        print(f"  [+] Created: {out.name}")

    print(f"\nDataset generation complete. Total images: {len(configs)}")


if __name__ == "__main__":
    main()