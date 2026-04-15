# Ghost OS X

**Activity Intelligence Engine for Linux**

GhostOS X is a lightweight adaptive system for Linux that learns your workflow, predicts your next actions, and prepares your environment automatically — without heavy AI or manual configuration.

Built with Python 3 and SQLite. No external dependencies.

---

## 🧠 Example

You open your laptop at night.

GhostOS:
- predicts you will code
- launches VSCode
- opens terminal
- prepares your workflow

All before you do anything.

---

## Features

| Module | Description |
|---|---|
| **Tracker** | Polls active window every 5s via `xdotool`, logs to SQLite |
| **Patterns** | Top apps by total usage + dominant app per hour |
| **Sequences** | Detects most common app-to-app transitions |
| **Predictions** | Time-based + next-app prediction from historical data |
| **Report** | Daily breakdown with focus score and visual bars |
| **Autopilot** | Phantom Mode — reconstructs & launches full workflow chains |
| **Daemon** | Background autopilot loop with configurable cooldown |
| **Config** | JSON-based toggle system for all features |
| **Voice** | Optional TTS announcements via espeak/spd-say |

---

## Installation

### Prerequisites

- Python 3.10+
- Linux with X11
- `xdotool` installed:

```bash
# Fedora
sudo dnf install xdotool

# Ubuntu/Debian
sudo apt install xdotool
```

### Optional: Voice Feedback

```bash
# Fedora
sudo dnf install espeak

# Ubuntu/Debian
sudo apt install espeak

# Then enable:
ghostos config set voice true
```

### Install

```bash
git clone https://github.com/youruser/ghostos-x.git
cd ghostos-x
pip install .
```

Or run directly without installing:

```bash
python ghostos.py <command>
```

---

## Usage

```
ghostos track              Start tracking active window
ghostos report [DATE]      Daily report (default: today)
ghostos patterns           Top apps + hourly usage patterns
ghostos sequences          App transition sequences
ghostos predict            Time + next-app predictions
ghostos autopilot          Phantom mode (workflow reconstruction)
ghostos daemon             Background autopilot daemon
ghostos config show        Show current config
ghostos config set K V     Set config value
ghostos status             Show database stats
```

---

## Configuration

All features are toggleable via `config/config.json`:

```json
{
  "overlay": true,
  "voice": false,
  "autopilot": true,
  "suggestions": true,
  "daemon_interval": 300,
  "cooldown": 1800
}
```

### CLI Config Commands

```bash
# View all settings
ghostos config show

# Enable voice feedback
ghostos config set voice true

# Disable autopilot
ghostos config set autopilot false

# Change daemon interval to 10 minutes
ghostos config set daemon_interval 600
```

---

## Example Output

### `ghostos report 2026-04-15`

```
╔══════════════════════════════════════╗
║       GHOST OS X — DAILY REPORT      ║
╠══════════════════════════════════════╣
║  Date: 2026-04-15                   ║
╚══════════════════════════════════════╝

=== Overview ===
Total tracked: 6.7h
Total sessions: 12
Apps used: 4
Avg session: 33.3m
Longest session: 1.0h
Focus score: [████████████████████] 100/100

=== App Breakdown ===
  Chrome             3.0h  ▓▓▓▓▓▓▓▓▓░░░░░░░░░░░  45%  (4 sessions)
  VSCode             2.5h  ▓▓▓▓▓▓▓░░░░░░░░░░░░░  38%  (4 sessions)
  Firefox           40.0m  ▓▓░░░░░░░░░░░░░░░░░░  10%  (2 sessions)
  Terminal          30.0m  ▓░░░░░░░░░░░░░░░░░░░  8%  (2 sessions)

=== Peak Hours ===
  09:00  3.0h
  21:00  1.5h
  14:00  1.0h
```

### `ghostos autopilot` (Phantom Mode)

```
[GhostOS] Hour: 09:00
[GhostOS] Reconstructing workflow...
[GhostOS] Chain: Chrome → Terminal
[GhostOS] Launching Chrome
[GhostOS] Launching Terminal
```

### `ghostos config show`

