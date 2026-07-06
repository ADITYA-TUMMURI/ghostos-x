import os
import re
import sys
import json
import time
import shutil
import sqlite3
import signal
import subprocess
from datetime import datetime

# Database path in user's home directory
DB_PATH = os.path.expanduser("~/.local/share/ghostos/activity.db")
CONFIG_PATH = os.path.expanduser("~/.local/share/ghostos/config.json")


def find_default_config():
    """Locate the default config.json packaged with the module."""
    dir_path = os.path.dirname(os.path.abspath(__file__))
    p1 = os.path.join(dir_path, "config", "config.json")
    if os.path.exists(p1):
        return p1
    p2 = os.path.join(os.path.dirname(dir_path), "ghostos", "config", "config.json")
    if os.path.exists(p2):
        return p2
    return None


def backup_db(db_path):
    """Safely backup a corrupted database."""
    if os.path.exists(db_path):
        bak = db_path + ".bak"
        try:
            shutil.copy2(db_path, bak)
            os.remove(db_path)
            print(f"[GhostOS] Corrupt database backed up to {bak} and removed.")
        except Exception as e:
            print(f"[GhostOS] Failed to backup corrupt database: {e}", file=sys.stderr)


def init_db(db_path):
    """Initialize the SQLite database schema and migrate column changes."""
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    try:
        conn = sqlite3.connect(db_path)
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS activity (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                app_name     TEXT    NOT NULL,
                start_time   TEXT    NOT NULL,
                end_time     TEXT    NOT NULL,
                duration     REAL    NOT NULL,
                context_hint TEXT
            )
            """
        )
        # Verify if context_hint column exists, perform migration if missing
        cursor = conn.execute("PRAGMA table_info(activity)")
        columns = [row[1] for row in cursor.fetchall()]
        if "context_hint" not in columns:
            conn.execute("ALTER TABLE activity ADD COLUMN context_hint TEXT")
        conn.commit()
        conn.close()
    except sqlite3.DatabaseError:
        backup_db(db_path)
        # Attempt to recreate the database fresh
        try:
            conn = sqlite3.connect(db_path)
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS activity (
                    id           INTEGER PRIMARY KEY AUTOINCREMENT,
                    app_name     TEXT    NOT NULL,
                    start_time   TEXT    NOT NULL,
                    end_time     TEXT    NOT NULL,
                    duration     REAL    NOT NULL,
                    context_hint TEXT
                )
                """
            )
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[GhostOS] Failed to initialize fresh database: {e}", file=sys.stderr)
    except Exception as e:
        print(f"[GhostOS] Database initialization error: {e}", file=sys.stderr)


def load_config(config_path, default_path):
    """Load configuration with dynamic fallback mechanism."""
    primary_config_path = os.path.expanduser("~/.config/ghostos/config.json")
    
    # Try loading from ~/.config/ghostos/config.json first
    if os.path.exists(primary_config_path):
        try:
            with open(primary_config_path, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"[GhostOS] Error parsing config at {primary_config_path}: {e}", file=sys.stderr)
            
    # Fallback to ~/.local/share/ghostos/config.json
    if os.path.exists(config_path):
        try:
            with open(config_path, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"[GhostOS] Error parsing config at {config_path}: {e}", file=sys.stderr)
            
    # Seed config in ~/.config/ghostos/config.json if template exists
    if default_path and os.path.exists(default_path):
        try:
            os.makedirs(os.path.dirname(primary_config_path), exist_ok=True)
            shutil.copy2(default_path, primary_config_path)
            print(f"[GhostOS] Initialized user config at {primary_config_path}")
            with open(primary_config_path, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"[GhostOS] Failed to initialize user config: {e}", file=sys.stderr)
            
    # Fallback to default template file directly
    if default_path and os.path.exists(default_path):
        try:
            with open(default_path, "r") as f:
                return json.load(f)
        except Exception:
            pass
            
    # Hardcoded minimum fallback profile
    return {
        "browser_privacy": {
            "mask_everything": False,
            "allowed_domains_only": []
        },
        "app_normalization": {},
        "hooks": {},
        "autopilot_settings": {
            "max_launches_per_minute": 10,
            "check_process_active": True
        }
    }


def get_active_window_x11():
    """Retrieve active window title on X11 environments using xdotool."""
    try:
        # Get active window ID
        wid = subprocess.check_output(
            ["xdotool", "getactivewindow"], stderr=subprocess.DEVNULL
        ).decode("utf-8", errors="ignore").strip()
        if not wid:
            return None
        # Get window title
        title = subprocess.check_output(
            ["xdotool", "getwindowname", wid], stderr=subprocess.DEVNULL
        ).decode("utf-8", errors="ignore").strip()
        return title
    except Exception:
        return None


