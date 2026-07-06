import os
import re
import sys
import sqlite3
from datetime import datetime

# Database path in user's home directory
DB_PATH = os.path.expanduser("~/.local/share/ghostos/activity.db")


def format_duration(seconds):
    """Format duration in seconds to a human-readable string (hours or minutes)."""
    if seconds >= 3600:
        return f"{seconds / 3600:.1f}h"
    else:
        return f"{seconds / 60:.1f}m"


def render_report(date_str, db_path=DB_PATH):
    """Retrieve daily activity stats and render a minimalist text CLI dashboard."""
    if not os.path.exists(db_path):
        print(f"[GhostOS] Database not found at {db_path}. Please start tracking first.")
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT app_name, duration, context_hint, start_time 
            FROM activity 
            WHERE date(start_time) = ?
            """,
            (date_str,)
        )
        rows = cursor.fetchall()
        conn.close()
    except Exception as e:
        print(f"[GhostOS] Error querying database: {e}", file=sys.stderr)
        return

    if not rows:
        print(f"╔══════════════════════════════════════╗")
        print(f"║       GHOST OS X — DAILY REPORT      ║")
        print(f"╠══════════════════════════════════════╣")
        print(f"║  Date: {date_str:<29} ║")
        print(f"╚══════════════════════════════════════╝")
        print(f"\nNo activity records found for this date.")
        return

    # Calculate metrics
    total_duration = sum(row[1] for row in rows)
    total_sessions = len(rows)
    
    # Context-hint presence indicates contextual focus work
    time_with_context = sum(row[1] for row in rows if row[2] is not None and row[2] != "")
    focus_score = int((time_with_context / total_duration) * 100) if total_duration > 0 else 100

    # Aggregate time per application
    app_times = {}
    for app_name, duration, _, _ in rows:
        app_times[app_name] = app_times.get(app_name, 0.0) + duration

    # Sort apps descending by total active time
    sorted_apps = sorted(app_times.items(), key=lambda x: x[1], reverse=True)

    # Output headers
    print(f"╔══════════════════════════════════════╗")
    print(f"║       GHOST OS X — DAILY REPORT      ║")
    print(f"╠══════════════════════════════════════╣")
    print(f"║  Date: {date_str:<29} ║")
    print(f"╚══════════════════════════════════════╝")

    # Output overview summary
    bar_length = 20
    focus_filled = int(round(bar_length * focus_score / 100))
    focus_bar = "█" * focus_filled + "░" * (bar_length - focus_filled)

    print("\n=== Overview ===")
    print(f"Total tracked:  {format_duration(total_duration)}")
    print(f"Total sessions: {total_sessions}")
    print(f"Focus score:    [{focus_bar}] {focus_score}/100")

    # Output App breakdown with relative progress bars
    print("\n=== App Breakdown ===")
    for app_name, duration in sorted_apps:
        percentage = int((duration / total_duration) * 100) if total_duration > 0 else 0
        filled_length = int(round(bar_length * duration / total_duration)) if total_duration > 0 else 0
        bar = "█" * filled_length + "░" * (bar_length - filled_length)
        
        # Format: App_Name (left-aligned), duration, bar, percentage
        name_str = f"  {app_name:<16}"
        time_str = f"{format_duration(duration):>6}"
        print(f"{name_str} {time_str}  {bar}  {percentage:>3}%")


if __name__ == "__main__":
    target_date = None
    if len(sys.argv) > 1:
        date_input = sys.argv[1]
        # Basic YYYY-MM-DD validation
        if re.match(r"^\d{4}-\d{2}-\d{2}$", date_input):
            target_date = date_input
        else:
            print("Error: Invalid date format. Please use YYYY-MM-DD (e.g. 2026-07-07).", file=sys.stderr)
            sys.exit(1)
    else:
        target_date = datetime.now().strftime("%Y-%m-%d")

    render_report(target_date)
