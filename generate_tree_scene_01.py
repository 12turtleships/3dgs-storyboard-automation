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

def create_world() -> Optional[str]:
    """Sends the POST request to start generating the 3D environment."""
    print("🎬 Kicking off generation for Scene 1: The Arboreal Monolith...")

    payload = {
        "world_prompt": {
            "type": "text",
            "text_prompt": "Low angle wide shot, worm's-eye view looking straight up the trunk of a massive ancient Sequoia tree with rugged deep bark, a single leaf twitches in the wind while the tree stands still, located in a cold grey concrete brutalist university courtyard at dawn under a deep purple and orange sky, 70mm film look, hyper-realistic, high contrast, cinematic lighting.",
            "disable_recaption": False
        },
        "display_name": "Tree_Scene_01_Monolith",
        "model": "marble-1.0-draft"  # Using 230 credits for the initial test
    }

    response = requests.post(f"{BASE_URL}/worlds:generate", headers=HEADERS, json=payload)

    if response.status_code in {200, 201, 202}:
        world_id = response.json().get("world_id")
        print(f"✅ Generation started successfully. World ID: {world_id}")
        return world_id
    else:
        print(f"❌ Error initiating generation: {response.text}")
        return None

def poll_for_completion(world_id: str, poll_interval: int = 15) -> Dict:
    """Polls the GET endpoint until the generation status is complete."""
    print(f"⏳ Polling status every {poll_interval} seconds...")

    while True:
        response = requests.get(f"{BASE_URL}/worlds/{world_id}", headers=HEADERS)
        data = response.json()

        status = data.get("status", "unknown").lower()

        if status == "completed":
            print("\n🎉 Generation Complete!")
            return data
        elif status == "failed":
            raise Exception(f"Generation failed: {data.get('error_message', 'Unknown error')}")

        # Print a simple loading indicator
        print(".", end="", flush=True)
        time.sleep(poll_interval)

if __name__ == "__main__":
    if API_KEY == "YOUR_API_KEY_HERE":
        print("⚠️ Please insert your API key or set the WLT_API_KEY environment variable.")
    else:
        world_id = create_world()
        if world_id:
            final_data = poll_for_completion(world_id)

            # Extract and print the critical asset URLs
            assets = final_data.get("assets", {})
            print("\n--- 💾 ASSET DOWNLOAD LINKS ---")
            print(f"Web Viewer URL: {final_data.get('world_marble_url')}")
            print(f"Gaussian Splat (.spz): {assets.get('splats', {}).get('spz_urls', {}).get('main')}")
            print(f"Collision Mesh (.glb): {assets.get('mesh', {}).get('collider_mesh_url')}")
            print(f"Base Panorama (.jpg): {assets.get('imagery', {}).get('pano_url')}")
