"""
MKWiiRR Core
Shared functions for RWFC API access with process-safe caching.
"""

import json
import os
import random
import time
import requests
import fcntl
from contextlib import contextmanager


def sleep_with_jitter(interval, jitter_percent=0.1):
    """
    Sleep for interval +/- random jitter to prevent thundering herd.
    
    Args:
        interval: Base sleep time in seconds
        jitter_percent: Max jitter as fraction of interval (default 10%)
    """
    jitter = random.uniform(-interval * jitter_percent, interval * jitter_percent)
    time.sleep(interval + jitter)

API_URL = "https://rwfc.net/api/roomstatus"

# -----------------------------------------------------------------------------
# Improved disk-based shared cache with file locking + backoff
# -----------------------------------------------------------------------------
_CACHE_DIR = os.path.join(os.path.dirname(__file__), ".cache")
_ROOMS_KEY = "roomstatus"
_GROUPS_KEY = "groups"

# Cache TTLs optimized for polling intervals
# - roomstatus: 8s (covers 6s monitor polling with buffer)
# - groups: 8s (same, used by session tracker)
# - leaderboard: 300s (rarely changes, reduce API load)
_TTL_ROOMS_SECONDS = 8
_TTL_GROUPS_SECONDS = 8
_TTL_LEADERBOARD_SECONDS = 300

# Backoff settings
_BACKOFF_INITIAL_SECONDS = 10
_BACKOFF_MAX_SECONDS = 120


def _ensure_cache_dir():
    """Create cache directory if it doesn't exist."""
    try:
        os.makedirs(_CACHE_DIR, exist_ok=True)
    except Exception:
        pass


@contextmanager
def _file_lock(path):
    """Context manager for file locking to prevent concurrent fetches."""
    lock_path = f"{path}.lock"
    _ensure_cache_dir()
    lock_file = None
    try:
        lock_file = open(lock_path, 'w')
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        yield
    finally:
        if lock_file:
            try:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
                lock_file.close()
            except Exception:
                pass
            try:
                os.remove(lock_path)
            except Exception:
                pass


def _cache_paths(key: str):
    """Return paths for cache data and backoff files."""
    _ensure_cache_dir()
    data_path = os.path.join(_CACHE_DIR, f"{key}.json")
    backoff_path = os.path.join(_CACHE_DIR, f"{key}.backoff")
    return data_path, backoff_path


def _read_json_file(path: str):
    """Read JSON file safely."""
    try:
        with open(path, "r") as f:
            return json.load(f)
    except Exception:
        return None


def _write_json_atomic(path: str, payload):
    """Write JSON atomically using temp file + rename."""
    try:
        tmp = f"{path}.tmp"
        with open(tmp, "w") as f:
            json.dump(payload, f)
        os.replace(tmp, path)
    except Exception:
        pass


def _mtime(path: str):
    """Get file modification time, or 0 if file doesn't exist."""
    try:
        return os.path.getmtime(path)
    except Exception:
        return 0


def _read_backoff_until(backoff_path: str):
    """Read backoff timestamp from file."""
    try:
        with open(backoff_path, "r") as f:
            val = f.read().strip()
            return float(val) if val else 0.0
    except Exception:
        return 0.0


def _write_backoff_until(backoff_path: str, until_ts: float):
    """Write backoff timestamp to file."""
    try:
        with open(backoff_path, "w") as f:
            f.write(str(until_ts))
    except Exception:
        pass


def _clear_backoff(backoff_path: str):
    """Clear backoff file after successful fetch."""
    try:
        if os.path.exists(backoff_path):
            os.remove(backoff_path)
    except Exception:
        pass


def _fetch_with_cache(url: str, key: str, ttl_seconds: int):
    """
    Shared cached fetch with file locking and exponential backoff.
    
    - Returns cached data if fresh (within TTL)
    - Uses file locking to prevent multiple processes from fetching simultaneously
    - Implements exponential backoff on 429 errors
    - Falls back to stale cache if fetch fails
    """
    data_path, backoff_path = _cache_paths(key)
    now = time.time()

    # Check if we're in backoff period
    backoff_until = _read_backoff_until(backoff_path)
    if backoff_until and now < backoff_until:
        # In backoff - return cached data if available
        cached = _read_json_file(data_path)
        if cached is not None:
            return cached
        # No cache available, wait a bit and try anyway
        time.sleep(min(2, backoff_until - now))

    # Check if cache is fresh
    cache_age = now - _mtime(data_path)
    if cache_age < ttl_seconds:
        cached = _read_json_file(data_path)
        if cached is not None:
            return cached

    # Cache is stale or missing - need to fetch
    # Use file locking to ensure only one process fetches at a time
    with _file_lock(data_path):
        # Double-check cache freshness after acquiring lock
        # (another process might have just updated it)
        cache_age = now - _mtime(data_path)
        if cache_age < ttl_seconds:
            cached = _read_json_file(data_path)
            if cached is not None:
                return cached

        # Fetch from network
        try:
            response = requests.get(url, timeout=10)
            
            if response.status_code == 429:
                # Rate limited - implement exponential backoff
                current_backoff = backoff_until - now if (backoff_until and now < backoff_until) else 0
                if current_backoff <= 0:
                    delay = _BACKOFF_INITIAL_SECONDS
                else:
                    delay = min(_BACKOFF_MAX_SECONDS, current_backoff * 2)
                
                # Add jitter to prevent thundering herd
                jitter = random.uniform(0, delay * 0.2)
                total_delay = delay + jitter
                
                _write_backoff_until(backoff_path, now + total_delay)
                
                # Return stale cache if available
                cached = _read_json_file(data_path)
                if cached is not None:
                    return cached
                
                # No cache - raise the error
                response.raise_for_status()

            response.raise_for_status()
            data = response.json()
            
            # Success - write to cache and clear backoff
            _write_json_atomic(data_path, data)
            _clear_backoff(backoff_path)
            
            return data
            
        except requests.exceptions.RequestException:
            # Network error - return stale cache if available
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
    # Sort by VR descending
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
