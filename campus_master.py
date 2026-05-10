import os
import time
import requests
from pathlib import Path
from typing import Dict, Optional
from dotenv import load_dotenv

from story_plot import WHEN

load_dotenv()

API_KEY = os.environ.get("WLT_API_KEY", "YOUR_API_KEY_HERE")
BASE_URL = "https://api.worldlabs.ai/marble/v1"
HEADERS = {
    "Content-Type": "application/json",
    "WLT-Api-Key": API_KEY
}

# ---------------------------------------------------------------------------
# MASTER CAMPUS WORLD — Run this first before any scene script.
#
# WHO:  No characters — establishing the world only.
# WHERE: All five campus locations present in one unified world.
# WHEN:  Bright summer midday — neutral light suitable as a spatial anchor.
# WHAT:  A university campus centered on a monolithic ancient oak tree.
# WHY:   Single spatial source of truth; all 19 scenes reference this world.
# HOW:   Text-only generation; NO concept image — image anchors to close-up
#        scale and produces a small courtyard diorama. Text-only allows the
#        model to generate at full campus scale.
#
# After running: copy MASTER_WORLD_ID and MASTER_PANO_URL into .env
# ---------------------------------------------------------------------------

MASTER_PROMPT = (
    # --- VIEWPOINT: ground level inside the quad ---
    "Photorealistic 360-degree panorama captured from ground level, standing inside "
    "a grand university quadrangle, camera at human eye height (1.7 metres). "
    "The camera stands at the edge of a large green lawn looking across toward the centre of the quad. "

    # --- THE TREE: dominant, centred ---
    "Dead centre of the quadrangle: one enormous ancient plane tree (Platanus x acerifolia), "
    "25-30 metres tall, massive spreading canopy 20 metres wide, "
    "mottled grey-green bark, dense fresh green summer foliage. "
    "The tree trunk is thick and imposing. The canopy fills the upper centre of the view. "
    "Visible roots emerge slightly at the base. "

    # --- BUILDINGS: Victorian Gothic on both sides ---
    "Flanking the quad on the right side (east): a grand Victorian Gothic university building, "
    "5 storeys of honey-coloured sandstone, rows of tall pointed-arch windows on every floor, "
    "ornate carved stone hood moulds above each window, corbelled cornice, steep slate roof with "
    "decorative stone chimneys. The building facade runs the full width of the right side of the quad. "
    "Style: University of Glasgow, University of Edinburgh main quad, or Trinity College Dublin. "

    "On the left side (west): a complementary stone building, slightly more modern, "
    "with large glass panels integrated into a stone frame — historic meets contemporary. "

    "Behind the viewer (south): the quad is open, with a wide stone archway entrance. "

    "Opposite (north, behind the tree): a matching Gothic stone hall, "
    "slightly recessed, with a visible clock tower. "

    # --- GROUND PLANE ---
    "The quad floor: a large rectangle of well-maintained deep green lawn, "
    "approximately 80 metres x 60 metres. "
    "A simple stone-edged path runs around the perimeter of the lawn. "
    "No hedgerows, no flowerbeds, no benches cluttering the open space. "

    # --- SKY: clean, open, complete ---
    "Sky: bright overcast summer sky, soft diffuse light, no harsh shadows. "
    "The sky is FULLY RENDERED — clean pale blue-white overcast, no artifacts, "
    "no blurring, no floating debris. The upper portion of the panorama shows "
    "clear sky above the tree canopy and building rooflines. "

    # --- LIGHTING ---
    "Soft summer overcast light. Even illumination across the whole scene. "
    "No extreme contrast. Stone buildings glow warmly. Lawn is vivid green. "
    "Tree canopy is lit from above, leaves translucent at the edges. "

    # --- QUALITY ---
    "Photorealistic. Architectural photography quality. "
    "Every stone, window frame, and leaf is crisp and well-defined. "
    "No people. No cars. No scaffolding."
)


def upload_concept_image(path: Path) -> Optional[str]:
    """Upload concept image as a media asset and return its ID."""
    suffix = path.suffix.lower().lstrip(".")
    ext = "jpg" if suffix in ("jpg", "jpeg") else suffix

    print(f"Uploading concept image: {path.name}")
    prep = requests.post(
        f"{BASE_URL}/media-assets:prepare_upload",
        headers=HEADERS,
        json={"file_name": path.name, "kind": "image", "extension": ext},
    )
    if prep.status_code not in {200, 201, 202}:
        print(f"ERROR preparing upload {prep.status_code}: {prep.text}")
        return None

    prep_data = prep.json()
    media_asset_id = prep_data.get("media_asset", {}).get("media_asset_id")
    upload_info = prep_data.get("upload_info", {})
    upload_url = upload_info.get("upload_url")
    upload_headers = upload_info.get("required_headers", {})

    if not upload_url or not media_asset_id:
        print(f"ERROR: missing upload_url or media_asset_id in response: {prep_data}")
        return None

    with open(path, "rb") as f:
        put_resp = requests.put(upload_url, headers=upload_headers, data=f)

    if put_resp.status_code not in {200, 201, 204}:
        print(f"ERROR uploading file {put_resp.status_code}: {put_resp.text}")
        return None

    print(f"Uploaded. Media asset ID: {media_asset_id}")
    return media_asset_id


