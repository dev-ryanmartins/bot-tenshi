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
    bot_dir = Path(__file__).resolve().parent / "artifacts" / "tenshi-bot"
    os.chdir(bot_dir)
    bot_path = str(bot_dir)
    if bot_path not in sys.path:
        sys.path.insert(0, bot_path)
    runpy.run_path(str(bot_dir / "main.py"), run_name="__main__")


if __name__ == "__main__":
    main()
