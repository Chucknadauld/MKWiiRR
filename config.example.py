"""
MKWiiRR Configuration
Copy this file to config.py and adjust settings as needed.
"""

# Minimum average VR to trigger alerts/display
VR_THRESHOLD = 35000

# Room stays tracked until it falls below this (notifier only)
VR_GRACE = 30000

# Seconds between API polls
POLL_INTERVAL_DASHBOARD = 15
POLL_INTERVAL_NOTIFIER = 20

# Set True to only show/track "Retro Tracks" rooms
RETRO_TRACKS_ONLY = True

# Notification toggles (notifier only)
NOTIFY_NEW_ROOM = True              # Notify when a new high-VR room is found
NOTIFY_BECAME_JOINABLE = True       # Notify when a room becomes joinable

# Dashboard toggles
SHOW_OPEN_HOSTS = True              # Show open host players with VR and friend codes

# Session tracker settings
PLAYER_FRIEND_CODE = "1760-9375-6261"  # Your friend code for session tracking
POLL_INTERVAL_SESSION = 10             # Seconds between session tracker polls
SAVE_SESSION_DATA = False              # Save session data to file for later review
SESSION_DATA_DIR = "sessions"          # Directory for saved session data (gitignored)

# Watchlist settings
# List one or more friend codes to watch; notifier will alert when they appear in a room,
# and monitor will highlight rooms containing any of them.
WATCHLIST_FRIEND_CODES = []            # e.g., ["0944-8938-8437", "3994-3199-5844"]
WATCHLIST_NOTIFY = True                # Send notifications for watchlist appearances

# Goal settings (session tracker)
#
# Leaderboard-based goal (uncomment to use)
# GOAL_LEADERBOARD_RANK = 50
# GOAL_LABEL = "Goal (Top {rank})"
GOAL_LEADERBOARD_RANK = 0  # leave 0 when using custom goal

# Custom goal (manual)
GOAL_LABEL = "For rank A"

# Optionally override the goal number shown in the session graph.
# If GOAL_TARGET_VR_TEXT is non-empty, it will be shown verbatim (e.g., "59.6k").
# Else if GOAL_TARGET_VR is a positive integer, that value will be shown (with commas).
# Otherwise, the app will fetch the VR for GOAL_LEADERBOARD_RANK from the API.
GOAL_TARGET_VR = 0
GOAL_TARGET_VR_TEXT = ""
