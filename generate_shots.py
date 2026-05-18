#!/usr/bin/env python3
"""
generate_shots.py — read scene_layout.json, output auto_shots.json.

For each shot the output contains a rotation OFFSET (degrees) from the
camera's eye-level-horizontal baseline:

  rotation_offset[0] = X rotation (Unity convention: + = tilt down toward ground,
                                                      - = tilt up toward canopy/sky)
  rotation_offset[1] = Y rotation (yaw: + = right, - = left)
  rotation_offset[2] = Z rotation (roll, always 0)
  fov_offset          = degrees added to the Edit-mode camera FOV

The Unity StoryboardCamera.cs applies these at runtime via:
    transform.rotation = Quaternion.Euler(_baseEuler) * Quaternion.Euler(rotation_offset)
    camera.fieldOfView = _baseFov + fov_offset

PLY coordinate convention used here (RDF, Y-down):
  - Y = 0        : eye level (original capture height)
  - Y = ground_y : ground surface (positive, below camera)
  - Y < 0        : above camera (sky / canopy)
  - PLY-space tilt angle = atan2(target_Y - cam_Y, horizontal_dist)
    → positive = looking toward ground  → Unity X rotation positive ✓
    → negative = looking toward sky     → Unity X rotation negative ✓

Dependencies: json, math (stdlib only)
"""

import json
import math
from pathlib import Path

SCENE_JSON = Path(__file__).parent / "scene_layout.json"
OUT_JSON   = Path(__file__).parent / "auto_shots.json"
UNITY_STREAMING = Path(__file__).parent.parent / "tree-unity" / "Assets" / "StreamingAssets"


def tilt_deg(cam_y: float, target_y: float, horiz_dist: float) -> float:
    """
    Vertical tilt angle in PLY space from camera to target.
    Positive = target is deeper (more ground-ward) → Unity X+ (look down).
    Negative = target is shallower (more sky-ward)  → Unity X- (look up).
    """
    dy = target_y - cam_y
    return math.degrees(math.atan2(dy, max(horiz_dist, 0.1)))


def horiz_dist(cam: list, target: list) -> float:
    """Horizontal (XZ-plane) distance between two PLY positions."""
    return math.sqrt((target[0]-cam[0])**2 + (target[2]-cam[2])**2)


