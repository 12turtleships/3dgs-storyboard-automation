#!/usr/bin/env python3
"""
Detect the ground plane from campus_v5_500k.ply using RANSAC.

Outputs Unity rotation for CampusSplat and eye-level Y for StoryboardCamera.
"""

import json
import numpy as np
from pathlib import Path

PLY_PATH = Path(__file__).parent / "campus_v5_500k.ply"


def read_ply_positions(path: Path, max_points: int = 100_000) -> np.ndarray:
    with open(path, "rb") as f:
        header_lines = []
        while True:
            line = f.readline().decode("ascii").strip()
            header_lines.append(line)
            if line == "end_header":
                break

        vertex_count = next(
            int(l.split()[-1]) for l in header_lines if l.startswith("element vertex")
        )
        stride = sum(1 for l in header_lines if l.startswith("property float"))
        print(f"PLY: {vertex_count:,} vertices, {stride} floats/vertex")

        data = np.frombuffer(f.read(vertex_count * stride * 4), dtype=np.float32)
        data = data.reshape(vertex_count, stride)

    positions = data[:, :3].copy()
    if vertex_count > max_points:
        idx = np.random.choice(vertex_count, max_points, replace=False)
        positions = positions[idx]
        print(f"Subsampled to {max_points:,} points")
    return positions


def ransac_plane(points, iterations=400, threshold=0.2):
    """Return (normal, d, inlier_mask) for the dominant plane."""
    best_mask  = None
    best_count = 0
    n = len(points)

    for _ in range(iterations):
        idx = np.random.choice(n, 3, replace=False)
        p0, p1, p2 = points[idx]
        v1 = p1 - p0
        v2 = p2 - p0
        normal = np.cross(v1, v2)
        norm = np.linalg.norm(normal)
        if norm < 1e-10:
            continue
        normal /= norm
        d = -np.dot(normal, p0)
        dist = np.abs(points @ normal + d)
        mask = dist < threshold
        count = mask.sum()
        if count > best_count:
            best_count = count
            best_mask  = mask
            best_normal = normal.copy()
            best_d      = d

    # Refine with inliers via SVD
    inliers   = points[best_mask]
    centroid  = inliers.mean(axis=0)
    _, _, Vt  = np.linalg.svd(inliers - centroid)
    normal    = Vt[-1]
    d         = -np.dot(normal, centroid)

    pct = best_count / n * 100
    print(f"RANSAC best: {best_count:,} inliers ({pct:.1f}%) threshold={threshold}")
    return normal, d, centroid, best_mask


def main():
    np.random.seed(42)

    print(f"Loading {PLY_PATH.name}…")
    pos = read_ply_positions(PLY_PATH)

    bbox_min = pos.min(axis=0)
    bbox_max = pos.max(axis=0)
    print(f"\nBBox  X [{bbox_min[0]:.2f}, {bbox_max[0]:.2f}]"
          f"  Y [{bbox_min[1]:.2f}, {bbox_max[1]:.2f}]"
          f"  Z [{bbox_min[2]:.2f}, {bbox_max[2]:.2f}]")

    # -------------------------------------------------------------------------
    # In our PLY (RDF, Y-down), from Three.js calibration we know:
    #   Three.js Y-up ground ≈ -30  →  RDF Y = +30  (Y_RDF = -Y_threejs)
    #   Three.js Y-up sky   ≈  0   →  RDF Y = 0
    # So ground layer is around Y = +20 to +40 in this PLY.
    # We filter to that band before RANSAC to avoid picking up the sky plane.
    # -------------------------------------------------------------------------
    y_range    = bbox_max[1] - bbox_min[1]       # total Y extent
    # Ground band: 30%–65% of Y range from the min (sky end)
    y_lo = bbox_min[1] + y_range * 0.30          # ≈ +19
    y_hi = bbox_min[1] + y_range * 0.65          # ≈ +42
    band = pos[(pos[:, 1] >= y_lo) & (pos[:, 1] <= y_hi)]
    print(f"\nGround search band  Y ∈ [{y_lo:.1f}, {y_hi:.1f}]  →  {len(band):,} points")

    if len(band) < 500:
        print("WARNING: sparse band — using full cloud")
        band = pos

    print("Running RANSAC…")
    normal, d, centroid, _ = ransac_plane(band, iterations=400, threshold=0.2)

    # Orient normal to point "up" (away from the bulk of the scene)
    scene_centre = pos.mean(axis=0)
    if np.dot(normal, scene_centre - centroid) > 0:
        normal = -normal
        d      = -d

    print(f"\nGround normal (PLY space): ({normal[0]:.4f}, {normal[1]:.4f}, {normal[2]:.4f})")
    print(f"Ground centroid:           ({centroid[0]:.2f}, {centroid[1]:.2f}, {centroid[2]:.2f})")

    # -------------------------------------------------------------------------
    # Unity rotation: rotate CampusSplat so ground normal → Unity Y+ (0,1,0)
    # We decompose into X and Z rotations (tilt corrections).
    # -------------------------------------------------------------------------
    unity_up  = np.array([0.0, 1.0, 0.0])
    cos_angle = float(np.clip(np.dot(normal, unity_up), -1, 1))
    tilt_deg  = np.degrees(np.arccos(cos_angle))

    # Rotation around X: tilt in the Y-Z plane
    rot_x = float(np.degrees(np.arctan2(-normal[2], normal[1])))
    # Rotation around Z: tilt in the X-Y plane
    rot_z = float(np.degrees(np.arctan2( normal[0], normal[1])))

    # Eye level = ground centroid + 1.7m along normal
    eye_offset   = 1.7
    eye_world    = centroid + normal * eye_offset
    ground_y_ply = float(centroid[1])

    # -------------------------------------------------------------------------
    print("\n" + "=" * 60)
    print("  RESULTS")
    print("=" * 60)
    print(f"\n  Ground tilt from horizontal: {tilt_deg:.2f}°")
    print(f"  Ground normal: ({normal[0]:.3f}, {normal[1]:.3f}, {normal[2]:.3f})")
    print(f"\n  [CampusSplat Transform Rotation]")
    print(f"    X = {rot_x:.1f}")
    print(f"    Y = 0   (rotate Y to face desired direction)")
    print(f"    Z = {rot_z:.1f}")
    print(f"\n  [Ground Y in PLY space]: {ground_y_ply:.2f}")
    print(f"  [Eye level world pos]:   ({eye_world[0]:.2f}, {eye_world[1]:.2f}, {eye_world[2]:.2f})")
    print(f"\n  [StoryboardCamera.cs] — set worldCenter to an empty")
    print(f"  GameObject placed at the ground centroid:")
    print(f"    Position: ({centroid[0]:.2f}, {centroid[1]:.2f}, {centroid[2]:.2f})")
    print(f"  Eye-level positionOffset.Y above that = {eye_offset}")
    print("=" * 60)

    result = {
        "ground_normal":    normal.tolist(),
        "ground_centroid":  centroid.tolist(),
        "tilt_deg":         tilt_deg,
        "campusSplat_rotation": {"x": rot_x, "y": 0, "z": rot_z},
        "eye_level_world":  eye_world.tolist(),
        "ground_y_ply":     ground_y_ply,
        "bbox_min":         bbox_min.tolist(),
        "bbox_max":         bbox_max.tolist(),
    }
    out = Path(__file__).parent / "ground_plane.json"
    out.write_text(json.dumps(result, indent=2))
    print(f"\nSaved: {out.name}")


if __name__ == "__main__":
    main()
