# GhostOS X

> Your desktop automation platform, rebuilt for minimalist Linux systems.

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![Platform](https://img.shields.io/badge/Linux-Wayland%20%2F%20X11-green)
![License](https://img.shields.io/badge/License-MIT-yellow)
![Dependencies](https://img.shields.io/badge/Dependencies-Standard%20Library%20Only-brightgreen)

No machine learning frameworks. No cloud. No tracking. Zero external dependencies. Everything runs locally in your standard Python environment.

---

## 🧠 Workflow Intelligence: Time-Decayed Markov Chain Engine

GhostOS X features a lightweight, time-decayed transition prediction engine implemented from scratch in pure Python:
*   **Decayed Transition Probabilities**: Instead of simple frequencies, the engine weights user history using an exponential decay algorithm:
    *   Transitions in the last 7 days receive a weight multiplier of `1.0`.
    *   Transitions in the last 30 days receive a weight multiplier of `0.5`.
    *   Transitions older than 30 days receive a weight multiplier of `0.1`.
*   **Context-Aware Routing**: Prioritizes transitions matching active context hints (e.g. project workspace directories mined from terminal title strings) by applying a `5.0x` weight boost.
*   **Workflow Reconstruction**: Iteratively charts upcoming transitions to form a chain of next actions (e.g. `Terminal -> VSCode -> Chrome`).

---

## 🔒 Privacy-First Design: Active Window Masking

GhostOS X protects your active session data using strict browser filtering and masking policies:
*   **Mask Everything Mode**: Optional configuration to replace all browser-related window titles with a generic `"Browser"` label.
*   **Domain Truncation**: When domain-masking is enabled, titles matching a customizable domain whitelist are truncated (e.g. mapping `"Pull Requests · ADITYA-TUMMURI/ghostos-x · GitHub"` down to `"github.com"`).
*   **Full Anonymization**: All path queries, query parameters, title headings, and metadata are scrubbed before logging to ensure zero exposure of private URLs.

---

## ⚡ Cross-Compositor Window Tracking

Unlike legacy solutions, GhostOS X dynamically detects your display server and compositor to gather window focus:
*   **Wayland Native**: 
    *   *Hyprland*: Uses `hyprctl` socket communication.
    *   *Sway*: Queries the window tree recursively via standard JSON messages (`swaymsg`).
*   **X11 Fallback**: Invokes `xdotool` natively.

---

## 🚀 Installation & Systemd Service

Deploy the systemd user tier background service and configurations using the universal installation script:

### 1. Run the Installer
```bash
./install.sh
```
*Note: The installer automatically checks package manager managers (`dnf`, `apt`, `pacman`, `zypper`) for platform binaries like `xdotool` and configures execution environments.*

### 2. Systemd User Tier Control
You do not need system root access. Run and monitor the background daemon:
```bash
# Enable and start the tracker immediately
systemctl --user enable --now ghostos.service

# Check active runtime status
systemctl --user status ghostos.service
```

### 3. Uninstall Cleanly
To stop the daemon and revert changes without losing your tracked SQLite records:
```bash
./uninstall.sh
```

---

## 💻 CLI Commands

Run the execution wrapper via Python module flags:

```bash
# Start active window tracking in the foreground
python3 -m ghostos track

# View Focus Score & ASCII progress bar breakdown for today
python3 -m ghostos report

# View focus score for a specific date
python3 -m ghostos report 2026-07-07

# Manually invoke safe Phantom Mode autopilot
python3 -m ghostos autopilot
```

---

## ⚙️ Configuration (`~/.config/ghostos/config.json`)

All active settings are defined in a clean JSON format:
```json
{
  "browser_privacy": {
    "mask_everything": false,
    "allowed_domains_only": [
      "github.com",
      "google.com",
      "stackoverflow.com"
    ]
  },
  "app_normalization": {
    "chrome": "Chrome",
    "firefox": "Firefox",
    "vs code": "VSCode",
    "code": "VSCode",
    "terminal": "Terminal"
  },
  "hooks": {
    "pre_autopilot": "echo 'Preparing Phantom Mode...'",
    "post_autopilot": "echo 'Phantom Mode complete.'"
  },
  "autopilot_settings": {
    "max_launches_per_minute": 10,
    "check_process_active": true
  }
}
```

---

## 🛠️ Data Storage & Recovery

All local databases and logs are stored under user XDG directories:
*   **Database**: `~/.local/share/ghostos/activity.db`
*   **Rate Limits**: `~/.local/share/ghostos/rate_limit.json`
*   **Self-Healing Recovery**: If database corruption is detected, GhostOS X backs up the corrupted database to `activity.db.bak` and reconstructs a fresh SQLite instance automatically without crashing the execution loop.

---

## 📄 License

MIT
