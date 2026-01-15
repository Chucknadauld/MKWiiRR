"""
MKWiiRR Room Dashboard
Live terminal display of high-VR Retro Rewind rooms.
"""

import time
import sys

try:
    from config import VR_THRESHOLD, POLL_INTERVAL_DASHBOARD as POLL_INTERVAL, RETRO_TRACKS_ONLY, SHOW_OPEN_HOSTS, WATCHLIST_FRIEND_CODES, PLAYER_FRIEND_CODE, WATCHLIST
except ImportError:
    print("Error: config.py not found. Copy config.example.py to config.py")
    sys.exit(1)

from core import fetch_rooms, get_high_vr_rooms, find_player_in_groups


def clear_lines(n):
    """Clear n lines above cursor."""
    for _ in range(n):
        sys.stdout.write("\033[A")
        sys.stdout.write("\033[K")
    sys.stdout.flush()


def _format_room_line(room):
    joinable = "Yes" if room["is_joinable"] else "No"
    suspended = "Yes" if room["is_suspended"] else "No"
    return (
        f"  {room['id']:<10} | VR: {room['avg_vr']:>7,.0f} | "
        f"{room['player_count']:>2}p | Joinable: {joinable:<3} | Suspended: {suspended:<3}"
    )


def _format_host_lines(room):
    lines = []
    if SHOW_OPEN_HOSTS and room["open_hosts"]:
        for host in room["open_hosts"]:
            lines.append(
                f"    ↳ {host['name']:<12} | VR: {host['vr']:>7,} | FC: {host['fc']}"
            )
    return lines


def print_dashboard(rooms, lines_printed, last_signature, current_room_id=None, watchlist_section=None):
    """Print live dashboard only when content changes.
    Returns (lines_printed, new_signature).
    """
    # Build stable content (signature) without the timestamp
    stable_lines = []
    if current_room_id:
        stable_lines.append(f"You: {current_room_id}")
    if not rooms:
        stable_lines.append(f"No rooms above {VR_THRESHOLD:,} VR")
    else:
        stable_lines.append(f"{len(rooms)} high-VR room(s)")
        for idx, room in enumerate(rooms):
            stable_lines.append(_format_room_line(room))
            stable_lines.extend(_format_host_lines(room))
            if idx < len(rooms) - 1:
                stable_lines.append("")  # blank line between rooms
    # Append watchlist section
    if watchlist_section is not None:
        stable_lines.append("")
        stable_lines.extend(watchlist_section)

    signature = "\n".join(stable_lines)

    # No change: keep the dashboard untouched
    if signature == last_signature:
        return lines_printed, last_signature

    # Change detected: re-render with timestamp
    if lines_printed > 0:
        clear_lines(lines_printed)

    timestamp = time.strftime("%I:%M:%S %p")

    display_lines = []
    if not rooms:
        display_lines.append(f"[{timestamp}] No rooms above {VR_THRESHOLD:,} VR")
    else:
        if current_room_id:
            display_lines.append(f"You: {current_room_id}")
        display_lines.append(f"━━━ {len(rooms)} high-VR room(s) | {timestamp} ━━━")
        display_lines.append("")  # blank line after header
        for idx, room in enumerate(rooms):
            display_lines.append(_format_room_line(room))
            display_lines.extend(_format_host_lines(room))
            if idx < len(rooms) - 1:
                display_lines.append("")  # blank line between rooms
        # Append watchlist section for display
        if watchlist_section is not None:
            display_lines.append("")
            display_lines.extend(watchlist_section)

    for line in display_lines:
        print(line)

    return len(display_lines), signature


def main():
    """Main dashboard loop."""
    print("MKWiiRR Room Dashboard")
    print(f"Threshold: {VR_THRESHOLD:,} VR")
    if RETRO_TRACKS_ONLY:
        print("Filter: Retro Tracks only")
    if SHOW_OPEN_HOSTS:
        print("Showing: Open hosts with VR and friend codes")
    print("-" * 50)

    lines_printed = 0
    last_signature = None

    try:
        while True:
            try:
                rooms = fetch_rooms()
                high_vr_rooms = get_high_vr_rooms(rooms, VR_THRESHOLD, RETRO_TRACKS_ONLY)
                # Compute current room
                current_room_id, _ = find_player_in_groups(PLAYER_FRIEND_CODE)
                # Build independent Watchlist section (regardless of VR/room type)
                wl_map = WATCHLIST or {}
                wl_set = set(WATCHLIST_FRIEND_CODES) | set(wl_map.keys())
                watchlist_lines = ["Watchlist"]
                online = []
                if wl_set:
                    for r in rooms:
                        if r.get("type") == "private":
                            continue
                        rid = r.get("id")
                        # Compute average VR for the room
                        vr_values = [p.get("vr") for p in r.get("players", []) if isinstance(p.get("vr"), (int, float))]
                        avg_vr = int(sum(vr_values) / len(vr_values)) if vr_values else 0
                        for p in r.get("players", []):
                            fc = p.get("friendCode")
                            if fc and fc in wl_set:
                                nickname = wl_map.get(fc)
                                name = nickname or p.get("name", "Unknown")
                                online.append(f"  {name} ({fc}) — Room {rid} - Avg VR {avg_vr:,}")
                if online:
                    watchlist_lines.extend(online)
                else:
                    watchlist_lines.append("  No watchlist players online")
                lines_printed, last_signature = print_dashboard(high_vr_rooms, lines_printed, last_signature, current_room_id, watchlist_lines)

            except Exception as e:
                if lines_printed > 0:
                    clear_lines(lines_printed)
                print(f"[Error: {e}]")
                lines_printed = 1
                # Force a redraw on next successful poll so the error line gets cleared
                last_signature = None

            time.sleep(POLL_INTERVAL)

    except KeyboardInterrupt:
        print("\n\nDashboard stopped.")


if __name__ == "__main__":
    main()
