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
# NOTIFICATION FUNCTIONS - Replace these to change notification method
# =============================================================================


def _notify(title, message):
    """Send a macOS notification using terminal-notifier."""
    subprocess.run(
        ["terminal-notifier", "-title", title, "-message", message, "-sound", "default"],
        check=False,
    )


def notify_new_room(all_rooms):
    """Notify when a new high-VR room is found."""
    # Terminal output
    print("\n" + "=" * 55)
    print("NEW HIGH-VR ROOM FOUND!")
    print("=" * 55)
    for r in all_rooms:
        joinable = "JOINABLE" if r["is_joinable"] else "NOT JOINABLE"
        print(f"\nRoom {r['id']} [{joinable}]")
        print(f"  Average VR: {r['avg_vr']:,.0f}")
        print(f"  Players ({r['player_count']}): {', '.join(r['players'])}")
    print("=" * 55 + "\n")

    # macOS notification
    top_room = all_rooms[0]
    room_count = len(all_rooms)
    title = f"Room Above {VR_THRESHOLD // 1000}k VR!"
    msg = f"{top_room['avg_vr']:,.0f} avg • {top_room['player_count']}p"
    if room_count > 1:
        msg += f" (+{room_count - 1} more)"
    _notify(title, msg)


def notify_became_joinable(room):
    """Notify when a tracked room becomes joinable."""
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


def main():
    """Main notification loop."""
    print("MKWiiRR Smart Notifier")
    print(f"Threshold: {VR_THRESHOLD:,} VR | Grace: {VR_GRACE:,} VR | Poll: {POLL_INTERVAL}s")
    if RETRO_TRACKS_ONLY:
        print("Filter: Retro Tracks only")
    print("-" * 55)
    print("Waiting for high-VR rooms...\n")

    tracked = {}  # room_id -> room_info

    try:
        while True:
            try:
                rooms = fetch_rooms()
                current = {}

                for room in rooms:
                    if room.get("type") == "private":
                        continue

                    info = get_room_info(room)

                    if RETRO_TRACKS_ONLY and not is_retro_tracks(info):
                        continue

                    # Use grace threshold if already tracked, otherwise main threshold
                    threshold = VR_GRACE if info["id"] in tracked else VR_THRESHOLD
                    if info["avg_vr"] >= threshold:
                        current[info["id"]] = info

                # Check for new rooms
                if NOTIFY_NEW_ROOM:
                    new_found = any(rid not in tracked for rid in current)
                    if new_found:
                        notify_new_room(sorted(current.values(), key=lambda r: r["avg_vr"], reverse=True))

                # Check for rooms that became joinable
                if NOTIFY_BECAME_JOINABLE:
                    for rid, old in tracked.items():
                        if rid in current and not old["is_joinable"] and current[rid]["is_joinable"]:
                            notify_became_joinable(current[rid])

                tracked = current

            except Exception as e:
                print(f"[Error: {e}]")

            time.sleep(POLL_INTERVAL)

    except KeyboardInterrupt:
        print("\n\nNotifier stopped.")


if __name__ == "__main__":
    main()
