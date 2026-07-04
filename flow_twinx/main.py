import argparse
import importlib
import sys
import threading
import time
from pathlib import Path

if __name__ == "__main__" and __package__ is None:
    __package__ = "flow_twinx"
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from .imports import config, show_banner, tui_input, is_connected
from . import shortcuts

P = config.Primary
S = config.Secondary
M = config.Muted
R = config.Reset


def _spinner(stop):
    chars = "|/-\\"
    i = 0
    while not stop():
        sys.stdout.write(f"\r{P}Checking connection... {chars[i]}{R}")
        sys.stdout.flush()
        time.sleep(0.1)
        i = (i + 1) % len(chars)
    sys.stdout.write("\r" + " " * 40 + "\r")
    sys.stdout.flush()


def _load_commands():
    return importlib.import_module(f".{config.Mode}.commands", package=__package__)


def _check_vlc():
    try:
        import vlc
    except ImportError:
        print(
            f"{config.Red}VLC is not installed. Flow requires VLC to play audio.{config.Reset}\n"
            f"{config.Muted}Install it with:{config.Reset}\n"
            f"  {config.Tertiary}sudo apt install vlc{config.Reset}"
            f"  {config.Muted}  # Debian/Ubuntu{config.Reset}\n"
            f"  {config.Tertiary}sudo dnf install vlc{config.Reset}"
            f"  {config.Muted}  # Fedora{config.Reset}\n"
            f"  {config.Tertiary}sudo pacman -S vlc{config.Reset}"
            f"  {config.Muted}  # Arch Linux{config.Reset}\n"
            f"  {config.Tertiary}brew install vlc{config.Reset}"
            f"  {config.Muted}  # macOS{config.Reset}"
        )
        sys.exit(1)


def main():
    _check_vlc()
    stop = False
    t = threading.Thread(target=_spinner, args=(lambda: stop,), daemon=True)
    t.start()
    try:
        is_connected()
    finally:
        stop = True
        t.join()

    parser = argparse.ArgumentParser(description="Flow Music Player")
    parser.add_argument("-r", action="store_true", help="repeat mode")
    parser.add_argument("-s", action="store_true", help="shuffle")
    parser.add_argument("-d", action="store_true", help="download mode")
    parser.add_argument("command", nargs="?", default=None, help="subcommand (play, search, list, ...)")

    args, unknown = parser.parse_known_args()

    shortcuts.load()
    commands = _load_commands()

    show_banner()

    if args.command:
        commands.run(args.command, unknown, args)
    elif unknown:
        print(f"Unknown argument: {' '.join(unknown)}")
    else:
        while True:
            try:
                parts = tui_input().strip().split()
                if not parts:
                    continue
                cmd = parts[0].lower()
                extra = parts[1:]
                cmd = shortcuts.resolve(cmd)
                if cmd in ("exit", "quit", "q"):
                    print(f"{M}Goodbye!{R}")
                    break
                cmd_args = argparse.Namespace(**vars(args))
                for flag in ("r", "s", "d"):
                    setattr(cmd_args, flag, False)
                commands.run(cmd, extra, cmd_args)
                if cmd == "switch":
                    mode = config.Mode
                    commands = _load_commands()
                    show_banner()
            except (EOFError, KeyboardInterrupt):
                print(f"{M}\nGoodbye!{R}")
                break


if __name__ == "__main__":
    main()
