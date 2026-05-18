#!/usr/bin/env python3
"""
Convert a WorldLabs .spz Gaussian splat to standard 3DGS .ply for Unity import.

Usage:
    python3 spz_to_ply.py                        # downloads 500k splats
    python3 spz_to_ply.py --full-res             # downloads full-resolution splats
    python3 spz_to_ply.py path/to/file.spz       # convert local file

Output: campus_v5.ply  (in same directory as this script)

Unity import:
    1. Install Aras Pranckevičius's GS package (see README)
    2. Drag campus_v5.ply into Assets/
    3. Select the .ply → in Inspector click "Create Asset"
"""

import importlib.util
import struct
import sys
import os
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Direct load of the spz native extension (avoids circular import in __init__)
# ---------------------------------------------------------------------------
_SO_PATH = Path(__file__).parent
_so = None
for site in [
    "/Library/Frameworks/Python.framework/Versions/3.9/lib/python3.9/site-packages/spz/spz.cpython-39-darwin.so",
    "/Library/Frameworks/Python.framework/Versions/3.11/lib/python3.11/site-packages/spz/spz.cpython-311-darwin.so",
]:
    if Path(site).exists():
        spec = importlib.util.spec_from_file_location("spz", site)
        _so = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(_so)
        break

if _so is None:
    # Fallback: glob for any installed spz .so
    import glob
    hits = glob.glob("/Library/**/spz/spz.cpython-*.so", recursive=True)
    if hits:
        spec = importlib.util.spec_from_file_location("spz", hits[0])
        _so = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(_so)

if _so is None:
    sys.exit("ERROR: spz native module not found. Run: pip3 install spz")

GaussianSplat   = _so.GaussianSplat
CoordinateSystem = _so.CoordinateSystem

# ---------------------------------------------------------------------------
# WorldLabs CDN URLs
# ---------------------------------------------------------------------------
SPZ_500K    = "https://cdn.marble.worldlabs.ai/fcf05383-91d7-4880-8186-98899075f4a1/2da89a0f-f85d-4077-8a7a-0540631cb250_ceramic_500k.spz"
SPZ_FULLRES = "https://cdn.marble.worldlabs.ai/fcf05383-91d7-4880-8186-98899075f4a1/e508d48c-b710-44a2-a61a-b6427802474f_ceramic.spz"

SCRIPT_DIR = Path(__file__).parent
CACHE_DIR  = SCRIPT_DIR / ".spz_cache"
CACHE_DIR.mkdir(exist_ok=True)


def download_spz(url: str, label: str) -> Path:
    cache_file = CACHE_DIR / Path(url).name
    if cache_file.exists():
        print(f"Using cached {label}: {cache_file.name}  ({cache_file.stat().st_size / 1e6:.1f} MB)")
        return cache_file

    print(f"Downloading {label}…")
    tmp = cache_file.with_suffix(".tmp")

    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        total = int(r.headers.get("content-length", 0))
        received = 0
        with open(tmp, "wb") as f:
            for chunk in r.iter_content(chunk_size=1 << 17):
                f.write(chunk)
                received += len(chunk)
                mb = received / 1e6
                tot = f"{total / 1e6:.1f}" if total else "?"
                print(f"\r  {mb:.1f} / {tot} MB", end="", flush=True)
    print()
    tmp.rename(cache_file)
    print(f"Saved: {cache_file.name}  ({cache_file.stat().st_size / 1e6:.1f} MB)")
    return cache_file


def write_ply(splat: "GaussianSplat", output_path: Path) -> None:
    """Write a standard 3DGS binary PLY file from a GaussianSplat object."""
    import numpy as np

    N         = splat.num_points
    sh_degree = splat.sh_degree
    sh_dims   = {0: 0, 1: 3, 2: 8, 3: 15}
    sh_dim    = sh_dims.get(sh_degree, 0)   # AC SH coefficients per channel

    positions  = splat.positions   # (N, 3)  float32  x,y,z
    scales     = splat.scales      # (N, 3)  float32  log-scale
    rotations  = splat.rotations   # (N, 4)  float32  w,x,y,z
    alphas     = splat.alphas      # (N,)    float32  logit opacity
    colors     = splat.colors      # (N, 3)  float32  SH0 r,g,b

    # Property list (standard 3DGS PLY schema)
    props = ["x", "y", "z", "nx", "ny", "nz", "f_dc_0", "f_dc_1", "f_dc_2"]
    n_rest = sh_dim * 3
    for i in range(n_rest):
        props.append(f"f_rest_{i}")
    props += ["opacity", "scale_0", "scale_1", "scale_2", "rot_0", "rot_1", "rot_2", "rot_3"]

    # PLY header
    header_lines = [
        "ply",
        "format binary_little_endian 1.0",
        f"element vertex {N}",
    ]
    for p in props:
        header_lines.append(f"property float {p}")
    header_lines.append("end_header")
    header = "\n".join(header_lines) + "\n"

    normals = np.zeros((N, 3), dtype=np.float32)

    # Assemble data columns
    parts = [positions, normals, colors]

    if n_rest > 0 and splat.spherical_harmonics is not None:
        sh_raw = splat.spherical_harmonics  # (N, sh_dim * 3)
        # spz stores SH as interleaved [r0,g0,b0, r1,g1,b1, ...]
        # PLY wants grouped [r0,r1,..., g0,g1,..., b0,b1,...]
        sh_rgb = sh_raw.reshape(N, sh_dim, 3)       # (N, sh_dim, 3)
        sh_ply = sh_rgb.transpose(0, 2, 1).reshape(N, sh_dim * 3).astype(np.float32)
        parts.append(sh_ply)

    parts += [
        alphas.reshape(N, 1),
        scales,
        rotations,
    ]

    data = np.concatenate(parts, axis=1).astype(np.float32)

    print(f"\nWriting PLY — {N:,} gaussians, SH degree {sh_degree} ({n_rest} AC coeffs per point)")
    with open(output_path, "wb") as f:
        f.write(header.encode("ascii"))
        f.write(data.tobytes())

    size_mb = output_path.stat().st_size / 1e6
    print(f"Output: {output_path}  ({size_mb:.1f} MB)")

    bbox = splat.bbox
    print(f"BBox centre: {bbox.center}")
    print(f"BBox size:   {bbox.size}")


def main():
    import numpy as np

    full_res   = "--full-res" in sys.argv or "--fullres" in sys.argv
    local_file = next((a for a in sys.argv[1:] if not a.startswith("--")), None)

    if local_file:
        spz_path = Path(local_file)
        if not spz_path.exists():
            sys.exit(f"ERROR: file not found: {spz_path}")
        print(f"Loading local SPZ: {spz_path}")
    else:
        url   = SPZ_FULLRES if full_res else SPZ_500K
        label = "full-res" if full_res else "500k"
        spz_path = download_spz(url, label)

    print(f"\nLoading SPZ (converting to PLY coordinate system)…")
    # RDF = Right, Down, Front — the standard 3DGS / PLY coordinate system
    splat = GaussianSplat.load(str(spz_path), CoordinateSystem.RDF)
    print(f"Loaded {splat.num_points:,} gaussians, SH degree {splat.sh_degree}")

    suffix = "_fullres" if full_res else "_500k"
    out = SCRIPT_DIR / f"campus_v5{suffix}.ply"
    write_ply(splat, out)
    print("\nDone. Import campus_v5*.ply into Unity via the Gaussian Splatting package.")


if __name__ == "__main__":
    main()
