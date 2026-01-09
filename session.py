"""
MKWiiRR Session Tracker
Tracks your VR gains/losses during a play session with a live-updating graph.
Simply polls /api/groups and detects VR changes.
"""

import json
import os
import time
import sys
from datetime import datetime

try:
    from config import (
        PLAYER_FRIEND_CODE, POLL_INTERVAL_SESSION as POLL_INTERVAL,
        SAVE_SESSION_DATA, SESSION_DATA_DIR
    )
except ImportError:
    print("Error: config.py not found. Copy config.example.py to config.py")
    sys.exit(1)

from core import find_player_in_groups, fetch_rooms

# =============================================================================
# GRAPH GENERATION
# =============================================================================

GRAPH_HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
    <title>MKWiiRR Session Tracker</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <meta http-equiv="refresh" content="5">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #1a1a2e;
            color: #eee;
            margin: 0;
            padding: 20px;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        h1 {{
            color: #00d4ff;
            margin-bottom: 5px;
        }}
        .subtitle {{
            color: #888;
            margin-bottom: 20px;
        }}
        .stats {{
            display: flex;
            gap: 20px;
            flex-wrap: wrap;
            margin-bottom: 20px;
        }}
        .stat-box {{
            background: #16213e;
            border-radius: 10px;
            padding: 15px 25px;
            min-width: 120px;
        }}
        .stat-label {{
            color: #888;
            font-size: 12px;
            text-transform: uppercase;
        }}
        .stat-value {{
            font-size: 28px;
            font-weight: bold;
        }}
        .stat-value.positive {{ color: #00ff88; }}
        .stat-value.negative {{ color: #ff4466; }}
        .stat-value.neutral {{ color: #00d4ff; }}
        .stat-sub {{
            margin-top: 6px;
            font-size: 14px;
            color: #aaa;
        }}
        .stat-sub.positive {{ color: #00ff88; }}
        .stat-sub.neutral {{ color: #aaa; }}
        .chart-container {{
            background: #16213e;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
        }}
        .race-history {{
            background: #16213e;
            border-radius: 10px;
            padding: 20px;
        }}
        .players-section {{
            background: #16213e;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
        }}
        .players-section h3 {{
            margin-top: 0;
            color: #00d4ff;
        }}
        .room-summary {{
            margin: 0 0 10px 0;
            font-weight: 600;
            color: #ddd;
        }}
        table.players-table {{
            width: 100%;
            border-collapse: collapse;
        }}
        table.players-table th, table.players-table td {{
            text-align: left;
            padding: 8px 10px;
            border-bottom: 1px solid #2a2a4a;
        }}
        table.players-table th {{
            color: #aaa;
            font-weight: 600;
        }}
        .race-history h3 {{
            margin-top: 0;
            color: #00d4ff;
        }}
        .race-item {{
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid #2a2a4a;
        }}
        .race-item:last-child {{
            border-bottom: none;
        }}
        .race-change.positive {{ color: #00ff88; }}
        .race-change.negative {{ color: #ff4466; }}
        .room-info {{
            background: #16213e;
            border-radius: 10px;
            padding: 15px 25px;
            margin-bottom: 20px;
        }}
        .not-in-room {{
            color: #ff4466;
        }}
        .waiting {{
            color: #ffaa00;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🏎️ MKWii Retro Rewind Session Tracker</h1>
        <p class="subtitle">Total session time: <span id="sessionDuration">{session_duration}</span></p>
        
        <div class="stats">
            <div class="stat-box">
                <div class="stat-label">Starting VR</div>
                <div class="stat-value neutral">{start_vr:,}</div>
            </div>
            <div class="stat-box">
                <div class="stat-label">Current VR</div>
                <div class="stat-value neutral">{current_vr:,}</div>
            </div>
            <div class="stat-box">
                <div class="stat-label">Net Change</div>
                <div class="stat-value {net_class}">{net_change:+,}</div>
            </div>
            <div class="stat-box">
                <div class="stat-label">Races</div>
                <div class="stat-value neutral">{race_count}</div>
            </div>
            <div class="stat-box">
                <div class="stat-label">VR Streak</div>
                <div class="stat-value {streak_class}">{streak_vr:+,}</div>
                <div class="stat-sub {streak_class}">{streak_races} {streak_race_label}</div>
            </div>
        </div>
        
        <div class="chart-container">
            <canvas id="vrChart"></canvas>
        </div>
        
        <div class="players-section">
            <h3>Current Room{room_id_heading}</h3>
            {players_section_html}
        </div>
        
        <div class="race-history">
            <h3>Race History (This Session)</h3>
            {race_history_html}
        </div>
    </div>
    
    <script>
        // Live-updating session duration (counts up from 0 at session start)
        const sessionStartMs = {session_start_ms};
        function updateSessionDuration() {{
            const elapsed = Date.now() - sessionStartMs;
            const hours = Math.floor(elapsed / 3600000);
            const minutes = Math.floor((elapsed % 3600000) / 60000);
            const seconds = Math.floor((elapsed % 60000) / 1000);
            const pad = (n) => String(n).padStart(2, '0');
            const text = `${{pad(hours)}}:${{pad(minutes)}}:${{pad(seconds)}}`;
            const el = document.getElementById('sessionDuration');
            if (el) el.textContent = text;
        }}
        updateSessionDuration();
        setInterval(updateSessionDuration, 1000);
        const ctx = document.getElementById('vrChart').getContext('2d');
        const data = {chart_data};
        
        new Chart(ctx, {{
            type: 'line',
            data: {{
                labels: data.labels,
                datasets: [
                    {{
                        label: 'VR',
                        data: data.values,
                        borderColor: '#00d4ff',
                        backgroundColor: 'rgba(0, 212, 255, 0.1)',
                        fill: true,
                        tension: 0.1,
                        pointBackgroundColor: data.values.map((v, i) => {{
                            if (i === 0) return '#00d4ff';
                            return v > data.values[i-1] ? '#00ff88' : '#ff4466';
                        }}),
                        pointRadius: 6,
                        pointHoverRadius: 8
                    }},
                    {{
                        label: 'Session Start',
                        data: data.startLine,
                        borderColor: '#aaaaaa',
                        borderWidth: 1,
                        fill: false,
                        tension: 0,
                        pointRadius: 0,
                        pointHoverRadius: 0
                    }},
                    {{
                        label: 'Session High',
                        data: data.highLine,
                        borderColor: '#00ff88',
                        borderWidth: 1,
                        borderDash: [6, 6],
                        fill: false,
                        tension: 0,
                        pointRadius: 0,
                        pointHoverRadius: 0
                    }},
                    {{
                        label: 'Session Low',
                        data: data.lowLine,
                        borderColor: '#ff4466',
                        borderWidth: 1,
                        borderDash: [6, 6],
                        fill: false,
                        tension: 0,
                        pointRadius: 0,
                        pointHoverRadius: 0
                    }}
                ]
            }},
            options: {{
                responsive: true,
                animation: false,
                plugins: {{
                    legend: {{
                        display: false
                    }},
                    title: {{
                        display: true,
                        text: 'VR Progression',
                        color: '#eee',
                        font: {{ size: 16 }}
                    }}
                }},
                scales: {{
                    x: {{
                        ticks: {{ color: '#888' }},
                        grid: {{ color: '#2a2a4a' }}
                    }},
                    y: {{
                        ticks: {{ color: '#888' }},
                        grid: {{ color: '#2a2a4a' }}
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>
"""


def generate_graph_html(session_data, output_path="session_graph.html"):
    """Generate the session graph HTML file."""
    races = session_data["races"]
    
    # Compute session duration (HH:MM:SS)
    try:
        start_dt = datetime.strptime(session_data["start_time"], "%Y-%m-%d %H:%M:%S")
        elapsed_seconds = int((datetime.now() - start_dt).total_seconds())
        hours = elapsed_seconds // 3600
        minutes = (elapsed_seconds % 3600) // 60
        seconds = elapsed_seconds % 60
        session_duration = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    except Exception:
        session_duration = "--:--:--"
    # Compute current positive VR streak (sum and count of consecutive gains)
    streak_vr = 0
    streak_races = 0
    for r in reversed(races):
        change = r.get("vr_change", 0)
        if change > 0:
            streak_vr += change
            streak_races += 1
        else:
            break
    streak_class = "positive" if streak_vr > 0 else "neutral"
    streak_race_label = "race" if streak_races == 1 else "races"
    # Build current room players section
    players_section_html = '<p class="not-in-room">Not currently in a room</p>'
    room_id = session_data.get("room_id")
    room_id_heading = f" — {room_id}" if room_id else ""
    if room_id:
        try:
            rooms = fetch_rooms()
            room = next((r for r in rooms if r.get("id") == room_id), None)
            if room:
                players = room.get("players", [])
                # Compute average VR from available vr fields
                vr_values = [p.get("vr") for p in players if isinstance(p.get("vr"), (int, float))]
                avg_vr = int(sum(vr_values) / len(vr_values)) if vr_values else 0
                summary = f'<p class="room-summary">{len(players)} Players - {avg_vr:,} VR Avg</p>'
                # Sort players by VR descending (treat None as 0)
                players_sorted = sorted(players, key=lambda p: p.get("vr") or 0, reverse=True)
                rows = []
                rows.append("<table class=\"players-table\">")
                rows.append("<thead><tr><th>Name</th><th>Friend Code</th><th>VR</th></tr></thead><tbody>")
                for p in players_sorted:
                    name = p.get("name", "Unknown")
                    fc = p.get("friendCode", "")
                    vr = p.get("vr") if isinstance(p.get("vr"), (int, float)) else 0
                    rows.append(f"<tr><td>{name}</td><td>{fc}</td><td>{vr:,}</td></tr>")
                rows.append("</tbody></table>")
                players_section_html = summary + "".join(rows)
            else:
                players_section_html = '<p class="waiting">Room data not found. It may have just changed.</p>'
        except Exception:
            players_section_html = '<p class="waiting">Unable to load room details right now.</p>'
    
    # Build chart data
    labels = ["Start"]
    values = [session_data["start_vr"]]
    
    for i, race in enumerate(races):
        labels.append(f"Race {i + 1}")
        values.append(race["total_vr"])
    
    # Session lines
    start_vr = session_data["start_vr"]
    session_high = max(values) if values else start_vr
    session_low = min(values) if values else start_vr
    start_line = [start_vr] * len(labels)
    high_line = [session_high] * len(labels)
    low_line = [session_low] * len(labels)
    
    chart_data = {
        "labels": labels,
        "values": values,
        "startLine": start_line,
        "highLine": high_line,
        "lowLine": low_line
    }
    
    # Calculate stats
    race_count = len(races)
    current_vr = session_data["current_vr"]
    net_change = current_vr - session_data["start_vr"]
    
    net_class = "positive" if net_change > 0 else "negative" if net_change < 0 else "neutral"
    
    # Build race history HTML (newest first)
    race_history_items = []
    for i, race in enumerate(reversed(races[-15:])):
        change_class = "positive" if race["vr_change"] > 0 else "negative"
        race_num = len(races) - i
        time_str = race["time"]
        race_history_items.append(
            f'<div class="race-item">'
            f'<span>Race {race_num} ({time_str})</span>'
            f'<span class="race-change {change_class}">{race["vr_change"]:+,} VR</span>'
            f'</div>'
        )
    
    if race_history_items:
        race_history_html = "".join(race_history_items)
    else:
        race_history_html = '<p class="waiting">Waiting for first race...</p>'
    
    html = GRAPH_HTML_TEMPLATE.format(
        session_duration=session_duration,
        session_start_ms=int(start_dt.timestamp() * 1000) if 'start_dt' in locals() else 0,
        start_vr=session_data["start_vr"],
        current_vr=current_vr,
        net_change=net_change,
        net_class=net_class,
        race_count=race_count,
        chart_data=json.dumps(chart_data),
        race_history_html=race_history_html,
        players_section_html=players_section_html,
        streak_vr=streak_vr,
        streak_races=streak_races,
        streak_class=streak_class,
        streak_race_label=streak_race_label,
        room_id_heading=room_id_heading
    )
    
    with open(output_path, "w") as f:
        f.write(html)


def save_session(session_data):
    """Save session data to a JSON file."""
    if not SAVE_SESSION_DATA:
        return
    
    os.makedirs(SESSION_DATA_DIR, exist_ok=True)
    timestamp = session_data["start_time"].replace(":", "-").replace(" ", "_")
    filename = f"session_{timestamp}.json"
    filepath = os.path.join(SESSION_DATA_DIR, filename)
    
    with open(filepath, "w") as f:
        json.dump(session_data, f, indent=2)
    
    print(f"Session saved to {filepath}")


def print_status(session_data):
    """Print current session status to terminal."""
    races = session_data["races"]
    current_vr = session_data["current_vr"]
    net_change = current_vr - session_data["start_vr"]
    room_id = session_data.get("room_id", "None")
    
    timestamp = time.strftime("%I:%M:%S %p")
    
    status = f"\r[{timestamp}] Room: {room_id} | VR: {current_vr:,} | Net: {net_change:+,} | Races: {len(races)}"
    
    if races:
        last_change = races[-1]["vr_change"]
        status += f" | Last: {last_change:+,}"
    
    print(status + "          ", end="", flush=True)


def main():
    """Main session tracking loop."""
    print("MKWiiRR Session Tracker")
    print(f"Friend Code: {PLAYER_FRIEND_CODE}")
    print(f"Poll Interval: {POLL_INTERVAL}s")
    print("-" * 55)
    
    # Get initial VR
    print("Finding player...")
    room_id, player = find_player_in_groups(PLAYER_FRIEND_CODE)
    
    if not player:
        print("Not currently in a room. Join a room and restart.")
        return
    
    start_vr = int(player.get("ev", 0))
    player_name = player.get("name", "Unknown")
    
    session_data = {
        "start_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "player_name": player_name,
        "start_vr": start_vr,
        "current_vr": start_vr,
        "room_id": room_id,
        "races": []
    }
    
    print(f"Player: {player_name}")
    print(f"Starting VR: {start_vr:,}")
    print(f"Room: {room_id}")
    print("-" * 55)
    print("Tracking... (Ctrl+C to stop)")
    print("Run: open session_graph.html")
    print()
    
    generate_graph_html(session_data)
    last_vr = start_vr
    
    try:
        while True:
            try:
                room_id, player = find_player_in_groups(PLAYER_FRIEND_CODE)
                
                if player:
                    current_vr = int(player.get("ev", 0))
                    session_data["room_id"] = room_id
                    session_data["current_vr"] = current_vr
                    
                    # VR changed = race completed
                    if current_vr != last_vr:
                        vr_change = current_vr - last_vr
                        race_data = {
                            "time": datetime.now().strftime("%I:%M %p"),
                            "vr_change": vr_change,
                            "total_vr": current_vr
                        }
                        session_data["races"].append(race_data)
                        
                        emoji = "🟢" if vr_change > 0 else "🔴"
                        print(f"\n{emoji} Race {len(session_data['races'])}: {vr_change:+,} VR (Total: {current_vr:,})")
                        
                        last_vr = current_vr
                        generate_graph_html(session_data)
                else:
                    session_data["room_id"] = None
                
                print_status(session_data)
                
            except Exception as e:
                print(f"\n[Error: {e}]")
            
            time.sleep(POLL_INTERVAL)
    
    except KeyboardInterrupt:
        print("\n\n" + "=" * 55)
        print("SESSION ENDED")
        print("=" * 55)
        
        races = session_data["races"]
        if races:
            net_change = session_data["current_vr"] - session_data["start_vr"]
            
            print(f"Total Races: {len(races)}")
            print(f"Starting VR: {session_data['start_vr']:,}")
            print(f"Ending VR: {session_data['current_vr']:,}")
            print(f"Net Change: {net_change:+,}")
        else:
            print("No races completed this session")
        
        save_session(session_data)
        print("=" * 55)


if __name__ == "__main__":
    main()