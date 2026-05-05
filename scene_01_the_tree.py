import os
import time
import requests
from typing import Dict, Optional, List
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.environ.get("WLT_API_KEY", "YOUR_API_KEY_HERE")
BASE_URL = "https://api.worldlabs.ai/marble/v1"
HEADERS = {
    "Content-Type": "application/json",
    "WLT-Api-Key": API_KEY
}

# marble-1.1-plus: larger worlds when prompted for outdoor/large spaces — ideal for campus shots
MODEL = "marble-1.1-plus"

# ---------------------------------------------------------------------------
# SCENE 1 — "THE TREE"
# Directorial intent: No dialogue, no students yet. Just the tree.
# The audience falls in love with what the students cannot see.
# Pacing: slow, reverent, sacred. Each shot holds longer than comfortable.
# Reference: the monolith reveal sequence, 2001: A Space Odyssey.
# ---------------------------------------------------------------------------

SHOTS: List[Dict] = [
    {
        "id": "1A",
        "label": "Establishing Wide — Campus & Tree",
        "display_name": "Tree_S01_1A_Establishing",
        "prompt": (
            "Sweeping ultra-wide establishing shot of a grand university campus at golden hour. "
            "A colossal ancient oak tree dominates the center of an open stone courtyard, its massive "
            "trunk and vast sprawling canopy dwarfing the surrounding Gothic and modernist university "
            "architecture. Lush deep green summer leaves catch the late afternoon sun. Long dramatic "
            "shadows stretch across the cobblestone path. The tree radiates quiet, undeniable presence. "
            "No people visible — a moment of pure natural beauty before the world intrudes. "
            "70mm film look, anamorphic lens flare, hyper-realistic, cinematic, lush green summer palette, epic scale."
        ),
    },
    {
        "id": "1B",
        "label": "Worm's Eye — Monolith Reveal",
        "display_name": "Tree_S01_1B_Monolith",
        "prompt": (
            "Extreme low angle worm's-eye view looking straight up the trunk of a massive ancient oak tree, "
            "rugged deeply furrowed bark filling the entire frame, the trunk rising impossibly tall like a "
            "cathedral column, branches reaching outward like arms against a deep blue and violet dawn sky. "
            "The tree feels monolithic, towering, divine — a silent sentinel. Dappled early morning light "
            "catches the texture of the bark. No humans. "
            "70mm film look, high contrast, cinematic lighting, hyper-realistic, awe-inspiring."
        ),
    },
    {
        "id": "1C",
        "label": "Canopy Upshot — Natural Cathedral",
        "display_name": "Tree_S01_1C_Canopy",
        "prompt": (
            "Looking up through the vast canopy of an ancient oak tree, thousands of golden and green "
            "lush green summer leaves filtering brilliant sunlight into scattered rays and soft bokeh. The canopy "
            "forms a natural cathedral ceiling — transcendent, sacred, breathtaking. Patches of deep blue "
            "sky visible between the leaves. Light is bright and warm, vibrant green glow. The effect is spiritual and "
            "beautiful. No people. "
            "70mm film look, shallow depth of field, warm luminous tones, hyper-realistic, cinematic."
        ),
    },
    {
        "id": "1D",
        "label": "Root Level — Tree and Campus",
        "display_name": "Tree_S01_1D_Roots",
        "prompt": (
            "Medium wide ground-level shot showing the massive gnarled roots of an ancient oak tree "
            "spreading organically across old stone cobblestones, cracking and lifting the pavement — "
            "nature reclaiming space. The tree trunk rises powerfully out of frame. Behind it, beautiful "
            "university buildings in warm stone, ivy-covered walls, arched windows. Early morning mist "
            "still lingers low across the courtyard. The scene is peaceful, timeless, alive. No people. "
            "70mm film look, warm morning light, cinematic, contemplative, hyper-realistic."
        ),
    },
    {
        "id": "1E",
        "label": "Transition — Students Arrive, Oblivious",
        "display_name": "Tree_S01_1E_Oblivious",
        "prompt": (
            "Wide shot of a beautiful university campus courtyard, the majestic ancient oak tree standing "
            "glorious and enormous in the center background, its canopy full and richly green in summer morning light. "
            "In the foreground and midground, streams of university students flow past on the cobblestone "
            "path — every single one with their head bowed down, face illuminated by the glow of a "
            "smartphone screen. The contrast is stark: overwhelming natural beauty behind them, complete "
            "digital oblivion in front. The tree is sharp and magnificent; the students are slightly soft. "
            "70mm film look, cinematic wide, bright summer morning, hyper-realistic, melancholy and ironic tone."
        ),
    },
]


