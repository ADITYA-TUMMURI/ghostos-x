import os
import subprocess


def check_xdotool():
    try:
        subprocess.run(
            ["which", "xdotool"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
        return True
    except Exception:
        return False


def check_tts():
    for cmd in ["espeak", "spd-say"]:
        try:
            subprocess.run(
                ["which", cmd],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True,
            )
            return cmd
        except Exception:
            continue
    return None


def detect_session_type():
    return os.environ.get("XDG_SESSION_TYPE", "unknown")


def which(cmd):
    try:
        subprocess.run(
            ["which", cmd],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
        return True
    except Exception:
        return False


def find_available_command(candidates):
    for cmd in candidates:
        if which(cmd):
            return cmd
    return None


def preflight(require_xdotool=True):
    ok = True

    session = detect_session_type()
    if session == "wayland":
        print("[GhostOS] ⚠ Wayland detected — tracking may not work.")
        print("[GhostOS]   Consider running under X11 or Xwayland.")

    if require_xdotool and not check_xdotool():
        print("[GhostOS] ✗ xdotool not found.")
        print("[GhostOS]   Install: sudo dnf install xdotool")
        print("[GhostOS]        or: sudo apt install xdotool")
        ok = False

    tts = check_tts()
    if not tts:
        print("[GhostOS] ℹ No TTS engine found (espeak/spd-say). Voice disabled.")

    return ok
