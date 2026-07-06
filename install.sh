#!/usr/bin/env bash

# Principal Linux Systems Engineer installer script for GhostOS X

set -euo pipefail

# Get absolute path of the directory where install.sh is located
PROJECT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "=================================================="
echo "    GhostOS X Installer Blueprint                 "
echo "=================================================="

# 1. Package manager detection
echo -n "Step 1: Checking system package manager... "
if command -v apt-get >/dev/null 2>&1; then
    PKG_MANAGER="apt"
    echo "Detected apt (Debian/Ubuntu/Mint)"
elif command -v dnf >/dev/null 2>&1; then
    PKG_MANAGER="dnf"
    echo "Detected dnf (Fedora/RHEL)"
elif command -v pacman >/dev/null 2>&1; then
    PKG_MANAGER="pacman"
    echo "Detected pacman (Arch/Manjaro)"
elif command -v zypper >/dev/null 2>&1; then
    PKG_MANAGER="zypper"
    echo "Detected zypper (openSUSE)"
else
    PKG_MANAGER="unknown"
    echo "Unknown package manager"
fi

# 2. Dependency validation
echo "Step 2: Checking environment dependencies..."
SESSION_TYPE="${XDG_SESSION_TYPE:-unknown}"
echo "Current Session Type: $SESSION_TYPE"

# Check for xdotool
if ! command -v xdotool >/dev/null 2>&1; then
    echo "WARNING: 'xdotool' is missing. It is required for tracking on X11 environments."
    case "$PKG_MANAGER" in
        apt)     echo "  To install: sudo apt install xdotool" ;;
        dnf)     echo "  To install: sudo dnf install xdotool" ;;
        pacman)  echo "  To install: sudo pacman -S xdotool" ;;
        zypper)  echo "  To install: sudo zypper install xdotool" ;;
        *)       echo "  Please install xdotool via your distribution package manager." ;;
    esac
else
    echo "  [✓] xdotool found: $(command -v xdotool)"
fi

# Wayland check
if [ "$SESSION_TYPE" = "wayland" ]; then
    if ! command -v hyprctl >/dev/null 2>&1 && ! command -v swaymsg >/dev/null 2>&1; then
        echo "WARNING: Wayland session detected, but neither 'hyprctl' nor 'swaymsg' was found."
        echo "         Limited default tracking will be used."
    else
        [ -n "$(command -v hyprctl)" ] && echo "  [✓] Hyprland environment detected."
        [ -n "$(command -v swaymsg)" ] && echo "  [✓] Sway environment detected."
    fi
fi

# 3. Create paths
echo "Step 3: Preparing directories..."
mkdir -p "$HOME/.local/share/ghostos"
mkdir -p "$HOME/.config/ghostos"
echo "  [✓] Paths initialized under ~/.local/share/ghostos and ~/.config/ghostos"

# 4. Deploy configuration
echo "Step 4: Deploying user configuration..."
if [ ! -f "$HOME/.config/ghostos/config.json" ]; then
    cp "$PROJECT_DIR/ghostos/config/config.json" "$HOME/.config/ghostos/config.json"
    echo "  [✓] Default config seeded at ~/.config/ghostos/config.json"
else
    echo "  [i] Configuration already exists at ~/.config/ghostos/config.json. Skipping copy."
fi

# 5. systemd Service Setup
echo "Step 5: Setup systemd user-tier service..."
USER_SYSTEMD_DIR="$HOME/.config/systemd/user"
mkdir -p "$USER_SYSTEMD_DIR"

# Dynamically replace path to point to cloned project directory (supports custom clone paths)
echo "  Configuring service file ExecStart path to: $PROJECT_DIR/ghostos/core_tracker.py"
sed "s|%h/projects/ghostos-x|${PROJECT_DIR}|g" "$PROJECT_DIR/systemd/ghostos.service" > "$USER_SYSTEMD_DIR/ghostos.service"

echo "  Reloading systemd user daemon..."
systemctl --user daemon-reload

echo "=================================================="
echo "    GhostOS X Service Setup Complete!             "
echo "=================================================="
echo ""
echo "To start the background tracking daemon right now:"
echo "    systemctl --user start ghostos.service"
echo ""
echo "To enable it to start automatically when you log in:"
echo "    systemctl --user enable ghostos.service"
echo ""
echo "To check service logs or active runtime status:"
echo "    systemctl --user status ghostos.service"
echo "    journalctl --user -u ghostos.service -f"
echo ""
echo "To view your first usage report:"
echo "    python3 $PROJECT_DIR/ghostos/report_cli.py"
echo ""
