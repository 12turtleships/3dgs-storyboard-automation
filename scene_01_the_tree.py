import os
import time
import requests
from typing import Dict, Optional, List
from dotenv import load_dotenv

from story_bible import WHO, WHERE, WHEN, STYLE_SUFFIX, build_prompt

load_dotenv()

API_KEY = os.environ.get("WLT_API_KEY", "YOUR_API_KEY_HERE")
BASE_URL = "https://api.worldlabs.ai/marble/v1"
HEADERS = {
    "Content-Type": "application/json",
    "WLT-Api-Key": API_KEY
}

MODEL = "marble-1.1-plus"
MASTER_PANO_URL = os.environ.get("MASTER_PANO_URL")

# =============================================================================
# SCENE 01 — "THE TREE"
#
# WHO:   No characters yet (1A-1E). Students appear in 1F, still anonymous.
# WHERE: Central courtyard + full campus (1A), narrowing to tree details (1B-1E).
# WHEN:  Early morning → the world before it fills with people.
# WHAT:  Reveal the beauty that the students cannot see.
# WHY:   The audience must fall in love with this world before watching
#        it be ignored — that contrast is the film's emotional engine.
# HOW:   Overhead → wide courtyard → worm's eye → canopy → roots → transition.
#        Slow, reverent pacing. Holds each shot longer than comfortable.
#        Reference: the monolith reveal sequence, 2001: A Space Odyssey.
# =============================================================================

SHOTS: List[Dict] = [
    {
        "id": "1A",
        "label": "Full Campus — The Entire World Revealed",
        "display_name": "Tree_S01_1A_Campus",
        "who": "None — no characters yet.",
        "where": "overhead",
        "when": "early_morning",
        "prompt": build_prompt(
            narrative=(
                "Overhead aerial view revealing the entire university campus in one sweeping frame — "
                "the complete world of the film introduced at once."
            ),
            visual=(
                "The campus fills the frame edge to edge: warm stone Gothic and modernist buildings, "
                "ivy-covered walls, cobblestone courtyards, winding pathways, an open green recreational field. "
                f"{WHERE['courtyard']} "
                "At the absolute center, the colossal ancient oak tree — its vast emerald canopy "
                "towers above all architecture, the undeniable heart of this world. "
                "All five campus locations visible from this god's-eye perspective."
            ),
            characters="No people visible. The campus breathes on its own.",
            lighting_key="early_morning",
            tone="Epic, serene, and full of quiet beauty waiting to be discovered.",
        ),
    },
    {
        "id": "1B",
        "label": "Courtyard Wide — Tree as Undeniable Center",
        "display_name": "Tree_S01_1B_Courtyard",
        "who": "None.",
        "where": "courtyard",
        "when": "early_morning",
        "prompt": build_prompt(
            narrative="Ground-level wide shot of the central courtyard — we have descended into the world.",
            visual=(
                f"{WHERE['courtyard']} "
                "The tree occupies the center third of the frame from ground to top of canopy. "
                "Pathways radiate left and right. Buildings frame the background. "
                "Foreground: cobblestones and gnarled roots. "
                "Anamorphic lens flare from low morning sun."
            ),
            characters="No people. The courtyard is entirely the tree's.",
            lighting_key="early_morning",
            tone="Reverent, quiet, monumental.",
        ),
    },
    {
        "id": "1C",
        "label": "Worm's Eye — The Monolith Reveal",
        "display_name": "Tree_S01_1C_Monolith",
        "who": WHO["tree"],
        "where": "under_tree",
        "when": "early_morning",
        "prompt": build_prompt(
            narrative=(
                "Extreme low angle worm's-eye view looking straight up the trunk — "
                "the tree revealed as a monolith."
            ),
            visual=(
                f"{WHO['tree']} "
                "Trunk fills the entire frame from bottom edge, rising impossibly tall like a cathedral column. "
                "Branches reach outward like arms against the sky. "
                "The tree feels divine, ancient, immovable. "
                "Deep blue summer sky visible around the spreading canopy above."
            ),
            characters="No humans. Only bark, branches, sky.",
            lighting_key="early_morning",
            tone="Awe-inspiring, sacred, slightly overwhelming — small against something enormous.",
        ),
    },
    {
        "id": "1D",
        "label": "Canopy Upshot — Natural Cathedral",
        "display_name": "Tree_S01_1D_Canopy",
        "who": WHO["tree"],
        "where": "under_tree",
        "when": "mid_morning",
        "prompt": build_prompt(
            narrative="Looking up through the canopy — the tree becomes a cathedral of light and green.",
            visual=(
                "Thousands of lush deep emerald-green summer leaves filter brilliant sunlight "
                "into scattered rays, volumetric light beams, and soft bokeh. "
                "Canopy forms a vaulted ceiling of nature. "
                "Patches of brilliant deep blue sky between the leaves. "
                "Light rays visibly descending through layers of green."
            ),
            characters="No people. Pure tree and sky.",
            lighting_key="mid_morning",
            tone="Transcendent, sacred, breathtaking — the most beautiful thing in the film.",
        ),
    },
    {
        "id": "1E",
        "label": "Root Level — Nature Reclaiming Stone",
        "display_name": "Tree_S01_1E_Roots",
        "who": WHO["tree"],
        "where": "courtyard",
        "when": "early_morning",
        "prompt": build_prompt(
            narrative=(
                "Ground-level detail shot — the tree's roots cracking and lifting the cobblestones, "
                "nature quietly reclaiming the campus from the ground up."
            ),
            visual=(
                "Massive gnarled roots spread across ancient cobblestones in the foreground, "
                "cracking and lifting the stone — beautiful and unstoppable. "
                "Moss and lichen on the north-facing root surfaces. "
                "Trunk rises powerfully from frame bottom. "
                "Behind it: warm stone university buildings, ivy walls, arched windows. "
                f"{WHERE['courtyard']}"
            ),
            characters="No people. The tree owns this ground.",
            lighting_key="early_morning",
            tone="Peaceful, timeless, quietly powerful — patience made visible.",
        ),
    },
    {
        "id": "1F",
        "label": "Transition — Campus Full, Students Blind",
        "display_name": "Tree_S01_1F_Oblivious",
        "who": WHO["students"],
        "where": "courtyard",
        "when": "mid_morning",
        "prompt": build_prompt(
            narrative=(
                "The world fills with people — and no one sees it. "
                "The transition shot: beauty ignored, the film's central irony established."
            ),
            visual=(
                "Wide shot pulling back to reveal the full courtyard. "
                "The magnificent ancient oak tree stands glorious at center, canopy enormous and green. "
                f"{WHERE['courtyard']} "
                "Streams of students flow past on every cobblestone pathway — "
                "every single one head bowed, face lit by smartphone screen glow. "
                "Tree sharp and detailed in the background; students softer, generic, interchangeable."
            ),
            characters=f"{WHO['students']} The tree and the students exist in the same frame but different worlds.",
            lighting_key="mid_morning",
            tone="Melancholy and ironic — overwhelming beauty, complete blindness.",
        ),
    },
]