```
=== Ghost OS X — Config ===
  overlay              True ✓
  voice                False ✗
  autopilot            True ✓
  suggestions          True ✓
  daemon_interval      300
  cooldown             1800
```

---

## Project Structure

```
ghostos-x/
├── ghostos.py              CLI entry point
├── activity_logger.py      SQLite database handler
├── tracker.py              Active window tracker
├── analysis/               Analysis & Prediction modules
├── core/                   Core logic (autopilot, daemon, config, etc.)
├── ui/
│   └── dashboard.py        Optional Flask web dashboard
├── ghostos.service         systemd user service
├── install-service.sh      Service installer
├── setup.py                Package installer
├── requirements.txt        Dependencies
└── README.md               This file
```

---

## Data Directory

All user data and runtime logs are stored securely in:
`~/.local/share/ghostos/`

```
~/.local/share/ghostos/
├── activity.db             SQLite database
├── config.json             User settings
└── logs/
    └── ghostos.log         Runtime logger output
```
├── ghostos.service          systemd user service
├── install-service.sh       Service installer
├── setup.py                 Package installer
├── requirements.txt         Dependencies
└── README.md                This file
```

---

## Compatibility

| Feature | X11 | Wayland |
|---|---|---|
| Window tracking | ✅ Full | ⚠ Limited |
| App launching | ✅ Full | ✅ Full |
| Predictions | ✅ Full | ✅ Full |
| Voice feedback | ✅ Full | ✅ Full |

> **Wayland note:** `xdotool` does not work natively on Wayland. Ghost OS X will print a warning and continue safely, but tracking data may be unavailable. Use XWayland or X11 session for full support.

---

## Quick Start

```bash
# 1. Install xdotool
sudo dnf install xdotool    # Fedora
sudo apt install xdotool    # Ubuntu/Debian

# 2. Start tracking (run for a few hours)
ghostos track

# 3. View your report
ghostos report

# 4. See predictions
ghostos predict

# 5. Start the background daemon
ghostos daemon

# 6. View local web dashboard (optional)
ghostos config set dashboard true
ghostos dashboard
```

---

## Troubleshooting

### xdotool not found
```
[GhostOS] ✗ xdotool not found.
```
**Fix:** Install it:
```bash
sudo dnf install xdotool    # Fedora
sudo apt install xdotool    # Ubuntu/Debian
```

### App not launching
```
[GhostOS] No installed binary for Chrome
```
**Fix:** Edit `config/config.json` and add your browser command to the `launch_map`:
```json
"Chrome": ["google-chrome", "chromium", "your-browser-command"]
```

### Voice not working
```
[GhostOS] ℹ No TTS engine found
```
**Fix:**
```bash
sudo dnf install espeak     # Fedora
sudo apt install espeak     # Ubuntu/Debian
ghostos config set voice true
```

### Wayland warning
```
[GhostOS] ⚠ Wayland detected — tracking may not work
```
**Fix:** Switch to X11 session at login, or accept limited tracking.

### Flask not installed
```
[GhostOS] Flask not installed. Run: pip install flask
```
**Fix:** If you enabled the dashboard, you must install Flask to run it:
```bash
pip install flask
```

### Database corruption
Ghost OS X automatically backs up corrupted databases to `~/.local/share/ghostos/activity.db.bak` and recreates a fresh one.

---

## App Normalization

Window titles are automatically normalized:

| Window Title Contains | Normalized To |
|---|---|
| chrome, chromium | Chrome |
| firefox | Firefox |
| vs code, code | VSCode |
| terminal, konsole, alacritty, kitty | Terminal |
| anything else | First 30 characters |

---

## How It Works

1. **Tracker** polls the active window every 5 seconds
2. On app switch (or every 30s checkpoint), duration is logged to SQLite
3. **Analysis engines** query the database for patterns, sequences, and predictions
4. **Autopilot** builds workflow chains from transition data and launches sequentially
5. **Daemon** runs autopilot in a loop with configurable cooldown
6. **Config** lets you toggle any feature on/off without touching code
7. **Voice** announces actions via system TTS when enabled
8. **Preflight** checks dependencies and environment before starting
9. **Logger** writes all activity to `logs/ghostos.log`

---

## License

MIT
