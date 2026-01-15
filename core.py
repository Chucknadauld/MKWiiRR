"""
MKWiiRR Core
Shared functions for RWFC API access.
"""

import json
import os
import random
import time
import requests

API_URL = "https://rwfc.net/api/roomstatus"

# -----------------------------------------------------------------------------
# Simple disk-based shared cache + 429 backoff
# -----------------------------------------------------------------------------
_CACHE_DIR = os.path.join(os.path.dirname(__file__), ".cache")
_ROOMS_KEY = "roomstatus"
_GROUPS_KEY = "groups"

_TTL_ROOMS_SECONDS = 5
_TTL_GROUPS_SECONDS = 5
_TTL_LEADERBOARD_SECONDS = 300

_BACKOFF_INITIAL_SECONDS = 5
_BACKOFF_MAX_SECONDS = 60


def _ensure_cache_dir():
    try:
        os.makedirs(_CACHE_DIR, exist_ok=True)
    except Exception:
        pass


def _cache_paths(key: str):
    _ensure_cache_dir()
    data_path = os.path.join(_CACHE_DIR, f"{key}.json")
    backoff_path = os.path.join(_CACHE_DIR, f"{key}.backoff")
    return data_path, backoff_path


def _read_json_file(path: str):
    try:
        with open(path, "r") as f:
            return json.load(f)
    except Exception:
        return None


def _write_json_atomic(path: str, payload):
    try:
        tmp = f"{path}.tmp"
        with open(tmp, "w") as f:
            json.dump(payload, f)
        os.replace(tmp, path)
    except Exception:
        pass


def _mtime(path: str):
    try:
        return os.path.getmtime(path)
    except Exception:
        return 0


def _read_backoff_until(backoff_path: str):
    try:
        with open(backoff_path, "r") as f:
            val = f.read().strip()
            return float(val) if val else 0.0
    except Exception:
        return 0.0


def _write_backoff_until(backoff_path: str, until_ts: float):
    try:
        with open(backoff_path, "w") as f:
            f.write(str(until_ts))
    except Exception:
        pass


def _clear_backoff(backoff_path: str):
    try:
        if os.path.exists(backoff_path):
            os.remove(backoff_path)
    except Exception:
        pass


def _fetch_with_cache(url: str, key: str, ttl_seconds: int):
    """
    Shared cached fetch with backoff handling.
    - Returns cached data if fresh.
    - On 429: sets backoff and returns cached data if any.
    - On other errors: returns cached data if any.
    """
    data_path, backoff_path = _cache_paths(key)
    now = time.time()

    # Respect backoff if present
    backoff_until = _read_backoff_until(backoff_path)
    if backoff_until and now < backoff_until:
        cached = _read_json_file(data_path)
        if cached is not None:
            return cached
        # If no cache, try fetch anyway (last resort)

    # Use fresh cache
    if (now - _mtime(data_path)) < ttl_seconds:
        cached = _read_json_file(data_path)
        if cached is not None:
            return cached

    # Fetch from network
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 429:
            prev = max(0.0, backoff_until - now) if backoff_until and now < backoff_until else 0.0
            base = _BACKOFF_INITIAL_SECONDS if prev <= 0 else min(_BACKOFF_MAX_SECONDS, prev * 2)
            jitter = random.uniform(0, 2)
            delay = min(_BACKOFF_MAX_SECONDS, base + jitter)
            _write_backoff_until(backoff_path, now + delay)
            cached = _read_json_file(data_path)
            if cached is not None:
                return cached
            response.raise_for_status()

        response.raise_for_status()
        data = response.json()
        _write_json_atomic(data_path, data)
        _clear_backoff(backoff_path)
        return data
    except Exception:
        cached = _read_json_file(data_path)
        if cached is not None:
            return cached
        raise


def fetch_rooms():
    """Fetch current rooms from the RWFC API (shared cache)."""
    data = _fetch_with_cache(API_URL, _ROOMS_KEY, _TTL_ROOMS_SECONDS)
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
    url = "http://rwfc.net/api/groups"
    data = _fetch_with_cache(url, _GROUPS_KEY, _TTL_GROUPS_SECONDS)
    return data


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


def fetch_leaderboard_top(count=50):
    """Fetch top N players by VR."""
    url = f"https://rwfc.net/api/leaderboard/top/{int(count)}"
    key = f"leaderboard_top_{int(count)}"
    data = _fetch_with_cache(url, key, _TTL_LEADERBOARD_SECONDS)
    return data


def get_goal_vr_for_rank(rank):
    """Return the VR value at the given leaderboard rank (1-based)."""
    try:
        rank = int(rank)
        if rank <= 0:
            return None
        top = fetch_leaderboard_top(rank)
        # Prefer exact rank match if provided by API
        for p in top:
            if str(p.get("rank")) == str(rank):
                return int(p.get("vr", 0))
        # Fallback: assume last entry is the desired rank
        if top:
            return int(top[-1].get("vr", 0))
    except Exception:
        return None
    return None