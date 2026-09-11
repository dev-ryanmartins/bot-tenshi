import os
import runpy
import sys
from pathlib import Path


def _configurar_console_utf8():
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")


def main():
    _configurar_console_utf8()
    this_file = globals().get("__file__") or os.path.abspath("main.py")
    bot_dir = Path(this_file).resolve().parent / "artifacts" / "tenshi-bot"
    os.chdir(bot_dir)
    bot_path = str(bot_dir)
    if bot_path not in sys.path:
        sys.path.insert(0, bot_path)
    
    import time
    while True:
        try:
            runpy.run_path(str(bot_dir / "main.py"), run_name="__main__")
            time.sleep(5)
        except Exception as e:
            print(f"[CONTAINER WATCHDOG] Exceção em main.py: {e}", file=sys.stderr)
            time.sleep(10)


if __name__ == "__main__":
    main()
