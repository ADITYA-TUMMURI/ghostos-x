import os
import json
import time
import shutil
import subprocess
import sys
from ghostos.engine_markov import predict_next_intent

# Configuration and Database paths
CONFIG_PATH = os.path.expanduser("~/.local/share/ghostos/config.json")
RATE_LIMIT_FILE = os.path.expanduser("~/.local/share/ghostos/rate_limit.json")

# Executables lookup mapping for common window classes to their shell launchers
LAUNCH_COMMANDS = {
    "chrome": ["google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "brave-browser", "firefox"],
    "firefox": ["firefox", "firefox-esr"],
    "vscode": ["code", "codium"],
    "terminal": ["kitty", "alacritty", "konsole", "gnome-terminal", "xfce4-terminal", "xterm"],
    "brave": ["brave-browser", "brave"],
    "opera": ["opera"],
    "slack": ["slack"],
    "discord": ["discord"]
}


def find_default_config():
    """Locate default config.json relative to the module paths."""
    dir_path = os.path.dirname(os.path.abspath(__file__))
    p1 = os.path.join(dir_path, "config", "config.json")
    if os.path.exists(p1):
        return p1
    p2 = os.path.join(os.path.dirname(dir_path), "ghostos", "config", "config.json")
    if os.path.exists(p2):
        return p2
    return None


def load_config():
    """Load configuration settings with fallback defaults."""
    primary_config_path = os.path.expanduser("~/.config/ghostos/config.json")
    default_path = find_default_config()
    
    # Try ~/.config/ghostos/config.json first
    if os.path.exists(primary_config_path):
        try:
            with open(primary_config_path, "r") as f:
                return json.load(f)
        except Exception:
            pass
            
    # Try fallback config path
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r") as f:
                return json.load(f)
        except Exception:
            pass
            
    # Fallback to default template file directly
    if default_path and os.path.exists(default_path):
        try:
            with open(default_path, "r") as f:
                return json.load(f)
        except Exception:
            pass
            
    return {}


def is_process_running(process_name):
    """Check if a process matches process_name using /proc or pgrep."""
    proc_name_lower = process_name.lower()
    my_pid = str(os.getpid())
    
    # 1. Native /proc scanning for dependency-free efficiency
    try:
        if os.path.exists("/proc"):
            for pid in os.listdir("/proc"):
                if pid.isdigit() and pid != my_pid:
                    try:
                        # Comm holds truncated process name
                        with open(os.path.join("/proc", pid, "comm"), "r", errors="ignore") as f:
                            comm = f.read().strip().lower()
                            if proc_name_lower in comm:
                                return True
                        # Cmdline holds full arguments
                        with open(os.path.join("/proc", pid, "cmdline"), "r", errors="ignore") as f:
                            cmdline = f.read().replace('\x00', ' ').strip().lower()
                            if proc_name_lower in cmdline:
                                return True
                    except (OSError, IOError):
                        continue
    except Exception:
        pass

    # 2. Command execution fallback
    try:
        # Exclude our own pid using pgrep -v
        res = subprocess.run(["pgrep", "-f", process_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if res.returncode == 0:
            pids = res.stdout.decode().strip().split()
            # If there's any pid other than ours, it is running
            if any(p != my_pid for p in pids):
                return True
    except Exception:
        pass

    return False


def get_mapped_binaries(app_name):
    """Map normalized app name to its respective potential process names."""
    app_lower = app_name.lower()
    
    # Check direct mapping
    if app_lower in LAUNCH_COMMANDS:
        return LAUNCH_COMMANDS[app_lower]
        
    # Check partial normalization mapping match
    for key, val in LAUNCH_COMMANDS.items():
        if key in app_lower or app_lower in key:
            return val
            
    return [app_lower]


def is_app_running(app_name):
    """Verify if any binary matching the application is active."""
    binaries = get_mapped_binaries(app_name)
    for binary in binaries:
        if is_process_running(binary):
            return True
    return False


class TokenBucketRateLimiter:
    """Token-bucket rate limiter that persists state to disk to handle multiple CLI invocations."""
    def __init__(self, max_launches_per_minute, state_file=RATE_LIMIT_FILE):
        self.limit = max_launches_per_minute
        self.state_file = state_file
        
    def _load_timestamps(self):
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, "r") as f:
                    data = json.load(f)
                    return [float(ts) for ts in data.get("timestamps", [])]
            except Exception:
                pass
        return []
        
    def _save_timestamps(self, timestamps):
        try:
            os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
            with open(self.state_file, "w") as f:
                json.dump({"timestamps": timestamps}, f)
        except Exception as e:
            print(f"[GhostOS] Failed to save rate-limiter state: {e}", file=sys.stderr)
            
    def acquire_token(self):
        """Register launch timestamp. Returns True if within rate limit, False otherwise."""
        now = time.time()
        one_minute_ago = now - 60.0
        
        timestamps = self._load_timestamps()
        # Filter timestamps from the last 60 seconds
        recent_timestamps = [ts for ts in timestamps if ts > one_minute_ago]
        
        if len(recent_timestamps) >= self.limit:
            return False
            
        recent_timestamps.append(now)
        self._save_timestamps(recent_timestamps)
        return True


def find_executable_binary(app_name):
    """Scan the path environment for available binaries associated with the app."""
    binaries = get_mapped_binaries(app_name)
    for binary in binaries:
        path = shutil.which(binary)
        if path:
            return path
    return None


def reconstruct_workflow_chain(current_app, current_context=None, max_depth=3, db_path=None):
    """Reconstruct a future sequence of transition intentions starting from current_app."""
    chain = []
    seen = {current_app}
    app = current_app
    context = current_context
    
    for _ in range(max_depth):
        kwargs = {}
        if db_path:
            kwargs["db_path"] = db_path
        next_app = predict_next_intent(app, context, **kwargs)
        if not next_app or next_app == "Idle" or next_app == "Browser" or next_app in seen:
            break
        chain.append(next_app)
        seen.add(next_app)
        app = next_app
        
    return chain


def trigger_phantom_mode(current_app, current_context=None, db_path=None):
    """Execute Phantom Mode: predicting, filtering running instances, and launching workflows."""
    config = load_config()
    
    # Extract autopilot configuration properties
    settings = config.get("autopilot_settings", {})
    max_launches = settings.get("max_launches_per_minute", 10)
    check_active = settings.get("check_process_active", True)
    
    hooks = config.get("hooks", {})
    pre_hook = hooks.get("pre_autopilot")
    post_hook = hooks.get("post_autopilot")
    
    limiter = TokenBucketRateLimiter(max_launches)
    
    # 1. Execute Pre-Autopilot Hook
    if pre_hook:
        print(f"[GhostOS] Executing pre-autopilot hook: {pre_hook}")
        subprocess.run(pre_hook, shell=True, check=False)
        
    # 2. Build the target workflow chain
    chain = reconstruct_workflow_chain(current_app, current_context, db_path=db_path)
    if not chain:
        print("[GhostOS] No predicted intent transition detected. Autopilot idle.")
        if post_hook:
            print(f"[GhostOS] Executing post-autopilot hook: {post_hook}")
            subprocess.run(post_hook, shell=True, check=False)
        return
        
    print(f"[GhostOS] Phantom Mode triggered. Workflow Chain: {' -> '.join(chain)}")
    
    # 3. Iteratively execute the workflow launch pipeline
    for app in chain:
        # Check active instances to prevent window duplicate clutter
        if check_active and is_app_running(app):
            print(f"[GhostOS] App '{app}' is already running. Skipping launch to avoid spam.")
            continue
            
        # Enforce rate limiter safety cap
        if not limiter.acquire_token():
            print(f"[GhostOS] Autopilot rate-limit gate triggered. Aborting workflow launch chain.")
            break
            
        # Locate binary path
        exe_path = find_executable_binary(app)
        if not exe_path:
            print(f"[GhostOS] Binary path not resolved for '{app}'. Skipping launch.")
            continue
            
        # Resolve working directories (e.g. terminals opening directly into local workspace folder)
        cwd = None
        is_terminal = app.lower() in ["terminal", "kitty", "alacritty", "konsole", "gnome-terminal"]
        if is_terminal and current_context:
            expanded_path = os.path.expanduser(current_context)
            if os.path.isdir(expanded_path):
                cwd = expanded_path
                print(f"[GhostOS] Direct terminal workspace routing: {cwd}")
                
        # Fire application launch subprocess
        try:
            print(f"[GhostOS] Launching: {app} -> ({exe_path})")
            # Run detached in a new session to ensure persistence
            subprocess.Popen(
                [exe_path], 
                cwd=cwd, 
                stdout=subprocess.DEVNULL, 
                stderr=subprocess.DEVNULL, 
                start_new_session=True
            )
        except Exception as e:
            print(f"[GhostOS] Launch error for application '{app}': {e}", file=sys.stderr)
            
    # 4. Execute Post-Autopilot Hook
    if post_hook:
        print(f"[GhostOS] Executing post-autopilot hook: {post_hook}")
        subprocess.run(post_hook, shell=True, check=False)


if __name__ == "__main__":
    # Test execution stub
    if len(sys.argv) > 1:
        app_arg = sys.argv[1]
        ctx_arg = sys.argv[2] if len(sys.argv) > 2 else None
        trigger_phantom_mode(app_arg, ctx_arg)
    else:
        print("Usage: python3 autopilot.py <current_app> [current_context]")
