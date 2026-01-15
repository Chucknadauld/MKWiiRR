# MKWiiRR - Mario Kart Wii Retro Rewind Monitor

A Python tool for monitoring Mario Kart Wii Retro Rewind online rooms.

## Setup

```bash
pip install requests
brew install terminal-notifier  # macOS notifications
cp config.example.py config.py
```

## Usage

### Dashboard

Live display of high-VR rooms (updates in-place):

```bash
python monitor.py
```
The dashboard shows:
- Your current room at the top (based on `PLAYER_FRIEND_CODE`)
- High‑VR rooms
- A Watchlist section at the bottom listing friends online (name/nickname and FC), regardless of room type or average VR
  - If none are online, it shows “No watchlist players online”

### Notifier

Alerts when rooms hit VR threshold or become joinable:

```bash
python notifier.py
```
In addition to VR threshold alerts, the notifier can alert when any watchlisted friend codes are seen in a room (once per friend per room) using `WATCHLIST_NOTIFY`.

Run notifier in background (keeps running after closing terminal):

```bash
nohup python3 notifier.py >> ~/mkwii_notify.log 2>&1 &
```

### Session Tracker

Track your VR gains/losses during a play session with a live-updating graph:

```bash
python session.py
```

Then open `session_graph.html` in your browser for a live-updating graph of your session.

**Features:**

- Tracks VR changes race-by-race
- Live-updating HTML graph (auto-refreshes every 5 seconds)
- Shows net VR change, average per race, race count
- Automatically resets session when you switch rooms
- Optionally saves session data to JSON for later review

## Configuration

Edit `config.py` to customize:

| Setting                   | Default        | Description                                     |
| ------------------------- | -------------- | ----------------------------------------------- |
| `VR_THRESHOLD`            | 35000          | Minimum avg VR to trigger alerts/display        |
| `VR_GRACE`                | 30000          | Room stays tracked until falling below this     |
| `POLL_INTERVAL_DASHBOARD` | 5              | Seconds between dashboard polls                 |
| `POLL_INTERVAL_NOTIFIER`  | 10             | Seconds between notifier polls                  |
| `RETRO_TRACKS_ONLY`       | False          | Only show/track Retro Tracks rooms              |
| `NOTIFY_NEW_ROOM`         | True           | Notify when room hits VR threshold              |
| `NOTIFY_BECAME_JOINABLE`  | True           | Notify when room becomes joinable (12p → fewer) |
| `SHOW_OPEN_HOSTS`         | False          | Show open host players with VR and friend codes |
| `PLAYER_FRIEND_CODE`      | 1760-9375-6261 | Your friend code for session tracking           |
| `POLL_INTERVAL_SESSION`   | 10             | Seconds between session tracker polls           |
| `SAVE_SESSION_DATA`       | False          | Save session data to JSON files                 |
| `SESSION_DATA_DIR`        | sessions       | Directory for saved session data (gitignored)   |
| `WATCHLIST_FRIEND_CODES`  | []             | List of FCs to watch for                        |
| `WATCHLIST`               | {}             | Optional map of FC -> Nickname                  |
| `WATCHLIST_NOTIFY`        | True           | Notify when any watchlisted FC appears          |
| `GOAL_LEADERBOARD_RANK`   | 0              | Rank to fetch target VR for (0 to disable)      |
| `GOAL_LABEL`              | "For rank A"   | Label for the goal box (supports `{rank}`)      |
| `GOAL_TARGET_VR`          | 0              | If > 0, overrides goal VR number                |
| `GOAL_TARGET_VR_TEXT`     | ""             | If set, overrides the goal VR text verbatim     |

## Background Commands

**Check if notifier is running:**

```bash
pgrep -f notifier.py
```

**Stop background notifier:**

```bash
pkill -f notifier.py
```

**View log:**

```bash
tail -f ~/mkwii_notify.log
```

## Features

- Live dashboard with real-time room status
- Background notifications that persist after closing terminal
- Smart notifications: alerts when rooms cross threshold, not on every poll
- Grace period tracking: rooms stay tracked between threshold and grace
- Joinable alerts: notifies when full rooms get an open slot
- Session tracking with VR graph and statistics
