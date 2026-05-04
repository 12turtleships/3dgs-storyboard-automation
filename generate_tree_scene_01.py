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
        "model": "marble-1.0-draft"  # 230 credits
    }

    response = requests.post(f"{BASE_URL}/worlds:generate", headers=HEADERS, json=payload)

    if response.status_code in {200, 201, 202}:
        data = response.json()
        operation_id = data.get("operation_id")
        print(f"✅ Generation started. Operation ID: {operation_id}")
        return operation_id
    else:
        print(f"❌ Error initiating generation: {response.status_code} {response.text}")
        return None

def poll_for_completion(operation_id: str, poll_interval: int = 15) -> Dict:
    """Polls the operations endpoint until done."""
    print(f"⏳ Polling every {poll_interval}s...")

    while True:
        response = requests.get(f"{BASE_URL}/operations/{operation_id}", headers=HEADERS)
        data = response.json()

        if data.get("done"):
            if data.get("error"):
                raise Exception(f"Generation failed: {data['error']}")
            print("\n🎉 Generation Complete!")
            return data.get("response", {})

        print(".", end="", flush=True)
        time.sleep(poll_interval)

if __name__ == "__main__":
    if API_KEY == "YOUR_API_KEY_HERE":
        print("⚠️ Please set WLT_API_KEY in your .env file.")
    else:
        operation_id = create_world()
        if operation_id:
            final_data = poll_for_completion(operation_id)

            assets = final_data.get("assets", {})
            spz_urls = assets.get("splats", {}).get("spz_urls", {})
            print("\n--- 💾 ASSET DOWNLOAD LINKS ---")
            print(f"Web Viewer URL:          {final_data.get('world_marble_url')}")
            print(f"Collision Mesh (.glb):   {assets.get('mesh', {}).get('collider_mesh_url')}")
            print(f"Thumbnail (.webp):       {assets.get('thumbnail_url')}")
            print(f"Splat full_res (.spz):   {spz_urls.get('full_res')}")
            print(f"Splat 500k (.spz):       {spz_urls.get('500k')}")
            print(f"Splat 100k (.spz):       {spz_urls.get('100k')}")
            print(f"Base Panorama (.jpg):    {assets.get('imagery', {}).get('pano_url')}")
            print(f"\nWorld ID: {final_data.get('world_id')}")
