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
    # --- VIEWPOINT ---
    "Photorealistic aerial view of a sprawling university campus, camera elevated "
    "approximately 150 feet above ground, tilted slightly downward to show the full campus. "
    "The campus stretches 800+ meters — a genuine large research university, not a small quad. "

    # --- CAMPUS STYLE: modern international, NOT British collegiate ---
    "Campus architectural style: modern international research university — "
    "mix of historic stone buildings and contemporary glass-and-concrete structures. "
    "NOT an Oxford-style enclosed collegiate quad. NOT formal English gardens or hedgerow parterres. "
    "Wide open spaces between buildings. Generous lawns. Natural informal landscaping. "
    "Think large modern university: MIT, ETH Zurich, or a large American state university. "

    # --- THE TREE ---
    "Dead center of campus: one ancient English oak, 80-100 feet tall, "
    "enormous spreading umbrella canopy 60+ feet wide, deeply furrowed grey bark, "
    "dense emerald-green summer foliage, massive gnarled roots lifting cobblestones at the base. "
    "The tree is visible from every corner of campus as the unmistakable landmark. "
    "It is surrounded by a large open cobblestone square, not a planter box, not a formal garden. "

    # --- CENTRAL QUAD: open, spacious ---
    "Around the tree: a large open cobblestone plaza, at least 100 meters across, "
    "with simple stone benches and no hedgerows, no formal gardens, no decorative parterres. "
    "Four wide straight paths (15m wide, tree-lined) radiate outward from the plaza. "

    # --- BUILDINGS: distinct, separated, varied styles ---
    "North: a large Gothic stone academic hall, 5 stories, pointed arched windows, "
    "ivy-covered, slate roof — the historic heart of campus. "
    "East: a modern glass-and-steel science complex, multiple stories, open plazas. "
    "West: contemporary arts and humanities buildings in warm brick and concrete. "
    "South: a large administration building with a visible clock tower. "
    "Northwest: a student services building with outdoor seating terraces. "
    "All buildings are large, architecturally complete, and visually distinct from each other. "
    "Each building stands 30-50 meters back from the nearest path. "

    # --- RECREATIONAL FIELD: natural grass sports field, NOT a formal garden ---
    "South of the academic core: a large open grass sports field, "
    "at least 150 meters long and 80 meters wide, natural green grass, "
    "simple white painted line markings for football/soccer, "
    "a small open-sided timber pavilion shelter on one side, "
    "a few simple wooden benches along the edge. "
    "NO hedgerows. NO formal lawn striping. NO decorative gardens. NO flagpoles. "
    "Just natural open turf with minimal markings. "
    "Clear direct sightline from the field back to the great oak. "

    # --- GROUNDS: natural, informal ---
    "Between buildings: wide open grass lawns, informal planting, mature trees. "
    "Bicycle racks. Casual seating. No formal English garden elements. "
    "Campus perimeter: low stone wall with open iron gate entries. "
    "Streets and urban context visible beyond the perimeter. "

    # --- LIGHTING ---
    f"{WHEN['afternoon']} "
    "Near-vertical summer sun, sharp shadows, intense green vegetation, "
    "warm stone and concrete in direct light. "

    # --- ATMOSPHERE ---
    "No people. Enormous scale. Real institution. Every surface has material weight and age."
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
        "display_name": "Tree_MASTER_Campus_v4",
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
