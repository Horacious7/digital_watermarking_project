from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np


DATASET_DIR = Path(__file__).resolve().parent / "dataset"
WIDTH = 1920
HEIGHT = 1080


def _write_png(name: str, image_bgr: np.ndarray) -> Path:
    DATASET_DIR.mkdir(parents=True, exist_ok=True)
    out_path = DATASET_DIR / name
    ok = cv2.imwrite(str(out_path), image_bgr)
    if not ok:
        raise RuntimeError(f"Failed to write image: {out_path}")
    return out_path


def _solid_gray() -> np.ndarray:
    gray = np.full((HEIGHT, WIDTH, 3), 128, dtype=np.uint8)
    return gray


def _horizontal_gradient() -> np.ndarray:
    line = np.linspace(0, 255, WIDTH, dtype=np.uint8)
    img = np.tile(line, (HEIGHT, 1))
    return cv2.merge([img, img, img])


def _checkerboard(tile: int = 16) -> np.ndarray:
    y = np.arange(HEIGHT)[:, None]
    x = np.arange(WIDTH)[None, :]
    board = (((x // tile) + (y // tile)) % 2 * 255).astype(np.uint8)
    return cv2.merge([board, board, board])


def _random_noise(seed: int = 1337) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return rng.integers(0, 256, size=(HEIGHT, WIDTH, 3), dtype=np.uint8)


def _sine_waves() -> np.ndarray:
    x = np.linspace(0, 2 * np.pi, WIDTH, dtype=np.float32)
    y = np.linspace(0, 2 * np.pi, HEIGHT, dtype=np.float32)
    xv, yv = np.meshgrid(x, y)
    wave1 = (np.sin(12 * xv) + 1.0) * 127.5
    wave2 = (np.sin(8 * yv) + 1.0) * 127.5
    wave3 = (np.sin(6 * xv + 5 * yv) + 1.0) * 127.5
    return cv2.merge([
        wave1.astype(np.uint8),
        wave2.astype(np.uint8),
        wave3.astype(np.uint8),
    ])


def _rgb_color_blocks() -> np.ndarray:
    img = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
    h2 = HEIGHT // 2
    w3 = WIDTH // 3
    colors = [
        (255, 0, 0),
        (0, 255, 0),
        (0, 0, 255),
        (255, 255, 0),
        (255, 0, 255),
        (0, 255, 255),
    ]
    idx = 0
    for r in range(2):
        for c in range(3):
            y0, y1 = r * h2, HEIGHT if r == 1 else (r + 1) * h2
            x0, x1 = c * w3, WIDTH if c == 2 else (c + 1) * w3
            img[y0:y1, x0:x1] = colors[idx]
            idx += 1
    return img


def _concentric_circles() -> np.ndarray:
    yy, xx = np.indices((HEIGHT, WIDTH), dtype=np.float32)
    cx, cy = WIDTH / 2.0, HEIGHT / 2.0
    radius = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
    rings = ((np.sin(radius / 8.0) + 1.0) * 127.5).astype(np.uint8)
    return cv2.merge([rings, rings, rings])


def _large_uniform() -> np.ndarray:
    return np.full((1800, 2400, 3), 90, dtype=np.uint8)


def main() -> None:
    generators = [
        ("01_solid_gray_1920x1080.png", _solid_gray),
        ("02_horizontal_gradient_1920x1080.png", _horizontal_gradient),
        ("03_checkerboard_1920x1080.png", _checkerboard),
        ("04_random_noise_1920x1080.png", _random_noise),
        ("05_sine_waves_1920x1080.png", _sine_waves),
        ("06_rgb_blocks_1920x1080.png", _rgb_color_blocks),
        ("07_concentric_circles_1920x1080.png", _concentric_circles),
        ("08_large_uniform_2400x1800.png", _large_uniform),
    ]

    print(f"Generating synthetic dataset in: {DATASET_DIR}")
    for filename, fn in generators:
        img = fn()
        out = _write_png(filename, img)
        print(f"  - saved {out.name} ({img.shape[1]}x{img.shape[0]})")

    print("Done. Generated 8 lossless PNG images.")


if __name__ == "__main__":
    main()

