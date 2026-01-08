"""
MKWiiRR Smart Notifier
Sends notifications for high-VR room events.
"""

import subprocess
import time
import sys

try:
    from config import (
        VR_THRESHOLD, VR_GRACE, POLL_INTERVAL_NOTIFIER as POLL_INTERVAL,
        RETRO_TRACKS_ONLY, NOTIFY_NEW_ROOM, NOTIFY_BECAME_JOINABLE
    )
except ImportError:
    print("Error: config.py not found. Copy config.example.py to config.py")
    sys.exit(1)

from core import fetch_rooms, get_room_info, is_retro_tracks

# =============================================================================
# NOTIFICATION FUNCTIONS
# =============================================================================


def _notify(title, message):
    """Send a macOS notification using terminal-notifier."""
    subprocess.run(
        ["terminal-notifier", "-title", title, "-message", message, "-sound", "Glass"],
        check=False,
    )


def notify_new_room(room):
    """Notify when a room crosses above VR_THRESHOLD."""
    joinable = "JOINABLE" if room["is_joinable"] else "NOT JOINABLE"
    
    # Terminal output
    print("\n" + "=" * 55)
    print(f"ROOM HIT {VR_THRESHOLD:,}+ VR!")
    print("=" * 55)
    print(f"Room {room['id']} [{joinable}]")
    print(f"  Average VR: {room['avg_vr']:,.0f}")
    print(f"  Players ({room['player_count']}): {', '.join(room['players'])}")
    print("=" * 55 + "\n")

    # macOS notification
    title = f"Room Above {VR_THRESHOLD // 1000}k VR!"
    msg = f"{room['avg_vr']:,.0f} avg • {room['player_count']}p"
    _notify(title, msg)


def notify_became_joinable(room):
    """Notify when a tracked room becomes joinable (was 12p, now fewer)."""
    # Terminal output
    print("\n" + "=" * 55)
    print(f"ROOM {room['id']} IS NOW JOINABLE!")
    print("=" * 55)
    print(f"  Average VR: {room['avg_vr']:,.0f}")
    print(f"  Players ({room['player_count']}): {', '.join(room['players'])}")
    print("=" * 55 + "\n")

    # macOS notification
    title = "Room Now Joinable!"
    msg = f"{room['avg_vr']:,.0f} VR avg • {room['player_count']}p"
    _notify(title, msg)


# =============================================================================
# MAIN LOOP
# =============================================================================

def main():
    """Main notification loop."""
    print("MKWiiRR Smart Notifier")
    print(f"Threshold: {VR_THRESHOLD:,} VR | Grace: {VR_GRACE:,} VR | Poll: {POLL_INTERVAL}s")
    if RETRO_TRACKS_ONLY:
        print("Filter: Retro Tracks only")
    print("-" * 55)
    print("Waiting for high-VR rooms...\n")

    # tracked[room_id] = {
    #     "above_threshold": bool,  # True if room is at/above VR_THRESHOLD
    #     "player_count": int,
    #     "notified": bool,         # True if we've notified for this threshold crossing
    # }
    tracked = {}

    try:
        while True:
            try:
                rooms = fetch_rooms()

                for room in rooms:
                    if room.get("type") == "private":
                        continue

                    info = get_room_info(room)
                    rid = info["id"]

                    # Apply retro tracks filter
                    if RETRO_TRACKS_ONLY and not is_retro_tracks(info):
                        continue

                    avg_vr = info["avg_vr"]
                    player_count = info["player_count"]

                    # Case 1: Room not tracked yet
                    if rid not in tracked:
                        if avg_vr >= VR_THRESHOLD:
                            # New room above threshold - notify and track
                            if NOTIFY_NEW_ROOM:
                                notify_new_room(info)
                            tracked[rid] = {
                                "above_threshold": True,
                                "player_count": player_count,
                                "notified": True,
                            }
                        # If below threshold, don't track it at all
                        continue

                    # Case 2: Room is already tracked
                    prev = tracked[rid]

                    # Check if room dropped below grace period - stop tracking
                    if avg_vr < VR_GRACE:
                        del tracked[rid]
                        continue

                    # Check if room crossed UP to threshold (was in grace zone, now above)
                    if NOTIFY_NEW_ROOM and not prev["above_threshold"] and avg_vr >= VR_THRESHOLD:
                        notify_new_room(info)
                        prev["notified"] = True

                    # Update threshold status
                    prev["above_threshold"] = avg_vr >= VR_THRESHOLD

                    # Check if room became joinable (was 12p, now fewer)
                    if NOTIFY_BECAME_JOINABLE and prev["player_count"] == 12 and player_count < 12:
                        notify_became_joinable(info)

                    # Update player count
                    prev["player_count"] = player_count

                # Clean up rooms that no longer exist in API response
                current_ids = set()
                for room in rooms:
                    if room.get("type") != "private":
                        info = get_room_info(room)
                        if not RETRO_TRACKS_ONLY or is_retro_tracks(info):
                            current_ids.add(info["id"])
                
                for rid in list(tracked.keys()):
                    if rid not in current_ids:
                        del tracked[rid]

            except Exception as e:
                print(f"[Error: {e}]")

            time.sleep(POLL_INTERVAL)

    except KeyboardInterrupt:
        print("\n\nNotifier stopped.")


if __name__ == "__main__":
    main()