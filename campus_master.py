import os
import time
import requests
from typing import Dict, Optional
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.environ.get("WLT_API_KEY", "YOUR_API_KEY_HERE")
BASE_URL = "https://api.worldlabs.ai/marble/v1"
HEADERS = {
    "Content-Type": "application/json",
    "WLT-Api-Key": API_KEY
}

# ---------------------------------------------------------------------------
# MASTER CAMPUS WORLD
#
# This is the single spatial source of truth for the entire film "TREE".
# Every scene — courtyard, pathways, classroom, playground — must be
# spatially consistent with this world.
#
# Generation strategy:
#   1. Generate this master world first.
#   2. Save the world_id and pano_url from the output.
#   3. All scene scripts reference this world's panorama as image input
#      to anchor spatial and visual consistency across all 19 scenes.
#
# Campus layout (all locations present in this world):
#   - Central courtyard: massive ancient oak tree, cobblestone ground
#   - Radial pathways: connecting courtyard to buildings and campus exit
#   - Academic buildings: Gothic + modernist mix, ivy-covered stone
#   - Computer classroom: visible through ground-floor windows
#   - Open green field / playground: to one side of the courtyard
#   - Campus entrance: pathway leading off-campus
#   - Sky: bright summer blue, full sun
# ---------------------------------------------------------------------------

MASTER_WORLD = {
    "display_name": "Tree_MASTER_Campus",
    "prompt": (
        "Aerial wide establishing shot of a grand, sprawling university campus in full summer. "
        "At the heart of the campus stands a single colossal ancient oak tree in the center of a large "
        "open stone courtyard — its massive trunk, enormous spreading canopy, and lush deep green leaves "
        "make it the undeniable focal point of the entire campus. "
        "Radiating outward from the courtyard: wide cobblestone pathways connecting to surrounding "
        "university buildings in warm stone Gothic and modernist architecture, ivy climbing the walls, "
        "tall arched windows. To one side of the campus, an open green recreational field with grass. "
        "Academic buildings with ground-floor classroom windows visible. "
        "The campus is beautiful, alive, sun-drenched — a place of learning surrounded by nature. "
        "Bright summer daylight, lush green everywhere, no people visible. "
        "70mm film look, epic scale, hyper-realistic, cinematic, god's-eye perspective."
    ),
}


def create_master_world() -> Optional[str]:
    print("\nTREE — Generating Master Campus World")
    print("=" * 60)
    print("This world is the spatial anchor for all 19 scenes.")
    print("=" * 60)
    print(f"\nModel: marble-1.1-plus")
    print("Initiating generation...\n")

    payload = {
        "display_name": MASTER_WORLD["display_name"],
        "model": "marble-1.1-plus",
        "world_prompt": {
            "type": "text",
            "text_prompt": MASTER_WORLD["prompt"],
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
            return data.get("response", {})

        print(".", end="", flush=True)
        time.sleep(poll_interval)


def get_full_world(world_id: str) -> Dict:
    response = requests.get(f"{BASE_URL}/worlds/{world_id}", headers=HEADERS)
    return response.json().get("world", {})


def print_master_assets(world: Dict) -> None:
    assets = world.get("assets", {})
    spz_urls = assets.get("splats", {}).get("spz_urls", {})
    pano_url = assets.get("imagery", {}).get("pano_url")
    world_id = world.get("id")

    print("\n" + "=" * 60)
    print("  MASTER CAMPUS WORLD — SAVE THESE VALUES")
    print("=" * 60)
    print(f"  World ID:         {world_id}")
    print(f"  Web Viewer:       {world.get('world_marble_url')}")
    print(f"  Panorama (.jpg):  {pano_url}")
    print(f"  Collision (.glb): {assets.get('mesh', {}).get('collider_mesh_url')}")
    print(f"  Thumbnail:        {assets.get('thumbnail_url')}")
    print(f"  Splat full_res:   {spz_urls.get('full_res')}")
    print(f"  Splat 500k:       {spz_urls.get('500k')}")
    print(f"  Splat 100k:       {spz_urls.get('100k')}")
    print(f"  Caption:          {(assets.get('caption') or '')[:160]}")
    print()
    print("  Next step: set MASTER_WORLD_ID and MASTER_PANO_URL in .env")
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
            world_id = snapshot.get("id")
            world = get_full_world(world_id) if world_id else snapshot
            print_master_assets(world)
