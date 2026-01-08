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

    # Extract open host players with their VR and friend codes
    open_hosts = []
    for p in players:
        if p.get("isOpenHost", False):
            open_hosts.append({
                "name": p.get("name", "Unknown"),
                "vr": p.get("vr", 0),
                "fc": p.get("friendCode", ""),
            })
    # Sort by VR descending (treat None as 0)
    open_hosts.sort(key=lambda x: x["vr"] or 0, reverse=True)

    return {
        "id": room.get("id"),
        "avg_vr": avg_vr,
        "player_count": len(players),
        "players": [p.get("name", "Unknown") for p in players],
        "open_hosts": open_hosts,
        "is_joinable": room.get("isJoinable", False),
        "is_suspended": room.get("suspend", False),
        "room_type": room.get("rk", ""),
        "room_label": room.get("roomType", ""),
    }


def is_retro_tracks(room_info):
    """Check if room is Retro Tracks type."""
    label = (room_info.get("room_label") or "").strip().lower()
    if label:
        return label == "retro tracks"
    return False


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


def find_player_room(rooms, friend_code):
    """Find the room containing a player with the given friend code.
    Returns (room_info, player_info) or (None, None) if not found.
    """
    for room in rooms:
        players = room.get("players", [])
        for player in players:
            if player.get("friendCode") == friend_code:
                return get_room_info(room), player
    return None, None


def fetch_player_info(friend_code):
    """Fetch player info from leaderboard API."""
    url = f"https://rwfc.net/api/leaderboard/player/{friend_code}"
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    return response.json()


def fetch_player_history(friend_code, count=50):
    """Fetch player's recent VR history."""
    url = f"https://rwfc.net/api/leaderboard/player/{friend_code}/history/recent?count={count}"
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    return response.json()


def fetch_groups():
    """Fetch raw groups data (faster VR updates than roomstatus)."""
    response = requests.get("http://rwfc.net/api/groups", timeout=10)
    response.raise_for_status()
    return response.json()


def find_player_in_groups(friend_code):
    """Find player in groups and return their live VR.
    Returns (room_id, player_data) or (None, None) if not found.
    """
    groups = fetch_groups()
    for group in groups:
        players = group.get("players", {})
        for pid, player in players.items():
            if player.get("fc") == friend_code:
                return group.get("id"), player
    return None, None