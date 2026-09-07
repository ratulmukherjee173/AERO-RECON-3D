"""
Generate a synthetic drone-style test video with:
- Moving camera (pan + tilt simulation via image warp)
- Textured ground plane (randomised terrain pattern)
- Sufficient texture for SIFT feature detection

Output: backend/data/samples/test_drone.mp4
"""
import cv2
import numpy as np
from pathlib import Path

# ── Settings ──────────────────────────────────────────────────────────────
OUT_PATH = Path(__file__).parent / "data" / "samples" / "test_drone.mp4"
OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

WIDTH, HEIGHT = 1280, 720
FPS = 30
DURATION_S = 20  # 20 seconds → 600 frames
N_FRAMES = FPS * DURATION_S

# ── Generate base terrain texture (randomised, feature-rich) ──────────────
np.random.seed(42)
terrain = np.zeros((HEIGHT * 3, WIDTH * 3, 3), dtype=np.uint8)

# Ground colour base
terrain[:] = (120, 160, 80)  # green-ish

# Add dirt patches
rng = np.random.default_rng(42)
for _ in range(200):
    cx, cy = rng.integers(0, WIDTH*3), rng.integers(0, HEIGHT*3)
    r = rng.integers(20, 120)
    col = (int(rng.integers(100, 200)), int(rng.integers(80, 160)), int(rng.integers(60, 140)))
    cv2.ellipse(terrain, (cx, cy), (r, r//2), int(rng.integers(0,180)), 0, 360, col, -1)

# Add roads / lines
for _ in range(30):
    x1, y1 = rng.integers(0, WIDTH*3), rng.integers(0, HEIGHT*3)
    x2, y2 = rng.integers(0, WIDTH*3), rng.integers(0, HEIGHT*3)
    thickness = int(rng.integers(4, 20))
    col = tuple(int(x) for x in rng.integers(40, 200, 3).tolist())
    cv2.line(terrain, (x1,y1), (x2,y2), col, thickness)

# Add buildings (rectangles with contrast)
for _ in range(60):
    bx, by = rng.integers(0, WIDTH*3-100), rng.integers(0, HEIGHT*3-100)
    bw, bh = rng.integers(30, 120), rng.integers(30, 100)
    col = tuple(int(x) for x in rng.integers(60, 220, 3).tolist())
    cv2.rectangle(terrain, (bx, by), (bx+bw, by+bh), col, -1)
    cv2.rectangle(terrain, (bx, by), (bx+bw, by+bh), (50,50,50), 2)

# Add Gaussian noise for texture
noise = rng.integers(0, 30, terrain.shape, dtype=np.uint8)
terrain = np.clip(terrain.astype(np.int16) + noise - 15, 0, 255).astype(np.uint8)

print(f"Terrain texture: {terrain.shape}")

# ── Video writer ─────────────────────────────────────────────────────────
fourcc = cv2.VideoWriter_fourcc(*"mp4v")
writer = cv2.VideoWriter(str(OUT_PATH), fourcc, FPS, (WIDTH, HEIGHT))

# ── Camera simulation: slow pan across terrain ────────────────────────────
# Start position in terrain image space
start_x = WIDTH
start_y = HEIGHT
# Move diagonally to simulate drone forward flight + slight drift
dx_total = WIDTH * 0.8
dy_total = HEIGHT * 0.5

for i in range(N_FRAMES):
    t = i / N_FRAMES

    # Translate camera (smooth, sinusoidal drift for realism)
    cx = start_x + int(dx_total * t + 20 * np.sin(t * np.pi * 3))
    cy = start_y + int(dy_total * t + 10 * np.sin(t * np.pi * 5))

    # Slight altitude change (scale terrain view up/down a tiny bit)
    scale = 1.0 + 0.05 * np.sin(t * np.pi * 2)

    # Build affine warp matrix (translate + slight scale)
    M = np.array([
        [scale, 0, cx - WIDTH//2 * scale],
        [0, scale, cy - HEIGHT//2 * scale],
    ], dtype=np.float32)

    frame = cv2.warpAffine(terrain, M, (WIDTH, HEIGHT),
                            flags=cv2.INTER_LINEAR,
                            borderMode=cv2.BORDER_REFLECT_101)

    # Slight motion blur to simulate real drone footage
    if i % 5 == 0:
        kernel = np.zeros((5, 5))
        kernel[2, :] = 1.0 / 5
        frame = cv2.filter2D(frame, -1, kernel)

    writer.write(frame)
    if i % 60 == 0:
        print(f"  Frame {i}/{N_FRAMES}")

writer.release()
print(f"\nOK  Test video written: {OUT_PATH}")
print(f"   Size: {OUT_PATH.stat().st_size / 1024 / 1024:.1f} MB")