def main() -> None:
    if not SCENE_JSON.exists():
        print(f"ERROR: {SCENE_JSON} not found. Run scene_analysis.py first.")
        return

    scene  = json.loads(SCENE_JSON.read_text())
    cam    = scene["capture_position_ply"]        # [x, 0, z]  at eye level
    gnd_y  = scene["ground_y_ply"]
    sky_y  = scene["sky_y_ply"]
    tree   = scene.get("main_tree")

    print(f"Capture position (PLY): {cam}")
    print(f"Ground Y: {gnd_y:.2f}   Sky Y: {sky_y:.2f}")

    if tree is None:
        print("\nWARNING: no tree in scene_layout.json — using scene centre as subject")
        bbox   = scene["bbox"]
        centre = [(bbox["min"][i]+bbox["max"][i])/2 for i in range(3)]
        tree   = {
            "centroid"   : centre,
            "bbox_min"   : bbox["min"],
            "bbox_max"   : bbox["max"],
            "extent_xyz" : [bbox["max"][i]-bbox["min"][i] for i in range(3)],
        }

    tc   = tree["centroid"]          # tree centroid in PLY
    t_bmin = tree["bbox_min"]
    t_bmax = tree["bbox_max"]

    # Tree top = minimum PLY Y in cluster (closest to sky)
    # Tree base = maximum PLY Y in cluster (closest to ground)
    tree_top_y  = t_bmin[1]   # smallest Y = highest real-world point
    tree_base_y = t_bmax[1]   # largest Y  = lowest real-world point (roots)

    h_dist = horiz_dist(cam, tc)
    print(f"\nTree centroid (PLY): ({tc[0]:.2f}, {tc[1]:.2f}, {tc[2]:.2f})")
    print(f"Tree top Y: {tree_top_y:.2f}   base Y: {tree_base_y:.2f}")
    print(f"Horizontal dist camera→tree: {h_dist:.2f}")

    # ── Compute tilt angles ───────────────────────────────────────────────────
    tilt_centroid = tilt_deg(cam[1], tc[1],       h_dist)
    tilt_canopy   = tilt_deg(cam[1], tree_top_y,  h_dist)
    tilt_roots    = tilt_deg(cam[1], tree_base_y, h_dist)
    tilt_ground   = tilt_deg(cam[1], gnd_y,       h_dist)

    # Clamp extreme tilts so we stay in the well-captured PLY region (≈±45°)
    tilt_canopy   = max(tilt_canopy,  -40.0)
    tilt_roots    = min(tilt_roots,    40.0)

    print(f"\nComputed tilts (Unity X rotation offsets):")
    print(f"  Centroid : {tilt_centroid:+.1f}°")
    print(f"  Canopy   : {tilt_canopy:+.1f}°")
    print(f"  Roots    : {tilt_roots:+.1f}°")
    print(f"  Ground   : {tilt_ground:+.1f}°")

    # ── Define shots ──────────────────────────────────────────────────────────
    shots = [
        {
            "id"               : "1A",
            "label"            : "Campus Wide — Establishing",
            "rotation_offset"  : [round(tilt_centroid, 1), 0, 0],
            "fov_offset"       : 25,
            "transitionDuration": 2.0,
        },
        {
            "id"               : "1B",
            "label"            : "Courtyard — Tree as Center",
            "rotation_offset"  : [round(tilt_centroid, 1), 0, 0],
            "fov_offset"       : 0,
            "transitionDuration": 1.5,
        },
        {
            "id"               : "1C",
            "label"            : "Canopy — Looking Up",
            "rotation_offset"  : [round(tilt_canopy, 1), 0, 0],
            "fov_offset"       : -10,
            "transitionDuration": 1.5,
        },
        {
            "id"               : "1D",
            "label"            : "Roots — Looking Down",
            "rotation_offset"  : [round(tilt_roots, 1), 0, 0],
            "fov_offset"       : -10,
            "transitionDuration": 1.5,
        },
        {
            "id"               : "1E",
            "label"            : "Campus Right — Pan 90°",
            "rotation_offset"  : [round(tilt_centroid, 1), 90, 0],
            "fov_offset"       : 0,
            "transitionDuration": 2.0,
        },
        {
            "id"               : "1F",
            "label"            : "Campus Left — Pan 90°",
            "rotation_offset"  : [round(tilt_centroid, 1), -90, 0],
            "fov_offset"       : 0,
            "transitionDuration": 2.0,
        },
    ]

    # ── Print summary ─────────────────────────────────────────────────────────
    print("\n" + "="*60)
    print("  GENERATED SHOTS")
    print("="*60)
    for s in shots:
        r = s["rotation_offset"]
        print(f"  {s['id']}  rot=({r[0]:+.1f}°, {r[1]:+.1f}°, {r[2]:+.1f}°)"
              f"  fov_offset={s['fov_offset']:+d}°  — {s['label']}")

    # ── Save JSON ─────────────────────────────────────────────────────────────
    OUT_JSON.write_text(json.dumps(shots, indent=2))
    print(f"\nSaved → {OUT_JSON.name}")

    # Copy to Unity StreamingAssets if the folder exists
    if UNITY_STREAMING.exists():
        dest = UNITY_STREAMING / "auto_shots.json"
        dest.write_text(json.dumps(shots, indent=2))
        print(f"Copied → {dest}")
    else:
        UNITY_STREAMING.mkdir(parents=True, exist_ok=True)
        dest = UNITY_STREAMING / "auto_shots.json"
        dest.write_text(json.dumps(shots, indent=2))
        print(f"Created StreamingAssets and copied → {dest}")


if __name__ == "__main__":
    main()
