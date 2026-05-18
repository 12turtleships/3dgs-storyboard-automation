#!/usr/bin/env python3
"""
scene_analysis.py — detect the tree and buildings in campus_v5_500k.ply.

Two-pass strategy:
  Pass 1 — COLOR: convert SH0 (f_dc) → linear RGB, isolate green/brown
            vegetation, cluster those → main tree.
  Pass 2 — SPATIAL: DBSCAN the full solid point cloud at smaller eps to
            find remaining objects (buildings, walls).

Output: scene_layout.json

Dependencies: pip install numpy scikit-learn
"""

import json
import numpy as np
from pathlib import Path

try:
    from sklearn.cluster import DBSCAN
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False
    print("WARNING: scikit-learn not found — run: pip install scikit-learn\n")

PLY_PATH    = Path(__file__).parent / "campus_v5_500k.ply"
GROUND_JSON = Path(__file__).parent / "ground_plane.json"
OUT_PATH    = Path(__file__).parent / "scene_layout.json"

# Standard 3DGS SH-degree-0 PLY column layout (from spz_to_ply.py)
# x y z  nx ny nz  f_dc_0 f_dc_1 f_dc_2  opacity  scale_0 scale_1 scale_2  rot×4
COL_X, COL_Y, COL_Z = 0, 1, 2
COL_DC_R, COL_DC_G, COL_DC_B = 6, 7, 8
COL_OPACITY = 9
COL_SCALE   = slice(10, 13)

SH_C0 = 0.28209479177387814   # 1/sqrt(4π) — converts SH0 coeff to linear radiance


def sigmoid(x):
    return 1.0 / (1.0 + np.exp(-np.clip(x.astype(np.float64), -20, 20)))


def load_ply(path):
    with open(path, "rb") as f:
        props, n = [], 0
        while True:
            line = f.readline().decode("ascii", errors="replace").strip()
            if line.startswith("element vertex"):
                n = int(line.split()[-1])
            elif line.startswith("property float"):
                props.append(line.split()[-1])
            elif line == "end_header":
                break
        stride = len(props)
        data = np.frombuffer(f.read(n * stride * 4), dtype=np.float32).reshape(n, stride)
    return data, props


def sh0_to_rgb(dc_r, dc_g, dc_b):
    """Convert SH0 (f_dc) coefficients to linear RGB in [0, 1]."""
    r = np.clip(0.5 + SH_C0 * dc_r.astype(np.float64), 0.0, 1.0)
    g = np.clip(0.5 + SH_C0 * dc_g.astype(np.float64), 0.0, 1.0)
    b = np.clip(0.5 + SH_C0 * dc_b.astype(np.float64), 0.0, 1.0)
    return r, g, b


def cluster_stats(pts, label="cluster"):
    c    = pts.mean(axis=0)
    bmin = pts.min(axis=0)
    bmax = pts.max(axis=0)
    ext  = bmax - bmin
    foot = max(ext[0], ext[2])
    asp  = ext[1] / max(foot, 0.01)
    print(f"  {label}: n={len(pts):,}  ctr=({c[0]:.2f},{c[1]:.2f},{c[2]:.2f})"
          f"  ext=({ext[0]:.1f},{ext[1]:.1f},{ext[2]:.1f})  aspect={asp:.2f}")
    return c, bmin, bmax, ext, asp


