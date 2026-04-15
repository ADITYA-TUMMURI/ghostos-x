#!/bin/bash
set -e

SERVICE_DIR="$HOME/.config/systemd/user"
SERVICE_FILE="ghostos.service"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "[GhostOS] Installing systemd service..."

mkdir -p "$SERVICE_DIR"
cp "$SCRIPT_DIR/$SERVICE_FILE" "$SERVICE_DIR/$SERVICE_FILE"

echo "[GhostOS] Reloading systemd..."
systemctl --user daemon-reload

echo "[GhostOS] Enabling service..."
systemctl --user enable ghostos

echo "[GhostOS] Starting service..."
systemctl --user start ghostos

echo "[GhostOS] Status:"
systemctl --user status ghostos --no-pager

echo ""
echo "[GhostOS] Done. Daemon will auto-start on login."
echo "[GhostOS] Logs: journalctl --user -u ghostos -f"
