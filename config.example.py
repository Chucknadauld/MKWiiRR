"""
MKWiiRR Configuration
Copy this file to config.py and adjust settings as needed.
"""

# Minimum average VR to trigger alerts/display
VR_THRESHOLD = 35000

# Room stays tracked until it falls below this (notifier only)
VR_GRACE = 30000

# Seconds between API polls
POLL_INTERVAL_DASHBOARD = 5
POLL_INTERVAL_NOTIFIER = 10

# Set True to only show/track "Retro Tracks" rooms
RETRO_TRACKS_ONLY = False

# Notification toggles (notifier only)
NOTIFY_NEW_ROOM = True              # Notify when a new high-VR room is found
NOTIFY_BECAME_JOINABLE = True       # Notify when a room becomes joinable

# Dashboard toggles
SHOW_OPEN_HOSTS = False             # Show open host players with VR and friend codes

# Session tracker settings
PLAYER_FRIEND_CODE = "1760-9375-6261"  # Your friend code for session tracking
POLL_INTERVAL_SESSION = 10             # Seconds between session tracker polls
SAVE_SESSION_DATA = False              # Save session data to file for later review
SESSION_DATA_DIR = "sessions"          # Directory for saved session data (gitignored)
