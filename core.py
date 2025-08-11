import random
import requests
import toml
import os

# Load config
config_path = os.path.join(os.path.dirname(__file__), "config.toml")
config = toml.load(config_path)
RBXL_PATH = config["RBXLPath"]

# 🎮 Name/description combos
_game_combos = [
    ("Obby of Shadows", "Escape the cursed maze before the shadows catch you."),
    ("Pet Simulator X+", "Collect mythical pets and unlock secret worlds."),
    ("Survive the Hacker", "Avoid getting traced in this digital survival thriller."),
    ("Blox Royale", "Battle your friends in a fast-paced arena showdown."),
    ("Tycoon Empire", "Build your empire from scratch and dominate the leaderboard.")
]

def pick_combo():
    return random.choice(_game_combos)

def get_csrf_token(cookie: str) -> str:
    headers = { "Cookie": f".ROBLOSECURITY={cookie}" }
    response = requests.post("https://auth.roblox.com/v2/logout", headers=headers)
    return response.headers.get("x-csrf-token", "")

def create_game(cookie: str, name: str, description: str) -> dict:
    csrf = get_csrf_token(cookie)
    headers = {
        "Cookie": f".ROBLOSECURITY={cookie}",
        "Content-Type": "application/json",
        "X-CSRF-TOKEN": csrf
    }
    payload = {
        "name": name,
        "description": description,
        "creatorType": "User",
        "createUniverse": True
    }
    response = requests.post("https://develop.roblox.com/v1/universes/create", headers=headers, json=payload)
    if response.status_code == 200:
        data = response.json()
        return {
            "universeId": data["universeId"],
            "placeId": data["rootPlaceId"]
        }
    else:
        raise Exception(f"❌ Game creation failed: {response.status_code} - {response.text}")

def configure_game(cookie: str, universe_id: int):
    csrf = get_csrf_token(cookie)
    headers = {
        "Cookie": f".ROBLOSECURITY={cookie}",
        "Content-Type": "application/json",
        "X-CSRF-TOKEN": csrf
    }
    payload = {
        "maxPlayerCount": 200,
        "avatarType": "R6",
        "allowThirdPartySales": True,
        "allowThirdPartyTeleport": True,
        "privateServers": {
            "active": True,
            "price": 0
        }
    }
    url = f"https://develop.roblox.com/v1/universes/{universe_id}/configuration"
    response = requests.patch(url, headers=headers, json=payload)
    if response.status_code == 200:
        print("✅ Game configured successfully")
    else:
        raise Exception(f"❌ Configuration failed: {response.status_code} - {response.text}")

def upload_rbxl(cookie: str, place_id: int, file_path: str):
    csrf = get_csrf_token(cookie)
    with open(file_path, "rb") as f:
        rbxl_data = f.read()
    headers = {
        "Cookie": f".ROBLOSECURITY={cookie}",
        "Content-Type": "application/octet-stream",
        "User-Agent": "Roblox/WinInet",
        "X-CSRF-TOKEN": csrf
    }
    url = f"https://data.roblox.com/Data/Upload.ashx?assetid={place_id}"
    response = requests.post(url, headers=headers, data=rbxl_data)
    if response.status_code == 200:
        print("✅ RBXL upload successful")
    else:
        raise Exception(f"❌ Upload failed: {response.status_code} - {response.text}")