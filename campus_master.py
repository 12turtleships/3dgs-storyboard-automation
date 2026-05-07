import os
import time
import requests
from typing import Dict, Optional
from dotenv import load_dotenv

from story_plot import WHERE, WHEN, STYLE_SUFFIX

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
# HOW:   Overhead god's-eye view; storyboard illustration style.
#
# After running: copy MASTER_WORLD_ID and MASTER_PANO_URL into .env
# ---------------------------------------------------------------------------

MASTER_PROMPT = (
    # WHO: none — establishing the world only
    # WHERE: all five campus locations
    # WHEN: summer midday
    # WHAT: spatial anchor for all 19 scenes
    # WHY: single source of truth for spatial and visual consistency
    # HOW: overhead god's-eye, storyboard illustration
    "Aerial establishing shot of an entire university campus in full summer — "
    "the complete world of the film revealed in one frame. "
    "At the absolute center: a single colossal ancient oak tree in a large open stone courtyard, "
    "its massive trunk and vast lush deep emerald-green canopy towering above everything, "
    "unmistakably the heart and soul of this campus. "
    f"{WHERE['courtyard']} "
    "Radiating outward: wide cobblestone pathways connecting to surrounding buildings. "
    f"{WHERE['pathways']} "
    "To one side: an open green recreational field, lush summer lawn, scattered benches, sports markings. "
    "Academic buildings with large ground-floor classroom windows visible. "
    f"{WHEN['afternoon']} "
    "The campus is breathtaking, alive, and full of beauty that no one is noticing. "
    "No people visible — a world waiting to be seen. "
    f"{STYLE_SUFFIX}"
)


def create_master_world() -> Optional[str]:
    print("\nTREE — Generating Master Campus World")
    print("=" * 60)
    print("WHO:   No characters — world only")
    print("WHERE: Full campus — all 5 locations")
    print("WHEN:  Summer midday")
    print("WHAT:  Spatial anchor for all 19 scenes")
    print("WHY:   Consistency source of truth")
    print("HOW:   Overhead establishing, storyboard illustration")
    print("=" * 60)
    print("Initiating generation...\n")

    payload = {
        "display_name": "Tree_MASTER_Campus",
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