def build_payload(shot: Dict) -> Dict:
    if MASTER_PANO_URL:
        return {
            "display_name": shot["display_name"],
            "model": MODEL,
            "world_prompt": {
                "type": "image",
                "image_prompt": {
                    "source": "uri",
                    "uri": MASTER_PANO_URL,
                    "is_pano": True,
                },
                "text_prompt": shot["prompt"],
            },
        }
    return {
        "display_name": shot["display_name"],
        "model": MODEL,
        "world_prompt": {
            "type": "text",
            "text_prompt": shot["prompt"],
        },
    }


def create_world(shot: Dict) -> Optional[str]:
    print(f"\n{'='*60}")
    print(f"  Shot {shot['id']} — {shot['label']}")
    print(f"  WHO:   {shot.get('who', '')[:80]}")
    print(f"  WHERE: {shot.get('where', '')}")
    print(f"  WHEN:  {shot.get('when', '')}")
    print(f"  Mode:  {'image (anchored to master)' if MASTER_PANO_URL else 'text only'}")
    print(f"{'='*60}")

    response = requests.post(
        f"{BASE_URL}/worlds:generate",
        headers=HEADERS,
        json=build_payload(shot)
    )

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

        metadata = data.get("metadata") or {}
        progress = metadata.get("progress") or {}
        status = progress.get("status", "")

        if not world_id and metadata.get("world_id"):
            world_id = metadata["world_id"]
            print(f"\n  World ID: {world_id}")
            print(f"  Preview:  https://marble.worldlabs.ai/world/{world_id}")
            print(f"  Status  ", end="", flush=True)

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


def print_assets(shot: Dict, world: Dict) -> None:
    assets = world.get("assets", {})
    spz_urls = assets.get("splats", {}).get("spz_urls", {})
    print(f"\n  Assets — Shot {shot['id']}: {shot['label']}")
    print(f"    Web Viewer:       {world.get('world_marble_url')}")
    print(f"    Collision (.glb): {assets.get('mesh', {}).get('collider_mesh_url')}")
    print(f"    Thumbnail:        {assets.get('thumbnail_url')}")
    print(f"    Splat full_res:   {spz_urls.get('full_res')}")
    print(f"    Splat 500k:       {spz_urls.get('500k')}")
    print(f"    Splat 100k:       {spz_urls.get('100k')}")
    print(f"    Panorama (.jpg):  {assets.get('imagery', {}).get('pano_url')}")
    print(f"    Caption:          {(assets.get('caption') or '')[:120]}")
    print(f"    World ID:         {world.get('id')}")


if __name__ == "__main__":
    if API_KEY == "YOUR_API_KEY_HERE":
        print("Please set WLT_API_KEY in your .env file.")
    else:
        if not MASTER_PANO_URL:
            print("WARNING: MASTER_PANO_URL not set — running in text-only mode.")
            print("Run campus_master.py first for spatial consistency.\n")

        print("\nTREE — Scene 01: 'The Tree'")
        print(f"Model: {MODEL} | Shots: {len(SHOTS)}")
        print(f"Anchored to master: {'YES' if MASTER_PANO_URL else 'NO (text-only fallback)'}\n")

        for shot in SHOTS:
            operation_id = create_world(shot)
            if operation_id:
                snapshot = poll_for_completion(operation_id, shot["id"])
                world_id = snapshot.get("id")
                world = get_full_world(world_id) if world_id else snapshot
                print_assets(shot, world)

        print("\n\nScene 01 complete.")
