"""
MKWiiRR Room Dashboard
Live terminal display of high-VR Retro Rewind rooms.
"""

import time
import sys

try:
    from config import VR_THRESHOLD, POLL_INTERVAL_DASHBOARD as POLL_INTERVAL, RETRO_TRACKS_ONLY, SHOW_OPEN_HOSTS
except ImportError:
    print("Error: config.py not found. Copy config.example.py to config.py")
    sys.exit(1)

from core import fetch_rooms, get_high_vr_rooms


def clear_lines(n):
    """Clear n lines above cursor."""
    for _ in range(n):
        sys.stdout.write("\033[A")
        sys.stdout.write("\033[K")


def print_dashboard(rooms, lines_printed):
    """Print live dashboard. Returns number of lines printed."""
    if lines_printed > 0:
        clear_lines(lines_printed)

    timestamp = time.strftime("%H:%M:%S")

    if not rooms:
        print(f"[{timestamp}] No rooms above {VR_THRESHOLD:,} VR")
        return 1

    lines = [f"━━━ {len(rooms)} high-VR room(s) | {timestamp} ━━━"]

    for room in rooms:
        joinable = "JOINABLE" if room["is_joinable"] else "NOT JOINABLE"
        suspended = "SUSPENDED" if room["is_suspended"] else "UNSUSPENDED"
        lines.append(f"  {room['id']}: {room['avg_vr']:,.0f} VR | {room['player_count']}p | {joinable} | {suspended}")

        if SHOW_OPEN_HOSTS and room["open_hosts"]:
            for host in room["open_hosts"]:
                lines.append(f"    ↳ {host['name']} | {host['vr']:,} VR | {host['fc']}")

    lines.append(f"━━━ Threshold: {VR_THRESHOLD:,} | Poll: {POLL_INTERVAL}s ━━━")

    for line in lines:
        print(line)

    return len(lines)


def main():
    """Main dashboard loop."""
    print("MKWiiRR Room Dashboard")
    print(f"Threshold: {VR_THRESHOLD:,} VR | Poll: {POLL_INTERVAL}s")
    if RETRO_TRACKS_ONLY:
        print("Filter: Retro Tracks only")
    if SHOW_OPEN_HOSTS:
        print("Showing: Open hosts with VR and friend codes")
    print("-" * 50 + "\n")

    lines_printed = 0

    try:
        while True:
            try:
                rooms = fetch_rooms()
                high_vr_rooms = get_high_vr_rooms(rooms, VR_THRESHOLD, RETRO_TRACKS_ONLY)
                lines_printed = print_dashboard(high_vr_rooms, lines_printed)

            except Exception as e:
                if lines_printed > 0:
                    clear_lines(lines_printed)
                print(f"[Error: {e}]")
                lines_printed = 1

            time.sleep(POLL_INTERVAL)

    except KeyboardInterrupt:
        print("\n\nDashboard stopped.")


if __name__ == "__main__":
    main()
