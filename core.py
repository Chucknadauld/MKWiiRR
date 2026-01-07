"""
MKWiiRR Core
Shared functions for RWFC API access.
"""

import requests

API_URL = "https://rwfc.net/api/roomstatus"


def fetch_rooms():
    """Fetch current rooms from the RWFC API."""
    response = requests.get(API_URL, timeout=10)
    response.raise_for_status()
    data = response.json()
    return data.get("rooms", [])


def get_room_info(room):
    """Extract relevant info from a room."""
    players = room.get("players", [])
    vr_values = [p.get("vr") for p in players if p.get("vr") is not None]
    avg_vr = sum(vr_values) / len(vr_values) if vr_values else 0

    return {
        "id": room.get("id"),
        "avg_vr": avg_vr,
        "player_count": len(players),
        "players": [p.get("name", "Unknown") for p in players],
        "is_joinable": room.get("isJoinable", False),
        "is_suspended": room.get("suspend", False),
        "room_type": room.get("rk", ""),
    }


def is_retro_tracks(room_info):
    """Check if room is Retro Tracks type."""
    return "vs" in room_info["room_type"].lower()


def get_high_vr_rooms(rooms, threshold, retro_only=False):
    """Filter and return high-VR public rooms, sorted by VR descending."""
    high_vr = []
    for room in rooms:
        if room.get("type") == "private":
            continue

        info = get_room_info(room)

        if retro_only and not is_retro_tracks(info):
            continue

        if info["avg_vr"] >= threshold:
            high_vr.append(info)

    high_vr.sort(key=lambda r: r["avg_vr"], reverse=True)
    return high_vr
