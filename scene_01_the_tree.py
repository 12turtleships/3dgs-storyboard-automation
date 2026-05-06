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

_STYLE = (
    "Storyboard illustration style, not photorealistic, no live actors. "
    "Semi-painterly digital art with clean linework, expressive human figures, "
    "and highly detailed natural elements especially trees and light. "
    "Rich summer color palette: deep greens, warm stone, golden light. "
    "Cinematic composition with dramatic depth and layered foreground-midground-background. "
    "Visible brushwork, warm paper grain, film grain overlay. "
    "Animated pre-visualization quality. Clear storytelling in a single frame."
)

_TREE = (
    "Ancient English Oak, 80-100 feet tall, trunk 12+ feet in diameter, deep charcoal-grey "
    "heavily furrowed bark with patches of lichen and moss at the base. "
    "Massive broad umbrella-like canopy of lush dense deep emerald-green summer leaves. "
    "Monolithic, immobile, permanent — the most detailed element in every frame."
)

_STUDENTS = (
    "University students ages 18-24, diverse group, all uniformly slouched with heads bowed "
    "to glowing smartphone screens. Faces lit identically by screen glow. "
    "Moving by rote muscle memory, zero eye contact with surroundings. "
    "Backpacks, hoodies, mixed casual university attire."
)

_COURTYARD = (
    "Central university courtyard: large open stone square, ancient cobblestones in grey and tan "
    "worn smooth by decades of foot traffic, five pathways radiating outward, "
    "surrounding warm stone Gothic and modernist university buildings, ivy-covered walls, tall arched windows. "
    "Tree roots crack and lift the cobblestones — nature reclaiming human space."
)

_EARLY_MORNING = (
    "Early morning, 7-9 AM. Low-angle golden side-light, long shadows across the courtyard. "
    "Soft warm directional light. Clear bright blue sky. "
    "Tree dramatically side-lit, trunk texture and bark fully visible."
)

_MID_MORNING = (
    "Mid-morning, 9 AM - 12 PM. Sun higher, shadows shorter, bright high-contrast summer daylight. "
    "Brilliant deep blue sky. Tree canopy brightly lit from above."
)


SHOTS: List[Dict] = [
    {
        "id": "1A",
        "label": "Full Campus — The Entire World Revealed",
        "display_name": "Tree_S01_1A_Campus",
        "who": "None — no characters.",
        "where": "Full campus overhead",
        "when": "Early morning",
        "prompt": (
            "Overhead aerial view revealing the entire university campus in one sweeping frame — "
            "the complete world of the film introduced at once. "
            "The campus fills the frame: warm stone Gothic and modernist buildings, "
            "ivy-covered walls, cobblestone courtyards, winding pathways, an open green recreational field. "
            f"{_COURTYARD} "
            "At the absolute center, the colossal ancient oak tree — its vast emerald canopy "
            "towers above all architecture, the undeniable heart of this world. "
            "All campus locations visible from this god's-eye perspective. "
            "No people visible. The campus breathes on its own. "
            f"{_EARLY_MORNING} "
            "Epic, serene, and full of quiet beauty waiting to be discovered. "
            f"{_STYLE}"
        ),
    },
    {
        "id": "1B",
        "label": "Courtyard Wide — Tree as Undeniable Center",
        "display_name": "Tree_S01_1B_Courtyard",
        "who": "None.",
        "where": "Central courtyard",
        "when": "Early morning",
        "prompt": (
            "Ground-level wide shot of the central courtyard — descended into the world. "
            f"{_COURTYARD} "
            "The tree occupies the center third of the frame from ground to top of canopy. "
            "Pathways radiate left and right. Buildings frame the background. "
            "Foreground: cobblestones and gnarled roots. Anamorphic lens flare from low morning sun. "
            "No people. The courtyard is entirely the tree's. "
            f"{_EARLY_MORNING} "
            "Reverent, quiet, monumental. "
            f"{_STYLE}"
        ),
    },
    {
        "id": "1C",
        "label": "Worm's Eye — The Monolith Reveal",
        "display_name": "Tree_S01_1C_Monolith",
        "who": "The Tree only.",
        "where": "Under the tree",
        "when": "Early morning",
        "prompt": (
            "Extreme low angle worm's-eye view looking straight up the trunk — the tree as monolith. "
            f"{_TREE} "
            "Trunk fills the entire frame from bottom edge, rising impossibly tall like a cathedral column. "
            "Branches reach outward like arms against the deep blue summer sky. "
            "No humans. Only bark, branches, sky. "
            f"{_EARLY_MORNING} "
            "Awe-inspiring, sacred, slightly overwhelming — small against something enormous. "
            f"{_STYLE}"
        ),
    },
    {
        "id": "1D",
        "label": "Canopy Upshot — Natural Cathedral",
        "display_name": "Tree_S01_1D_Canopy",
        "who": "The Tree only.",
        "where": "Under the tree",
        "when": "Mid-morning",
        "prompt": (
            "Looking up through the canopy — the tree becomes a cathedral of light and green. "
            "Thousands of lush deep emerald-green summer leaves filter brilliant sunlight "
            "into scattered rays, volumetric light beams, and soft bokeh. "
            "Canopy forms a vaulted ceiling of nature. "
            "Patches of brilliant deep blue sky between the leaves. "
            "No people. Pure tree and sky. "
            f"{_MID_MORNING} "
            "Transcendent, sacred, breathtaking — the most beautiful thing in the film. "
            f"{_STYLE}"
        ),
    },
    {
        "id": "1E",
        "label": "Root Level — Nature Reclaiming Stone",
        "display_name": "Tree_S01_1E_Roots",
        "who": "The Tree only.",
        "where": "Central courtyard, ground level",
        "when": "Early morning",
        "prompt": (
            "Ground-level detail — the tree's roots cracking and lifting the cobblestones, "
            "nature quietly reclaiming the campus from the ground up. "
            "Massive gnarled roots spread across ancient cobblestones in the foreground, "
            "cracking and lifting the stone — beautiful and unstoppable. "
            "Moss and lichen on the north-facing root surfaces. "
            "Trunk rises powerfully from frame bottom. "
            "Behind it: warm stone university buildings, ivy walls, arched windows. "
            "No people. The tree owns this ground. "
            f"{_EARLY_MORNING} "
            "Peaceful, timeless, quietly powerful — patience made visible. "
            f"{_STYLE}"
        ),
    },
    {
        "id": "1F",
        "label": "Transition — Campus Full, Students Blind",
        "display_name": "Tree_S01_1F_Oblivious",
        "who": "Students (background, anonymous).",
        "where": "Central courtyard",
        "when": "Mid-morning",
        "prompt": (
            "The world fills with people — and no one sees it. "
            "Beauty ignored: the film's central irony established in one frame. "
            "Wide shot of the full courtyard. The magnificent ancient oak tree stands glorious at center. "
            f"{_COURTYARD} "
            f"{_STUDENTS} "
            "Streams of students flow past on every cobblestone pathway — "
            "every single one head bowed, face lit by smartphone screen glow. "
            "Tree sharp and magnificent in the background; students softer, generic, interchangeable. "
            "The tree and the students exist in the same frame but in different worlds. "
            f"{_MID_MORNING} "
            "Melancholy and ironic — overwhelming beauty, complete blindness. "
            f"{_STYLE}"
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
