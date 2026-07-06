import sys
from ghostos import core_tracker, report_cli, autopilot

def main():
    if len(sys.argv) < 2:
        print("Usage: ghostos [track|report|autopilot]")
        sys.exit(1)
        
    cmd = sys.argv[1].lower()
    if cmd == "track":
        core_tracker.start_loop()
    elif cmd == "report":
        report_cli.generate_report()
    elif cmd == "autopilot":
        if len(sys.argv) > 2:
            app_arg = sys.argv[2]
            ctx_arg = sys.argv[3] if len(sys.argv) > 3 else None
            autopilot.trigger_phantom_mode(app_arg, ctx_arg)
        else:
            autopilot.trigger_autopilot_cli()
    else:
        print(f"Unknown command: {cmd}")

if __name__ == "__main__":
    main()
