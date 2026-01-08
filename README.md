# MKWiiRR - Mario Kart Wii Retro Rewind Monitor

A Python tool for monitoring Mario Kart Wii Retro Rewind online rooms.

## Setup

```bash
pip install requests
brew install terminal-notifier
cp config.example.py config.py
```

## Usage

**Dashboard** - Live display of high-VR rooms (updates in-place):

```bash
python monitor.py
```

**Notifier** - Alerts when rooms hit VR threshold or become joinable:

```bash
python notifier.py
```

**Run notifier in background** (keeps running after closing terminal):

```bash
cd ~/Documents/Github/MKWIIrr
nohup python3 notifier.py >> ~/mkwii_notify.log 2>&1 &
```

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

## Configuration

Edit `config.py` to customize:

| Setting                   | Default | Description                                     |
| ------------------------- | ------- | ----------------------------------------------- |
| `VR_THRESHOLD`            | 35000   | Minimum avg VR to trigger alerts/display        |
| `VR_GRACE`                | 30000   | Room stays tracked until falling below this     |
| `POLL_INTERVAL_DASHBOARD` | 5       | Seconds between dashboard polls                 |
| `POLL_INTERVAL_NOTIFIER`  | 10      | Seconds between notifier polls                  |
| `RETRO_TRACKS_ONLY`       | False   | Only show/track Retro Tracks rooms              |
| `NOTIFY_NEW_ROOM`         | True    | Notify when room hits VR threshold              |
| `NOTIFY_BECAME_JOINABLE`  | True    | Notify when room becomes joinable (12p → fewer) |
| `SHOW_OPEN_HOSTS`         | False   | Show open host players with VR and friend codes |

## Features

- Live dashboard with real-time room status
- Background notifications that persist after closing terminal
- Smart notifications: alerts when rooms cross threshold, not on every poll
- Grace period tracking: rooms stay tracked between threshold and grace
- Joinable alerts: notifies when full rooms get an open slot
