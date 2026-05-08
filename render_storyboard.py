"""
render_storyboard.py — Panorama to Storyboard Panels

Downloads the master campus panorama (equirectangular PNG) and crops
specific camera viewpoints for each shot, outputting PNG storyboard frames.

Runs fully on CPU — no GPU required.
Dependencies: pip install requests Pillow numpy

Usage:
    python render_storyboard.py                    # renders Scene 01 shots
    python render_storyboard.py --pano <url>       # override panorama URL
    python render_storyboard.py --out ./frames     # override output directory
"""

import os
import sys
import math
import argparse
import requests
import numpy as np
from pathlib import Path
from io import BytesIO
from PIL import Image
from dotenv import load_dotenv

load_dotenv()

MASTER_PANO_URL = os.environ.get("MASTER_PANO_URL")
OUTPUT_DIR = Path("storyboard_frames")

# ---------------------------------------------------------------------------
# Camera viewpoints for Scene 01 — "THE TREE"
#
# Each shot maps to a yaw/pitch angle into the equirectangular panorama:
#   yaw:   horizontal rotation in degrees (0 = forward, 90 = right, 180 = back)
#   pitch: vertical tilt in degrees (+90 = straight up, -90 = straight down)
#   fov:   field of view in degrees (lower = more zoomed in)
#
# WHO / WHERE / WHEN annotations kept for 5W1H consistency.
# ---------------------------------------------------------------------------

SHOTS = [
    {
        "id": "1A",
        "label": "Full Campus — The Entire World Revealed",
        "who": "None",
        "where": "East campus, full establishing view",
        "when": "Early morning",
        "yaw": 90,
        "pitch": 0,     # ground-level east: Gothic hall + clock tower + open sports field
        "fov": 100,
    },
    {
        "id": "1B",
        "label": "Courtyard Wide — Tree as Undeniable Center",
        "who": "The Tree",
        "where": "Central courtyard, ground level",
        "when": "Early morning",
        "yaw": 0,
        "pitch": 0,     # eye level: tree trunk, cobblestone base, colonnade behind
        "fov": 85,
    },
    {
        "id": "1C",
        "label": "Worm's Eye — The Monolith Reveal",
        "who": "The Tree",
        "where": "Under the tree",
        "when": "Early morning",
        "yaw": 0,
        "pitch": 25,    # looking up: spreading branches against sky, building edge
        "fov": 75,
    },
    {
        "id": "1D",
        "label": "Canopy Upshot — Natural Cathedral",
        "who": "The Tree",
        "where": "Under the tree",
        "when": "Mid-morning",
        "yaw": 0,
        "pitch": 45,    # steeply up through dense canopy, sky beyond
        "fov": 80,
    },
    {
        "id": "1E",
        "label": "Root Level — Nature Reclaiming Stone",
        "who": "The Tree",
        "where": "Courtyard, ground level",
        "when": "Early morning",
        "yaw": 0,
        "pitch": -15,   # slight down: cobblestones, tree base, roots
        "fov": 75,
    },
    {
        "id": "1F",
        "label": "Transition — Campus Full, Students Blind",
        "who": "Students (background)",
        "where": "Sports field, south campus",
        "when": "Mid-morning",
        "yaw": 180,
        "pitch": 0,     # eye level south: real sports field, brick + glass buildings
        "fov": 95,
    },
]


def download_panorama(url: str) -> Image.Image:
    print(f"Downloading panorama...")
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    img = Image.open(BytesIO(response.content)).convert("RGB")
    print(f"Panorama size: {img.width} x {img.height} px")
    return img