def get_hyprland_active_window():
    """Retrieve active window title/class from Hyprland compositor."""
    try:
        out = subprocess.check_output(
            ["hyprctl", "activewindow"], stderr=subprocess.DEVNULL
        ).decode("utf-8", errors="ignore")
        title = None
        class_name = None
        for line in out.splitlines():
            line = line.strip()
            if line.startswith("title:"):
                title = line.split("title:", 1)[1].strip()
            elif line.startswith("class:"):
                class_name = line.split("class:", 1)[1].strip()
        if title:
            return title
        if class_name:
            return class_name
    except Exception:
        pass
    return None


def get_sway_active_window():
    """Retrieve active window title/class from Sway compositor tree."""
    try:
        out = subprocess.check_output(
            ["swaymsg", "-t", "get_tree"], stderr=subprocess.DEVNULL
        ).decode("utf-8", errors="ignore")
        tree = json.loads(out)
        
        def find_focused(node):
            if node.get("focused"):
                return node
            for child in node.get("nodes", []) + node.get("floating_nodes", []):
                res = find_focused(child)
                if res:
                    return res
            return None
            
        focused_node = find_focused(tree)
        if focused_node:
            name = focused_node.get("name")
            if name:
                return name
            app_id = focused_node.get("app_id")
            if app_id:
                return app_id
            wp = focused_node.get("window_properties", {})
            if wp.get("class"):
                return wp.get("class")
    except Exception:
        pass
    return None


def get_active_window_wayland():
    """Iterate through Wayland compositor query fallbacks."""
    title = get_hyprland_active_window()
    if title:
        return title
        
    title = get_sway_active_window()
    if title:
        return title
        
    return None


def get_active_window():
    """Retrieve active window title according to current session type."""
    session_type = os.environ.get("XDG_SESSION_TYPE", "").lower()
    
    if session_type == "wayland":
        title = get_active_window_wayland()
        if title:
            return title
        # X11 fallback (e.g. XWayland client or gnome fallback)
        return get_active_window_x11()
    else:
        # Default X11 session
        return get_active_window_x11()


def check_domain_in_title(domain, title_lower):
    """Verify if a domain exists in the lowercased window title with bounds."""
    # Match domain prefixed/suffixed by non-alphanumeric boundaries or start/end of string
    pattern = r'(?:^|[^a-zA-Z0-9])' + re.escape(domain.lower()) + r'(?:[^a-zA-Z0-9]|$)'
    return re.search(pattern, title_lower) is not None


def process_browser_privacy(title, config):
    """Enforce aggressive browser masking & privacy white-lists."""
    if not title:
        return "Idle"
        
    title_lower = title.lower()
    browsers = ["chrome", "firefox", "chromium", "brave", "opera"]
    is_browser = any(b in title_lower for b in browsers)
    
    if not is_browser:
        return None  # Skip if not browser
        
    privacy_cfg = config.get("browser_privacy", {})
    mask_everything = privacy_cfg.get("mask_everything", False)
    allowed_domains = privacy_cfg.get("allowed_domains_only", [])
    
    if mask_everything:
        return "Browser"
        
    # Check whitelist domains
    for domain in allowed_domains:
        if not domain:
            continue
        if check_domain_in_title(domain, title_lower):
            return domain
            
    # Default mask for unlisted domains
    return "Browser"


def extract_context_hint(title, app_name):
    """Extract path or directory structure out of terminal title."""
    if not title:
        return None
        
    # Avoid matching general URLs
    if "://" in title:
        return None
        
    # Match paths starting with ~ or /
    match = re.search(r'(~?/[a-zA-Z0-9_\-\.\/]+)', title)
    if match:
        path = match.group(1).strip()
        # Strip trailing syntax/punctuation
        path = path.rstrip(".,:;)")
        return path
        
    return None


