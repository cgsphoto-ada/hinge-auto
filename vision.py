"""Image-based detection for UI elements whose position varies per profile.

All pixel-size constants are defined for a 1080px-wide screen and scaled
at import time to match config.SCREEN_WIDTH so detection works on any
device (emulator, real phone, different resolutions).
"""

import io

import config

import numpy as np
from PIL import Image
from scipy.ndimage import label, find_objects


# Scale factor: resolution-independent constants are defined for 1080px
# (Pixel 10 reference width) and scaled at import time.
_S = config.SCREEN_WIDTH / 1080.0


def _png_to_array(png: bytes) -> np.ndarray:
    return np.array(Image.open(io.BytesIO(png)).convert("RGB"))


def find_send_like(png: bytes) -> tuple[int, int] | None:
    """Locate the 'Send Like' button. Returns (x, y) center or None.

    Hinge changed the compose card button in late June 2026 — replaced
    the filled peach button with a white button + pink 'Send Like' text
    (RGB ~255, 159, 191). As of early July 2026 the button is back to
    a filled warm peach color (RGB ~238, 225, 219). This finds the
    peach blob and returns its centroid as a proxy for the button
    position.
    """
    arr = _png_to_array(png)
    r, g, b = arr[..., 0], arr[..., 1], arr[..., 2]
    # Peach filled button: r ~238, g ~225, b ~219. r > g > b, light/muted.
    peach = (
        (r > 225) & (r < 250)
        & (g > 210) & (g < 240)
        & (b > 205) & (b < 230)
        & (r > g) & (g > b)
    )
    labeled, num = label(peach)
    candidates = []
    for i in range(1, num + 1):
        sl = find_objects((labeled == i).astype(np.int32))
        if sl is None or sl[0] is None:
            continue
        y0, y1 = sl[0][0].start, sl[0][0].stop
        x0, x1 = sl[0][1].start, sl[0][1].stop
        h, w = y1 - y0, x1 - x0
        area = ((labeled == i).astype(np.int32))[sl[0]].sum()
        # Button is larger than text; use button-sized filter.
        if not (h > 30 and area > 500):
            continue
        cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
        # Button is in the right half of the compose card.
        if cx < int(500 * _S):
            continue
        candidates.append((cy, cx))
    if not candidates:
        return None
    candidates.sort()
    cy, cx = candidates[0]
    return (cx, cy)


def _heart_icon_white_ratio(arr: np.ndarray, x0: int, y0: int, x1: int, y1: int) -> float:
    """Fraction of white pixels inside the blob's bounding box.

    The heart button has a white heart icon cutout inside the dark circle.
    A solid dark blob (clothing, shadow) has near-zero white interior;
    the real button has ~30-50% white pixels from the heart icon.
    """
    patch = arr[y0:y1, x0:x1]
    if patch.size == 0:
        return 0.0
    white = (patch[..., 0] > 180) & (patch[..., 1] > 180) & (patch[..., 2] > 180)
    return white.sum() / patch[..., 0].size


def _heart_button_score(arr: np.ndarray, cx: int, cy: int) -> float | None:
    """Score a candidate heart button at (cx, cy).

    Returns a 0-1 score or None if the candidate fails basic checks.
    The heart button is a dark circle (~25px diameter) with a white
    heart icon inside. We check:
      - Dark ring at the boundary
      - White interior (the heart icon cutout)
      - Moderate dark-fill ratio (~0.50-0.85 for icon cutout)
    """
    scr_h, scr_w = arr.shape[:2]
    radius = int(13 * _S)  # button radius in pixels
    margin = 2
    x0 = max(0, cx - radius - margin)
    x1 = min(scr_w, cx + radius + margin + 1)
    y0 = max(0, cy - radius - margin)
    y1 = min(scr_h, cy + radius + margin + 1)

    patch = arr[y0:y1, x0:x1]
    if patch.shape[0] < 10 or patch.shape[1] < 10:
        return None

    # Create a circular mask for the interior (slightly smaller than radius)
    py, px = patch.shape[:2]
    cy_p, cx_p = py // 2, px // 2
    yy, xx = np.ogrid[:py, :px]
    dist = np.sqrt((yy - cy_p) ** 2 + (xx - cx_p) ** 2)
    inner_mask = dist <= (radius - 3) * 0.9
    ring_mask = (dist >= radius * 0.7) & (dist <= radius * 1.1)

    dark = (patch[..., 0] < 60) & (patch[..., 1] < 60) & (patch[..., 2] < 60)
    white = (patch[..., 0] > 180) & (patch[..., 1] > 180) & (patch[..., 2] > 180)

    # Dark ring: should have high dark-pixel density
    ring_pixels = ring_mask.sum()
    if ring_pixels < 10:
        return None
    ring_dark = (dark & ring_mask).sum() / ring_pixels
    if ring_dark < 0.30:
        return None

    # White interior: the heart icon is white
    inner_pixels = inner_mask.sum()
    if inner_pixels < 5:
        return None
    inner_white = (white & inner_mask).sum() / inner_pixels
    if inner_white < 0.20:
        return None

    # Overall dark fill in the whole window (not just inner/ring)
    total_dark = dark.sum() / patch[..., 0].size
    if not (0.15 < total_dark < 0.75):
        return None

    # Score: combine ring darkness + interior whiteness
    return ring_dark * 0.6 + inner_white * 0.4