def main():
    np.random.seed(42)

    # ── Load ──────────────────────────────────────────────────────────────────
    print(f"Loading {PLY_PATH.name}…")
    data, props = load_ply(PLY_PATH)
    n = len(data)
    pos = data[:, COL_X:COL_Z+1]
    print(f"  {n:,} Gaussians | props: {props}")

    bmin = pos.min(axis=0)
    bmax = pos.max(axis=0)
    scene_w = (bmax - bmin).max()
    print(f"\nBBox  X[{bmin[0]:.1f},{bmax[0]:.1f}]"
          f"  Y[{bmin[1]:.1f},{bmax[1]:.1f}]"
          f"  Z[{bmin[2]:.1f},{bmax[2]:.1f}]  (width={scene_w:.1f})")

    # ── Ground info ───────────────────────────────────────────────────────────
    if GROUND_JSON.exists():
        gp = json.loads(GROUND_JSON.read_text())
        ground_y   = float(gp["ground_y_ply"])
        capture_pos = [5.6, 0.0, 9.8]
    else:
        ground_y    = bmin[1] + (bmax[1] - bmin[1]) * 0.35
        capture_pos = [(bmin[0]+bmax[0])/2, 0.0, (bmin[2]+bmax[2])/2]
    print(f"Ground Y (PLY): {ground_y:.2f}")

    # ── Convert SH0 → linear RGB ──────────────────────────────────────────────
    r, g, b = sh0_to_rgb(data[:, COL_DC_R], data[:, COL_DC_G], data[:, COL_DC_B])

    # ── Colour diagnostics ────────────────────────────────────────────────────
    print(f"\nColour stats (linear RGB after SH0 conversion):")
    print(f"  R: min={r.min():.3f}  max={r.max():.3f}  mean={r.mean():.3f}")
    print(f"  G: min={g.min():.3f}  max={g.max():.3f}  mean={g.mean():.3f}")
    print(f"  B: min={b.min():.3f}  max={b.max():.3f}  mean={b.mean():.3f}")

    dominant_g  = (g > r) & (g > b)
    dominant_r  = (r > g) & (r > b)
    dominant_b  = (b > r) & (b > g)
    print(f"  G dominant: {dominant_g.sum():,}  R dominant: {dominant_r.sum():,}"
          f"  B dominant: {dominant_b.sum():,}")

    # ── Vegetation (green / brownish-green) mask ──────────────────────────────
    # Green foliage: G channel is the strongest
    green_mask  = dominant_g & (g > 0.25)

    # Brown bark/trunk: reddish-warm with G > B (not blue-dominated)
    brown_mask  = (r >= g * 0.85) & (g > b * 1.1) & (r > 0.15) & (r < 0.75)

    veg_mask    = green_mask | brown_mask
    print(f"\nVegetation mask: {veg_mask.sum():,} / {n:,}  ({100*veg_mask.mean():.1f}%)")
    print(f"  Green: {green_mask.sum():,}   Brown: {brown_mask.sum():,}")

    # ── Opacity filter ────────────────────────────────────────────────────────
    opa   = sigmoid(data[:, COL_OPACITY])
    o_msk = opa > 0.15
    print(f"\nOpacity > 0.15: {o_msk.sum():,} ({100*o_msk.mean():.1f}%)")

    # ── Object-band filter (between sky and ground) ───────────────────────────
    band_msk = (pos[:, 1] >= bmin[1] - 1.0) & (pos[:, 1] <= ground_y + 1.0)

    # ── PASS 1 — colour-based tree detection ──────────────────────────────────
    print("\n" + "="*60)
    print("PASS 1 — Colour-based vegetation clustering")
    print("="*60)

    main_tree = None
    if HAS_SKLEARN:
        veg_pts = pos[veg_mask & o_msk & band_msk]
        print(f"Vegetation points in band: {len(veg_pts):,}")

        if len(veg_pts) >= 200:
            # Subsample
            MAX_V = 40_000
            if len(veg_pts) > MAX_V:
                idx     = np.random.choice(len(veg_pts), MAX_V, replace=False)
                veg_sub = veg_pts[idx]
            else:
                veg_sub = veg_pts

            # Try progressively smaller eps to find distinct tree cluster
            for eps_v in [0.8, 1.2, 1.8, 2.5]:
                db     = DBSCAN(eps=eps_v, min_samples=20, n_jobs=-1).fit(veg_sub)
                labels = db.labels_
                unique = sorted(set(labels) - {-1})
                n_clust = len(unique)
                print(f"  eps={eps_v:.1f} → {n_clust} clusters  "
                      f"(noise={( labels==-1).sum():,})")
                if n_clust >= 1:
                    # Pick the cluster with the greatest vertical (Y) extent
                    best, best_dy = None, 0
                    for lbl in unique:
                        pts = veg_sub[labels == lbl]
                        dy  = pts[:, 1].max() - pts[:, 1].min()
                        if dy > best_dy:
                            best_dy = dy
                            best    = (lbl, pts)
                    if best:
                        lbl, tree_pts = best
                        c, tbmin, tbmax, ext, asp = cluster_stats(tree_pts, f"tree (eps={eps_v})")
                        main_tree = {
                            "id"          : "tree_0",
                            "type"        : "tree",
                            "n_points"    : int(len(tree_pts)),
                            "centroid"    : [round(float(c[i]),3) for i in range(3)],
                            "bbox_min"    : [round(float(tbmin[i]),3) for i in range(3)],
                            "bbox_max"    : [round(float(tbmax[i]),3) for i in range(3)],
                            "extent_xyz"  : [round(float(ext[i]),3) for i in range(3)],
                            "footprint_r" : round(float(max(ext[0],ext[2])/2),3),
                            "aspect_ratio": round(float(asp),3),
                            "detection"   : f"colour+eps={eps_v}",
                        }
                        break   # accept first result that finds something
        else:
            print("  Too few vegetation points — skipping colour pass")

    if main_tree:
        c = main_tree["centroid"]
        print(f"\n✓ Tree found via colour: centroid ({c[0]:.2f},{c[1]:.2f},{c[2]:.2f})")
    else:
        print("\n✗ Colour pass did not isolate a tree cluster")

    # ── PASS 2 — spatial clustering (all solid points, small eps) ────────────
    print("\n" + "="*60)
    print("PASS 2 — Spatial clustering (all solid points)")
    print("="*60)

    solid_pts = pos[o_msk & band_msk]
    print(f"Solid points in band: {len(solid_pts):,}")

    MAX_S = 60_000
    if len(solid_pts) > MAX_S:
        idx = np.random.choice(len(solid_pts), MAX_S, replace=False)
        sub = solid_pts[idx]
    else:
        sub = solid_pts

    objects = []
    if HAS_SKLEARN:
        for eps_s in [0.5, 0.8, 1.2, 1.8]:
            db     = DBSCAN(eps=eps_s, min_samples=30, n_jobs=-1).fit(sub)
            labels = db.labels_
            unique = sorted(set(labels) - {-1})
            noise  = (labels == -1).sum()
            print(f"\n  eps={eps_s:.1f} → {len(unique)} clusters  noise={noise:,}")
            for lbl in unique:
                pts = sub[labels == lbl]
                c, lbmin, lbmax, ext, asp = cluster_stats(pts, f"  cluster_{lbl}")
            if len(unique) >= 2:
                # Enough clusters — use this eps
                for lbl in unique:
                    pts = sub[labels == lbl]
                    if len(pts) < 30:
                        continue
                    c, lbmin, lbmax, ext, asp = pts.mean(0), pts.min(0), pts.max(0), pts.max(0)-pts.min(0), 0
                    foot = max(float(ext[0]), float(ext[2]))
                    asp  = float(ext[1]) / max(foot, 0.01)
                    kind = "tree" if asp > 1.2 and foot < scene_w*0.25 else "building"
                    if main_tree and kind == "tree":
                        kind = "building"   # tree already found via colour
                    objects.append({
                        "id"          : f"{kind}_{lbl}",
                        "type"        : kind,
                        "n_points"    : int(len(pts)),
                        "centroid"    : [round(float(c[i]),3) for i in range(3)],
                        "bbox_min"    : [round(float(lbmin[i]),3) for i in range(3)],
                        "bbox_max"    : [round(float(lbmax[i]),3) for i in range(3)],
                        "extent_xyz"  : [round(float(ext[i]),3) for i in range(3)],
                        "footprint_r" : round(float(foot/2),3),
                        "aspect_ratio": round(float(asp),3),
                    })
                break

    objects.sort(key=lambda o: o["n_points"], reverse=True)

    # ── Summary ───────────────────────────────────────────────────────────────
    if main_tree:
        objects.insert(0, main_tree)

    print("\n" + "="*60)
    print("  FINAL OBJECT LIST")
    print("="*60)
    for o in objects:
        c = o["centroid"]
        print(f"  [{o['type']:8s}] {o['id']:<14}  n={o['n_points']:6,}"
              f"  ctr=({c[0]:.2f},{c[1]:.2f},{c[2]:.2f})"
              f"  aspect={o['aspect_ratio']:.2f}")

    if not any(o["type"] == "tree" for o in objects):
        print("\n  ⚠  No tree detected. Will fall back to nearest cluster as main subject.")
        if objects:
            objects[0]["type"] = "tree"
            objects[0]["id"]   = "tree_0"

    tree_obj = next((o for o in objects if o["type"] == "tree"), None)
    if tree_obj:
        c  = tree_obj["centroid"]
        ex = tree_obj["extent_xyz"]
        print(f"\n  Main subject: centroid ({c[0]:.2f},{c[1]:.2f},{c[2]:.2f})"
              f"  extent Y={ex[1]:.2f} (PLY units)")

    # ── Save ──────────────────────────────────────────────────────────────────
    result = {
        "capture_position_ply" : capture_pos,
        "ground_y_ply"         : float(ground_y),
        "sky_y_ply"            : float(bmin[1]),
        "bbox"                 : {
            "min": [round(float(v),3) for v in bmin],
            "max": [round(float(v),3) for v in bmax],
        },
        "objects"  : objects,
        "main_tree": tree_obj,
    }
    OUT_PATH.write_text(json.dumps(result, indent=2))
    print(f"\nSaved → {OUT_PATH.name}")


if __name__ == "__main__":
    main()