def create_master_world() -> Optional[str]:
    print("\nTREE — Generating Master Campus World")
    print("=" * 60)
    print("WHO:   No characters — world only")
    print("WHERE: Full campus — all 5 locations")
    print("WHEN:  Summer midday")
    print("WHAT:  Spatial anchor for all 19 scenes")
    print("WHY:   Consistency source of truth")
    print("HOW:   Aerial text-only — no concept image (avoids close-up scale lock)")
    print("=" * 60)
    print("Initiating generation...\n")

    payload = {
        "display_name": "Tree_MASTER_Campus_v5",
        "model": "marble-1.1-plus",
        "world_prompt": {
            "type": "text",
            "text_prompt": MASTER_PROMPT,
        },
    }

    response = requests.post(f"{BASE_URL}/worlds:generate", headers=HEADERS, json=payload)

    if response.status_code in {200, 201, 202}:
        operation_id = response.json().get("operation_id")
        print(f"Started. Operation ID: {operation_id}")
        return operation_id
    else:
        print(f"ERROR {response.status_code}: {response.text}")
        return None


def poll_for_completion(operation_id: str, poll_interval: int = 15) -> Dict:
    print("Polling ", end="", flush=True)
    world_id = None

    while True:
        response = requests.get(f"{BASE_URL}/operations/{operation_id}", headers=HEADERS)
        data = response.json()

        metadata = data.get("metadata") or {}
        progress = metadata.get("progress") or {}
        status = progress.get("status", "")

        if not world_id and metadata.get("world_id"):
            world_id = metadata["world_id"]
            print(f"\nWorld ID (mid-gen): {world_id}")
            print(f"Preview: https://marble.worldlabs.ai/world/{world_id}")
            print("Status  ", end="", flush=True)

        if data.get("done"):
            if data.get("error"):
                raise Exception(f"Generation failed: {data['error']}")
            print(f" {status}")
            snapshot = data.get("response", {})
            # Inject the world_id we captured from metadata if not in snapshot
            if world_id and not snapshot.get("id"):
                snapshot["id"] = world_id
            return snapshot

        print(".", end="", flush=True)
        time.sleep(poll_interval)


def get_full_world(world_id: str) -> Dict:
    response = requests.get(f"{BASE_URL}/worlds/{world_id}", headers=HEADERS)
    return response.json()


def print_master_assets(world: Dict) -> None:
    assets = world.get("assets", {})
    spz_urls = assets.get("splats", {}).get("spz_urls", {})
    pano_url = assets.get("imagery", {}).get("pano_url")
    world_id = world.get("world_id") or world.get("id")
    marble_url = f"https://marble.worldlabs.ai/world/{world_id}" if world_id else None

    print("\n" + "=" * 60)
    print("  MASTER CAMPUS WORLD — SAVE THESE VALUES")
    print("=" * 60)
    print(f"  World ID:         {world_id}")
    print(f"  Web Viewer:       {marble_url}")
    print(f"  Panorama (.png):  {pano_url}")
    print(f"  Collision (.glb): {assets.get('mesh', {}).get('collider_mesh_url')}")
    print(f"  Thumbnail:        {assets.get('thumbnail_url')}")
    print(f"  Splat full_res:   {spz_urls.get('full_res')}")
    print(f"  Splat 500k:       {spz_urls.get('500k')}")
    print(f"  Splat 100k:       {spz_urls.get('100k')}")
    print(f"  Caption:          {(assets.get('caption') or '')[:160]}")
    print()
    print("  Add these to your .env file:")
    print(f"  MASTER_WORLD_ID={world_id}")
    print(f"  MASTER_PANO_URL={pano_url}")
    print("=" * 60)


if __name__ == "__main__":
    if API_KEY == "YOUR_API_KEY_HERE":
        print("Please set WLT_API_KEY in your .env file.")
    else:
        operation_id = create_master_world()
        if operation_id:
            snapshot = poll_for_completion(operation_id)
            # id may be absent in snapshot — extract from world_marble_url as fallback
            world_id = snapshot.get("id")
            if not world_id:
                url = snapshot.get("world_marble_url", "")
                world_id = url.rstrip("/").split("/")[-1] if url else None
            world = get_full_world(world_id) if world_id else snapshot
            print_master_assets(world)
