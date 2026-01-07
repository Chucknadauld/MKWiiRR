"""
MKWiiRR Room Monitor
Monitors Retro Rewind rooms for high average VR.
"""

import time
import requests

API_URL = "https://rwfc.net/api/roomstatus"

"""
VR Threshold is the MINIMUM average room VR required for a notification.
Change accordingly.
"""
VR_THRESHOLD = 35000

POLL_INTERVAL = 30  # seconds


def fetch_rooms():
    """Fetch current rooms from the RWFC API."""
    response = requests.get(API_URL, timeout=10)
    response.raise_for_status()
    data = response.json()
    return data.get("rooms", [])


def calculate_room_avg_vr(room):
    """Calculate average VR for a room. Returns None if no VR data."""
    players = room.get("players", [])
    vr_values = [p.get("vr") for p in players if p.get("vr") is not None]

    if not vr_values:
        return None
    return sum(vr_values) / len(vr_values)


def check_high_vr_rooms(rooms):
    """Find rooms with average VR above threshold."""
    high_vr_rooms = []

    for room in rooms:
        # Skip private rooms
        if room.get("type") == "private":
            continue

        avg_vr = calculate_room_avg_vr(room)
        if avg_vr and avg_vr > VR_THRESHOLD:
            players = room.get("players", [])
            high_vr_rooms.append({
                "id": room.get("id"),
                "avg_vr": avg_vr,
                "player_count": len(players),
                "players": [p.get("name", "Unknown") for p in players],
                "is_joinable": room.get("isJoinable", False),
            })

    # Sort by average VR descending
    high_vr_rooms.sort(key=lambda r: r["avg_vr"], reverse=True)
    return high_vr_rooms


def print_alert(high_vr_rooms):
    """Print alert for high VR rooms."""
    print("\n" + "=" * 50)
    print(f"HIGH VR ALERT! Found {len(high_vr_rooms)} room(s) above {VR_THRESHOLD:,} VR")
    print("=" * 50)

    for room in high_vr_rooms:
        status = "JOINABLE" if room["is_joinable"] else "NOT JOINABLE"
        print(f"\nRoom {room['id']} [{status}]")
        print(f"  Average VR: {room['avg_vr']:,.0f}")
        print(f"  Players ({room['player_count']}): {', '.join(room['players'])}")

    print()


def main():
    """Main monitoring loop."""
    print(f"Starting MKWiiRR Room Monitor")
    print(f"Threshold: {VR_THRESHOLD:,} VR | Polling every {POLL_INTERVAL}s")
    print("-" * 50)

    while True:
        try:
            rooms = fetch_rooms()
            high_vr_rooms = check_high_vr_rooms(rooms)

            if high_vr_rooms:
                print_alert(high_vr_rooms)
            else:
                timestamp = time.strftime("%H:%M:%S")
                print(f"[{timestamp}] No rooms above {VR_THRESHOLD:,} VR")

        except requests.RequestException as e:
            print(f"Error fetching rooms: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")

        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