def normalize_and_log(title, config):
    """Normalize window title into a clean app_name and extract directory context."""
    if not title:
        return "Idle", None
        
    # Process browser masking privacy rules first
    browser_app = process_browser_privacy(title, config)
    if browser_app is not None:
        return browser_app, None
        
    # Check normalization rules
    title_lower = title.lower()
    app_normalization = config.get("app_normalization", {})
    
    app_name = None
    for fragment, clean_value in app_normalization.items():
        if fragment.lower() in title_lower:
            app_name = clean_value
            break
            
    # Detect typical user@host terminal window title pattern
    if not app_name:
        if re.search(r'^[a-zA-Z0-9_\-]+@[a-zA-Z0-9_\-]+:', title) or re.search(r'^[a-zA-Z0-9_\-]+@[a-zA-Z0-9_\-]+\s', title):
            app_name = "Terminal"
            
    if not app_name:
        # Default truncation rule
        app_name = title[:30].strip() if title else "Idle"
        
    # Extract directory context hints if the app resolves to Terminal
    context_hint = None
    if app_name == "Terminal":
        context_hint = extract_context_hint(title, app_name)
        
    return app_name, context_hint


def log_session(db_path, app_name, start_time, end_time, context_hint=None):
    """Save parsed window activity details to local SQLite database."""
    if not app_name or app_name == "Idle":
        return
    duration = (end_time - start_time).total_seconds()
    if duration < 1.0:
        return
        
    try:
        conn = sqlite3.connect(db_path)
        try:
            conn.execute(
                """
                INSERT INTO activity (app_name, start_time, end_time, duration, context_hint)
                VALUES (?, ?, ?, ?, ?)
                """,
                (app_name, start_time.isoformat(), end_time.isoformat(), duration, context_hint),
            )
            conn.commit()
            print(f"[GhostOS] Logged: {app_name} | {duration:.1f}s | Context: {context_hint or 'None'}")
        finally:
            conn.close()
    except sqlite3.DatabaseError:
        # DB corruption recovery fallback
        backup_db(db_path)
        init_db(db_path)
        try:
            conn = sqlite3.connect(db_path)
            conn.execute(
                """
                INSERT INTO activity (app_name, start_time, end_time, duration, context_hint)
                VALUES (?, ?, ?, ?, ?)
                """,
                (app_name, start_time.isoformat(), end_time.isoformat(), duration, context_hint),
            )
            conn.commit()
            print(f"[GhostOS] Logged (Recovered): {app_name} | {duration:.1f}s | Context: {context_hint or 'None'}")
            conn.close()
        except Exception as e:
            print(f"[GhostOS] Failed to log after recovery: {e}", file=sys.stderr)
    except Exception as e:
        print(f"[GhostOS] Error saving session to database: {e}", file=sys.stderr)


def start_tracking(poll_interval=5, checkpoint_interval=30):
    """Launch the main desktop tracking loop with check-pointing."""
    db_path = DB_PATH
    config_path = CONFIG_PATH
    default_config_path = find_default_config()
    
    # Preflight initialization
    init_db(db_path)
    config = load_config(config_path, default_config_path)
    
    print(f"[GhostOS] Tracker engine initialized.")
    print(f"[GhostOS] SQLite DB: {db_path}")
    print(f"[GhostOS] User Config: {config_path}")
    
    # Establish initial state
    raw_active_title = get_active_window()
    current_app, current_context = normalize_and_log(raw_active_title, config)
    start_time = datetime.now()
    last_save = start_time
    
    print(f"[GhostOS] Tracking active window: {current_app} (Context: {current_context})")
    
    # Register shutdown signals for saving active session state
    def sig_handler(signum, frame):
        print(f"\n[GhostOS] Signal {signum} received. Saving final session...")
        now = datetime.now()
        log_session(db_path, current_app, start_time, now, current_context)
        print("[GhostOS] Exit complete.")
        sys.exit(0)
        
    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)
    
    # Primary polling loop
    while True:
        try:
            time.sleep(poll_interval)
            
            # Periodically reload config so changes take effect
            config = load_config(config_path, default_config_path)
            
            # Query window details
            raw_active_title = get_active_window()
            active_app, active_context = normalize_and_log(raw_active_title, config)
            
            now = datetime.now()
            
            # Check for focus transitions (either application or directory context)
            if active_app != current_app or active_context != current_context:
                log_session(db_path, current_app, start_time, now, current_context)
                current_app = active_app
                current_context = active_context
                start_time = now
                last_save = now
                print(f"[GhostOS] Focus switched: {current_app} (Context: {current_context})")
                
            # Log checkpoints to avoid losing usage data
            elif (now - last_save).total_seconds() >= checkpoint_interval:
                log_session(db_path, current_app, start_time, now, current_context)
                start_time = now
                last_save = now
                
        except Exception as e:
            # Shield background polling loop from runtime interruptions
            print(f"[GhostOS] Tracking loop error: {e}", file=sys.stderr)


if __name__ == "__main__":
    start_tracking()