def crop_rectilinear(
    pano: Image.Image,
    yaw_deg: float,
    pitch_deg: float,
    fov_deg: float,
    out_width: int = 1920,
    out_height: int = 1080,
) -> Image.Image:
    """
    Extract a rectilinear (perspective) crop from an equirectangular panorama.

    Args:
        pano:       Equirectangular panorama image.
        yaw_deg:    Horizontal look direction in degrees (0 = front).
        pitch_deg:  Vertical look direction in degrees (+90 = up, -90 = down).
        fov_deg:    Horizontal field of view in degrees.
        out_width:  Output frame width in pixels.
        out_height: Output frame height in pixels.
    """
    pano_w, pano_h = pano.size
    pano_arr = np.array(pano, dtype=np.float32)

    yaw   = math.radians(yaw_deg)
    pitch = math.radians(-pitch_deg)  # negate: panorama Y-axis is inverted vs. convention
    fov   = math.radians(fov_deg)

    # Build grid of output pixel coordinates
    xs = np.linspace(-1, 1, out_width)
    ys = np.linspace(1, -1, out_height) * (out_height / out_width)
    xv, yv = np.meshgrid(xs, ys)

    # Focal length from fov
    f = 1.0 / math.tan(fov / 2)

    # Ray directions in camera space
    ray_x = xv
    ray_y = yv
    ray_z = np.full_like(xv, f)

    # Normalise
    norm = np.sqrt(ray_x**2 + ray_y**2 + ray_z**2)
    ray_x /= norm
    ray_y /= norm
    ray_z /= norm

    # Rotate by pitch (around X axis)
    cp, sp = math.cos(pitch), math.sin(pitch)
    ry = ray_y * cp - ray_z * sp
    rz = ray_y * sp + ray_z * cp
    ray_y, ray_z = ry, rz

    # Rotate by yaw (around Y axis)
    cy, sy = math.cos(yaw), math.sin(yaw)
    rx = ray_x * cy + ray_z * sy
    rz = -ray_x * sy + ray_z * cy
    ray_x, ray_z = rx, rz

    # Convert ray to equirectangular UV
    lon = np.arctan2(ray_x, ray_z)          # -pi to pi
    lat = np.arcsin(np.clip(ray_y, -1, 1))  # -pi/2 to pi/2

    u = (lon / (2 * math.pi) + 0.5) * pano_w
    v = (0.5 - lat / math.pi) * pano_h

    # Clamp and convert to int indices
    u = np.clip(u, 0, pano_w - 1).astype(np.int32)
    v = np.clip(v, 0, pano_h - 1).astype(np.int32)

    # Sample panorama
    out_arr = pano_arr[v, u].astype(np.uint8)
    return Image.fromarray(out_arr)


def render_shot(pano: Image.Image, shot: dict, out_dir: Path) -> Path:
    print(f"\n  Shot {shot['id']} — {shot['label']}")
    print(f"    WHO:   {shot['who']}")
    print(f"    WHERE: {shot['where']}")
    print(f"    WHEN:  {shot['when']}")
    print(f"    Camera: yaw={shot['yaw']}° pitch={shot['pitch']}° fov={shot['fov']}°")

    frame = crop_rectilinear(
        pano,
        yaw_deg=shot["yaw"],
        pitch_deg=shot["pitch"],
        fov_deg=shot["fov"],
    )

    out_path = out_dir / f"scene01_shot_{shot['id']}.png"
    frame.save(out_path)
    print(f"    Saved: {out_path}")
    return out_path


def main():
    parser = argparse.ArgumentParser(description="Render storyboard frames from panorama.")
    parser.add_argument("--pano", help="Panorama URL (overrides MASTER_PANO_URL in .env)")
    parser.add_argument("--out", help="Output directory", default=str(OUTPUT_DIR))
    args = parser.parse_args()

    pano_url = args.pano or MASTER_PANO_URL
    out_dir = Path(args.out)

    if not pano_url:
        print("ERROR: No panorama URL. Set MASTER_PANO_URL in .env or pass --pano <url>")
        sys.exit(1)

    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"\nTREE — Rendering Scene 01 Storyboard Frames")
    print(f"Output directory: {out_dir.resolve()}")

    pano = download_panorama(pano_url)

    saved = []
    for shot in SHOTS:
        path = render_shot(pano, shot, out_dir)
        saved.append(path)

    print(f"\n{'='*60}")
    print(f"  Done. {len(saved)} frames saved to: {out_dir.resolve()}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