def find_first_heart(png: bytes) -> tuple[int, int] | None:
    """Locate the heart icon on photo 1 (topmost heart in current view).

    Three-tier detection (tried in order):
      1. Quick 5x5 kernel check at the calibrated static coordinate.
      2. Scanning-window search around the static coord (±80px). Scores
         each candidate by dark-ring + white-interior pattern. Immune to
         blob-merging issues that plague connected-component approaches.
      3. Lenient connected-component blob search as last-resort fallback.
    """
    arr = _png_to_array(png)
    scr_h, scr_w = arr.shape[:2]
    r, g, b = arr[..., 0], arr[..., 1], arr[..., 2]

    # ---- 1. Quick static-coord check ----
    sx, sy = config.COORDS["heart_photo_1"]
    if 2 <= sy < scr_h - 2 and 2 <= sx < scr_w - 2:
        r_patch = r[sy-2:sy+3, sx-2:sx+3]
        g_patch = g[sy-2:sy+3, sx-2:sx+3]
        b_patch = b[sy-2:sy+3, sx-2:sx+3]
        dark_patch = (r_patch < 60) & (g_patch < 60) & (b_patch < 60)
        if dark_patch.sum() >= 15:
            return (sx, sy)

    # ---- 2. Scanning-window search across right half of screen ----
    # The heart button is always on the right side but its Y varies per
    # profile (depends on photo size, text length, etc.). Scan a narrow X
    # band (rightmost 18%) across the full profile area.
    step = max(int(5 * _S), 3)
    x_start = int(scr_w * 0.78)
    x_end = int(scr_w * 0.96)
    y_start = int(scr_h * 0.25)
    y_end = int(scr_h * 0.88)
    best_score = 0.0
    best_xy = None
    for cy in range(y_start, y_end, step):
        for cx in range(x_start, x_end, step):
            score = _heart_button_score(arr, cx, cy)
            if score is not None and score > best_score:
                best_score = score
                best_xy = (cx, cy)

    if best_xy is not None and best_score > 0.40:
        print(f"  Heart vision: scan hit at {best_xy} score={best_score:.2f}")
        return best_xy

    # ---- 3. Connected-component blob search (lenient fallback) ----
    dark = (r < 60) & (g < 60) & (b < 60)
    labeled, _ = label(dark)
    hearts = []
    for i, sl in enumerate(find_objects(labeled), 1):
        if sl is None:
            continue
        y0, y1 = sl[0].start, sl[0].stop
        x0, x1 = sl[1].start, sl[1].stop
        blob_h, blob_w = y1 - y0, x1 - x0
        area = (labeled[sl] == i).sum()
        cx = (x0 + x1) // 2
        cy = (y0 + y1) // 2

        if blob_w < int(15 * _S) or blob_h < int(15 * _S):
            continue
        if cx <= int(scr_w * 0.50):
            continue
        frac_y = cy / scr_h
        if not (0.25 < frac_y < 0.92):
            continue

        aspect = blob_w / max(blob_h, 1)
        if not (0.40 < aspect < 2.50):
            continue

        fill = area / (blob_w * blob_h)
        if fill < 0.40:
            continue

        if not (int(200 * _S * _S) < area < int(5000 * _S * _S)):
            continue

        white_ratio = _heart_icon_white_ratio(arr, x0, y0, x1, y1)
        if white_ratio < 0.05:
            continue

        hearts.append((cy, cx, white_ratio))

    if hearts:
        hearts.sort(key=lambda h: -h[2])
        cy, cx, wr = hearts[0]
        print(f"  Heart vision: blob fallback at ({cx},{cy}) white_ratio={wr:.2f}")
        return (cx, cy)

    return None


def comment_field_text_pixels(png: bytes, send_like_xy: tuple[int, int]) -> int:
    """Count dark (text) pixels in the comment input area above Send Like."""
    arr = _png_to_array(png)
    sx, sy = send_like_xy
    y0 = max(0, sy - int(230 * _S))
    y1 = max(0, sy - int(60 * _S))
    x0 = max(0, sx - int(350 * _S))
    x1 = min(arr.shape[1], sx + int(350 * _S))
    region = arr[y0:y1, x0:x1]
    if region.size == 0:
        return 0
    dark = (region.max(axis=-1) < 130).sum()
    return int(dark)


def find_comment_input(send_like_xy: tuple[int, int]) -> tuple[int, int]:
    """Comment input sits at a fixed offset above the Send Like button."""
    _, send_y = send_like_xy
    return (int(540 * _S), send_y - int(171 * _S))