def create_world(shot: Dict) -> Optional[str]:
    print(f"\n{'='*60}")
    print(f"  Shot {shot['id']} — {shot['label']}")
    print(f"{'='*60}")
    print(f"  Model: {MODEL}")
    print("  Initiating generation...")

    payload = {
        "display_name": shot["display_name"],
        "model": MODEL,
        "world_prompt": {
            "type": "text",
            "text_prompt": shot["prompt"],
        },
    }

    response = requests.post(f"{BASE_URL}/worlds:generate", headers=HEADERS, json=payload)

    if response.status_code in {200, 201, 202}:
        operation_id = response.json().get("operation_id")
        print(f"  Started. Operation ID: {operation_id}")
        return operation_id
    else:
        print(f"  ERROR {response.status_code}: {response.text}")
        return None


def poll_for_completion(operation_id: str, shot_id: str, poll_interval: int = 15) -> Dict:
    print(f"  Polling [{shot_id}] ", end="", flush=True)
    world_id = None

    while True:
        response = requests.get(f"{BASE_URL}/operations/{operation_id}", headers=HEADERS)
        data = response.json()

        # Surface world_id and progress status as soon as they're available mid-generation
        metadata = data.get("metadata") or {}
        progress = metadata.get("progress") or {}
        status = progress.get("status", "")
        if not world_id and metadata.get("world_id"):
            world_id = metadata["world_id"]
            print(f"\n  World ID (mid-gen): {world_id}")
            print(f"  Preview: https://marble.worldlabs.ai/world/{world_id}")
            print(f"  Status  ", end="", flush=True)

        if data.get("done"):
            if data.get("error"):
                raise Exception(f"Generation failed: {data['error']}")
            print(f" {status}")
            return data.get("response", {})

        print(".", end="", flush=True)
        time.sleep(poll_interval)


def get_full_world(world_id: str) -> Dict:
    """Fetch the complete, up-to-date world object after generation."""
    response = requests.get(f"{BASE_URL}/worlds/{world_id}", headers=HEADERS)
    return response.json().get("world", {})


def print_assets(shot: Dict, world: Dict) -> None:
    assets = world.get("assets", {})
    spz_urls = assets.get("splats", {}).get("spz_urls", {})
    print(f"\n  Assets for Shot {shot['id']} — {shot['label']}:")
    print(f"    Web Viewer:       {world.get('world_marble_url')}")
    print(f"    Collision (.glb): {assets.get('mesh', {}).get('collider_mesh_url')}")
    print(f"    Thumbnail:        {assets.get('thumbnail_url')}")
    print(f"    Splat full_res:   {spz_urls.get('full_res')}")
    print(f"    Splat 500k:       {spz_urls.get('500k')}")
    print(f"    Splat 100k:       {spz_urls.get('100k')}")
    print(f"    Panorama (.jpg):  {assets.get('imagery', {}).get('pano_url')}")
    print(f"    Caption:          {assets.get('caption', '')[:120]}")
    print(f"    World ID:         {world.get('id')}")


if __name__ == "__main__":
    if API_KEY == "YOUR_API_KEY_HERE":
        print("Please set WLT_API_KEY in your .env file.")
    else:
        print("\nTREE — Scene 01: 'The Tree'")
        print(f"Model: {MODEL} | Shots: {len(SHOTS)}\n")

        for shot in SHOTS:
            operation_id = create_world(shot)
            if operation_id:
                snapshot = poll_for_completion(operation_id, shot["id"])
                # Fetch full world for complete fields (display_name, model, world_prompt, timestamps)
                world_id = snapshot.get("id")
                world = get_full_world(world_id) if world_id else snapshot
                print_assets(shot, world)

        print("\n\nScene 01 complete.")
