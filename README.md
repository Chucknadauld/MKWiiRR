# MKWiiRR - Mario Kart Wii Retro Rewind Monitor

A Python tool for monitoring Mario Kart Wii Retro Rewind online rooms.

## Setup

```bash
pip install requests
cp config.example.py config.py
```

## Usage

**Dashboard** - Live display of high-VR rooms (updates in-place):
```bash
python monitor.py
```

**Notifier** - Alerts when new high-VR rooms appear or become joinable:
```bash
python notifier.py
```

## Configuration

Edit `config.py` to customize:

| Setting | Default | Description |
|---------|---------|-------------|
| `VR_THRESHOLD` | 35000 | Minimum avg VR to trigger alerts/display |
| `VR_GRACE` | 30000 | Room stays tracked until falling below this |
| `POLL_INTERVAL_DASHBOARD` | 5 | Seconds between dashboard polls |
| `POLL_INTERVAL_NOTIFIER` | 10 | Seconds between notifier polls |
| `RETRO_TRACKS_ONLY` | False | Only show/track Retro Tracks rooms |
| `NOTIFY_NEW_ROOM` | True | Notify on new high-VR room |
| `NOTIFY_BECAME_JOINABLE` | True | Notify when room becomes joinable |
| `SHOW_OPEN_HOSTS` | False | Show open host players with VR and friend codes |

## Features

- Live dashboard with real-time room status
- Smart notifications (only alerts on state changes)
- Grace period tracking (rooms stay tracked between threshold and grace)
- Configurable thresholds and toggles
